"""Equivalent sequential and threaded rating analytics."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from time import perf_counter

import pandas as pd


def _popular(ratings: pd.DataFrame, movies: pd.DataFrame) -> pd.DataFrame:
    counts = ratings.groupby("movieId").size().rename("rating_count")
    return (movies.merge(counts, on="movieId", how="left").fillna({"rating_count": 0})
            .sort_values(["rating_count", "title"], ascending=[False, True]).head(20))


def _top_rated(ratings: pd.DataFrame, movies: pd.DataFrame, minimum: int = 30) -> pd.DataFrame:
    stats = ratings.groupby("movieId")["rating"].agg(average_rating="mean", rating_count="count").reset_index()
    return (movies.merge(stats, on="movieId", how="inner").query("rating_count >= @minimum")
            .sort_values(["average_rating", "rating_count", "title"], ascending=[False, False, True]).head(20))


def _rating_distribution(ratings: pd.DataFrame) -> pd.DataFrame:
    return ratings.groupby("rating").size().rename("count").reset_index()


def _genre_summary(ratings: pd.DataFrame, movies: pd.DataFrame) -> pd.DataFrame:
    joined = ratings.merge(movies[["movieId", "genres"]], on="movieId", how="inner")
    rows = joined.assign(genre=joined["genres"].str.split("|")).explode("genre")
    return rows.groupby("genre")["rating"].agg(average_rating="mean", rating_count="count").reset_index()


def analytics_tasks(ratings: pd.DataFrame, movies: pd.DataFrame) -> dict:
    return {
        "popular_movies": lambda: _popular(ratings, movies),
        "top_rated_movies": lambda: _top_rated(ratings, movies),
        "rating_distribution": lambda: _rating_distribution(ratings),
        "genre_summary": lambda: _genre_summary(ratings, movies),
    }


def run_sequential(ratings: pd.DataFrame, movies: pd.DataFrame) -> tuple[dict, float]:
    tasks = analytics_tasks(ratings, movies)
    start = perf_counter()
    results = {name: task() for name, task in tasks.items()}
    return results, perf_counter() - start


def run_threaded(ratings: pd.DataFrame, movies: pd.DataFrame, workers: int = 4) -> tuple[dict, float]:
    tasks = analytics_tasks(ratings, movies)
    start = perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {name: pool.submit(task) for name, task in tasks.items()}
        results = {name: future.result() for name, future in futures.items()}
    return results, perf_counter() - start


def user_preferences(ratings: pd.DataFrame, movies: pd.DataFrame) -> pd.DataFrame:
    joined = ratings.merge(movies[["movieId", "genres"]], on="movieId", how="inner")
    rows = joined.assign(genre=joined["genres"].str.split("|")).explode("genre")
    return rows.groupby(["userId", "genre"])["rating"].agg(average_rating="mean", rating_count="count").reset_index()


def fallback_recommendations(ratings: pd.DataFrame, movies: pd.DataFrame, user_id: int, limit: int = 10) -> pd.DataFrame:
    """Transparent genre/rating baseline used only when Spark ALS is unavailable."""
    prefs = user_preferences(ratings, movies)
    own = prefs[prefs.userId == user_id]
    seen = set(ratings.loc[ratings.userId == user_id, "movieId"])
    candidates = movies[~movies.movieId.isin(seen)].copy()
    global_stats = ratings.groupby("movieId").rating.agg(average_rating="mean", rating_count="count")
    candidates = candidates.merge(global_stats, on="movieId", how="left")
    pref_map = own.set_index("genre").average_rating.to_dict()
    def score(genres: str) -> float:
        values = [pref_map[g] for g in genres.split("|") if g in pref_map and g != "(no genres listed)"]
        return sum(values) / len(values) if values else float(candidates.average_rating.mean())
    candidates["predicted_rating"] = candidates.genres.map(score)
    return candidates.sort_values(["predicted_rating", "rating_count"], ascending=False).head(limit)


def benchmark_rows(times: dict[str, float], ratings_count: int, workers: int) -> pd.DataFrame:
    baseline = times["Sequential"]
    rows = []
    for method, seconds in times.items():
        rows.append({"method": method, "elapsed_seconds": seconds,
                     "speedup_vs_sequential": baseline / seconds if seconds else None,
                     "ratings_per_second": ratings_count / seconds if seconds else None,
                     "workers": 1 if method == "Sequential" else workers if method == "Multithreaded" else None})
    return pd.DataFrame(rows)
