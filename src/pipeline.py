"""Run the complete MovieLens analytics and save report/dashboard artifacts."""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import pandas as pd

from .analytics import (benchmark_rows, fallback_recommendations, run_sequential,
                        run_threaded, user_preferences)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "ml-latest-small"
RESULTS = ROOT / "results"


def load_data():
    ratings_path, movies_path = DATA / "ratings.csv", DATA / "movies.csv"
    if not ratings_path.exists() or not movies_path.exists():
        raise FileNotFoundError("MovieLens files missing. Run: python -m src.download_data")
    ratings = pd.read_csv(ratings_path)
    movies = pd.read_csv(movies_path)
    required = {"userId", "movieId", "rating", "timestamp"}
    if not required.issubset(ratings.columns) or not {"movieId", "title", "genres"}.issubset(movies.columns):
        raise ValueError("Unexpected CSV columns; verify that the official MovieLens archive was extracted")
    if ratings[["userId", "movieId", "rating"]].isna().any().any():
        raise ValueError("Ratings contain missing userId, movieId, or rating values")
    if not ratings.rating.between(0.5, 5.0).all():
        raise ValueError("Ratings outside the MovieLens 0.5–5.0 range were found")
    return ratings, movies


def median_time(fn, repeats: int):
    times = []
    output = None
    for _ in range(repeats):
        output, elapsed = fn()
        times.append(elapsed)
    return output, statistics.median(times), times


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-repeats", type=int, default=3)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--user-id", type=int, default=None)
    parser.add_argument("--require-spark", action="store_true", help="Fail instead of using the labeled baseline if Spark is unavailable")
    parser.add_argument("--spark-master", default=None, help="Spark master URL; defaults to local[*]")
    args = parser.parse_args()
    if args.benchmark_repeats < 1 or args.workers < 1:
        parser.error("benchmark repeats and workers must be positive")

    ratings, movies = load_data()
    RESULTS.mkdir(parents=True, exist_ok=True)
    user_id = args.user_id if args.user_id is not None else int(ratings.userId.mode().iloc[0])
    if user_id not in set(ratings.userId):
        parser.error(f"user ID {user_id} has no ratings in this dataset")

    seq, seq_time, seq_runs = median_time(lambda: run_sequential(ratings, movies), args.benchmark_repeats)
    threaded, thread_time, thread_runs = median_time(lambda: run_threaded(ratings, movies, args.workers), args.benchmark_repeats)
    for key in seq:
        if not seq[key].equals(threaded[key]):
            raise AssertionError(f"Sequential/threaded mismatch for {key}")

    spark_time = None
    spark_startup = None
    spark_status = "unavailable"
    rmse = None
    spark = None
    try:
        from .spark_model import spark_aggregate, train_and_recommend
        startup_start = perf_counter()
        spark, spark_results, spark_time = spark_aggregate(ratings, movies, args.spark_master)
        spark_startup = perf_counter() - startup_start - spark_time
        for key in ("popular_movies", "top_rated_movies"):
            if not set(seq[key].movieId) == set(spark_results[key].movieId):
                raise AssertionError(f"Spark and pandas result mismatch for {key}")
        if not seq["rating_distribution"].equals(spark_results["rating_distribution"]):
            raise AssertionError("Spark and pandas result mismatch for rating_distribution")
        recs, rmse = train_and_recommend(spark, ratings, movies, user_id)
        recs["method"] = "Spark MLlib ALS"
        spark_status = "available"
    except Exception as exc:
        if args.require_spark:
            raise
        spark_status = f"fallback: {type(exc).__name__}: {exc}"
        recs = fallback_recommendations(ratings, movies, user_id)
        recs["method"] = "Genre/rating baseline (Spark unavailable)"
        print(f"Spark unavailable; using labeled baseline recommendations. Details: {exc}")
    finally:
        if spark is not None:
            spark.stop()

    recs["userId"] = int(user_id)
    seq["popular_movies"].to_csv(RESULTS / "popular_movies.csv", index=False)
    seq["top_rated_movies"].to_csv(RESULTS / "top_rated_movies.csv", index=False)
    user_preferences(ratings, movies).to_csv(RESULTS / "user_preferences.csv", index=False)
    recs.to_csv(RESULTS / "recommendations.csv", index=False)
    seq["rating_distribution"].to_csv(RESULTS / "rating_distribution.csv", index=False)
    seq["genre_summary"].to_csv(RESULTS / "genre_summary.csv", index=False)

    times = {"Sequential": seq_time, "Multithreaded": thread_time}
    if spark_time is not None:
        times["Apache Spark (aggregation)"] = spark_time
    bench = benchmark_rows(times, len(ratings), args.workers)
    bench.to_csv(RESULTS / "performance.csv", index=False)
    summary = {
        "project": "Movie Recommendation and User Preference Analysis",
        "dataset": "MovieLens Latest Small",
        "dataset_source": "https://grouplens.org/datasets/movielens/",
        "dataset_directory": str(DATA.relative_to(ROOT)),
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "ratings": int(len(ratings)), "users": int(ratings.userId.nunique()), "movies": int(movies.movieId.nunique()),
        "selected_user_id": int(user_id), "benchmark_repeats": args.benchmark_repeats,
        "timing_runs_seconds": {"sequential": seq_runs, "multithreaded": thread_runs},
        "spark_status": spark_status, "spark_master": args.spark_master or "local[*]",
        "spark_startup_and_input_seconds_approx": spark_startup,
        "als_test_rmse": rmse,
        "python_version": sys.version.split()[0], "platform": platform.platform(),
        "interpretation": "Spark local mode uses local cores and is not a multi-machine cluster demonstration.",
    }
    (RESULTS / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Processed {len(ratings):,} ratings for {ratings.userId.nunique():,} users and {movies.movieId.nunique():,} movies.")
    print(bench.to_string(index=False))
    print(f"Selected user: {user_id}; ALS held-out RMSE: {rmse if rmse is not None else 'not measured'}")
    print(f"Artifacts written to {RESULTS}")


if __name__ == "__main__":
    main()
