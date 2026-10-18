"""Spark DataFrame aggregation and MLlib ALS recommendation workflow."""
from __future__ import annotations

import os
import sys
from time import perf_counter


def start_spark(master: str | None = None):
    # On Windows, `python3` may resolve to a Store alias or may not exist.
    # Use the exact interpreter running this project for Spark's Python workers.
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F
    from pyspark.ml.recommendation import ALS
    from pyspark.ml.evaluation import RegressionEvaluator

    builder = SparkSession.builder.appName("MovieLensPDS")
    builder = builder.master(master or "local[*]")
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark, F, ALS, RegressionEvaluator


def spark_aggregate(ratings_pd, movies_pd, master: str | None = None):
    spark, F, _, _ = start_spark(master)
    ratings = spark.createDataFrame(ratings_pd[["userId", "movieId", "rating", "timestamp"]]).cache()
    movies = spark.createDataFrame(movies_pd[["movieId", "title", "genres"]])
    ratings.count()  # Materialize input once before timing the aggregation workload.
    begin = perf_counter()
    popular = (ratings.groupBy("movieId").agg(F.count("*").alias("rating_count"))
               .join(movies, "movieId").orderBy(F.desc("rating_count"), "title").limit(20).toPandas())
    rating_distribution = (ratings.groupBy("rating").agg(F.count("*").alias("count"))
                           .orderBy("rating").toPandas())
    top_rated = (ratings.groupBy("movieId").agg(F.avg("rating").alias("average_rating"), F.count("*").alias("rating_count"))
                 .filter(F.col("rating_count") >= 30).join(movies, "movieId")
                 .orderBy(F.desc("average_rating"), F.desc("rating_count"), "title").limit(20).toPandas())
    genre_summary = (ratings.join(movies, "movieId")
                     .withColumn("genre", F.explode(F.split("genres", r"\|")))
                     .groupBy("genre").agg(F.avg("rating").alias("average_rating"), F.count("*").alias("rating_count")).toPandas())
    elapsed = perf_counter() - begin
    return spark, {
        "popular_movies": popular,
        "top_rated_movies": top_rated,
        "rating_distribution": rating_distribution,
        "genre_summary": genre_summary,
    }, elapsed


def train_and_recommend(spark, ratings_pd, movies_pd, user_id: int, seed: int = 42):
    from pyspark.sql import functions as F
    from pyspark.ml.evaluation import RegressionEvaluator
    from pyspark.ml.recommendation import ALS

    all_ratings = spark.createDataFrame(ratings_pd[["userId", "movieId", "rating"]])
    train, test = all_ratings.randomSplit([0.8, 0.2], seed=seed)
    model = ALS(userCol="userId", itemCol="movieId", ratingCol="rating", rank=10,
                maxIter=10, regParam=0.1, coldStartStrategy="drop", seed=seed).fit(train)
    predictions = model.transform(test)
    rmse = RegressionEvaluator(labelCol="rating", predictionCol="prediction", metricName="rmse").evaluate(predictions)
    seen = all_ratings.filter(F.col("userId") == int(user_id)).select("movieId").distinct()
    ids = spark.createDataFrame([(int(user_id), int(mid)) for mid in movies_pd.movieId], ["userId", "movieId"])
    unseen = ids.join(seen, "movieId", "left_anti")
    recs = model.transform(unseen).filter(F.col("prediction").isNotNull())
    movies = spark.createDataFrame(movies_pd[["movieId", "title", "genres"]])
    recs = (recs.join(movies, "movieId").select("movieId", "title", "genres", F.col("prediction").alias("predicted_rating"))
            .orderBy(F.desc("predicted_rating")).limit(10).toPandas())
    return recs, float(rmse)
