# Movie Recommendation and User Preference Analysis

## Cover page

**Institution:** [College name]  
**Department:** [Department]  
**Course:** Parallel and Distributed Systems (PDS)  
**Project title:** Movie Recommendation and User Preference Analysis  
**Team members:** [Names and roll numbers]  
**Project guide:** [Name]  
**Academic year:** [Year]

## Abstract

This project analyzes movie ratings to identify popular and highly rated movies, user genre preferences, and personalized recommendations. It uses the publicly available MovieLens Latest Small dataset from GroupLens Research. Sequential Python, Python multithreading, and Apache Spark were run to compare the same four analysis tasks. Spark MLlib ALS generated personalized recommendations and was evaluated on held-out ratings. A Streamlit dashboard presents the analysis. In the measured run, median sequential and multithreaded aggregation times were **0.3176 seconds** and **0.2606 seconds**, respectively (1.2187× speedup with four threads). Spark aggregation took **13.6745 seconds**; ALS test RMSE was **0.8817**. Spark ran in `local[*]` mode on one computer.

## 1. Problem statement

Large movie catalogues make it difficult for users to find films that match their interests. Rating data can reveal broad popularity and individual taste, and collaborative filtering can use patterns from similar users to suggest unseen movies. This project examines how parallel and distributed processing concepts can support these analyses.

## 2. Objectives

1. Identify popular movies using rating counts.
2. Rank highly rated movies while applying a minimum-rating-count threshold.
3. Summarize a user's average ratings by genre.
4. Generate personalized recommendations using Spark MLlib ALS.
5. Compare sequential, multithreaded, and Spark execution for equivalent aggregation tasks.
6. Present results in a live interactive dashboard.

## 3. Dataset description and source

- **Dataset:** MovieLens Latest Small
- **Provider:** GroupLens Research, University of Minnesota
- **Dataset page:** https://grouplens.org/datasets/movielens/
- **Direct archive:** https://files.grouplens.org/datasets/movielens/ml-latest-small.zip
- **Download date:** October 18, 2026
- **Version as shown in the included dataset README:** `ml-latest-small`, generated September 26, 2018
- **Files used:** `ratings.csv` (user ID, movie ID, rating, timestamp) and `movies.csv` (movie ID, title, genres)
- **Observed data counts:** 100,836 ratings, 610 users, and 9,742 movies

Do not report the dataset's approximate counts as your observed counts; use the generated run summary.

## 4. System architecture

```text
MovieLens CSV files
        |
Validation and pandas input
        +------------------------------+
        |                              |
Sequential + ThreadPool analytics   Spark DataFrames
        |                              +--> partitioned summaries
        |                              +--> ALS train/test + RMSE
        +---------------+--------------+
                        |
             CSV/JSON result artifacts
                        |
                 Streamlit dashboard
```

### Selected PDS technologies

**Python multithreading:** Independent calculations (popular movies, top-rated movies, rating distribution, and genre summary) are submitted to a `ThreadPoolExecutor`. This demonstrates concurrency on one machine. It may be slower for this CPU-bound pandas workload because Python threads do not guarantee CPU parallelism under the GIL and scheduling has overhead.

**Apache Spark:** Spark DataFrames aggregate ratings using Spark's partition/task execution model. Spark MLlib ALS learns latent user and movie factors for collaborative filtering. The default master is `local[*]`, which uses cores on one computer. It demonstrates local parallel processing, not a multi-computer distributed cluster. A cluster run must use a real cluster master and be described with its configuration.

## 5. Methodology

1. Validate required columns, missing identifiers/ratings, and the MovieLens rating range.
2. Count ratings per movie for popularity.
3. Compute mean rating and count; exclude titles with fewer than 30 ratings from the high-rating table.
4. Split genres and compute the selected user's average rating and count per genre.
5. Compare identical four-task analytics in sequential and threaded modes. Spark results are checked against the pandas result for movie ranking IDs.
6. Split ratings deterministically (seed 42) into 80% training and 20% test data. Fit Spark ALS using training ratings, then compute held-out RMSE using Spark's regression evaluator.
7. Recommend the selected user's unseen movies in predicted-rating order.
8. Measure elapsed times with a monotonic timer. Repeat sequential and threaded runs and report the median. Spark startup/input materialization is recorded separately from the aggregation measurement.

### Metrics

\[\text{Speedup} = T_{sequential}/T_{method}\]

\[\text{Throughput} = \text{number of ratings}/T_{method}\]

\[\text{Efficiency} = \text{Speedup}/\text{worker count}\]

RMSE is the square root of mean squared error between held-out true ratings and ALS predictions after rows without a valid prediction are dropped.

## 6. Implementation details

- `src/download_data.py`: downloads and extracts the official archive.
- `src/analytics.py`: sequential/threaded analysis, genre preferences, and clearly labeled fallback recommender.
- `src/spark_model.py`: Spark aggregation and ALS train/test evaluation.
- `src/pipeline.py`: validation, orchestration, benchmarking, and artifact writing.
- `app.py`: Streamlit dashboard.

## 7. Results and screenshots

Attach screenshots of the live dashboard and include the generated top movies, selected user genre preferences, recommendations, and benchmark table. Insert the five most popular movies and their rating counts from `results/popular_movies.csv`, plus the top high-rated titles from `results/top_rated_movies.csv`.

**Selected user ID:** 414  
**Recommendation method actually used:** Spark MLlib ALS  
**Held-out ALS RMSE:** 0.8817

Do not call the fallback recommendations ALS results. The pipeline writes the method into `recommendations.csv` and the Spark status into `run_summary.json`.

## 8. Performance analysis

Paste the rows from `results/performance.csv` here. Include all repeats and hardware details where possible.

| Method | Median elapsed time (s) | Speedup | Throughput (ratings/s) | Workers |
|---|---:|---:|---:|---:|
| Sequential | 0.3176 | 1.0000 | 317,498 | 1 |
| Multithreaded | 0.2606 | 1.2187 | 386,919 | 4 |
| Spark aggregation | 13.6745 | 0.0232 | 7,374 | local[*] |

**Environment:** Windows 10, Python 3.10.10, PySpark 4.2.0, Temurin Java 21.0.12.1; add CPU and RAM details before submission.  
**Spark startup and input materialization:** approximately 24.9491 seconds, recorded separately from the aggregation time.  
**Discussion:** Four-thread execution was about 21.9% faster than sequential execution in this three-repeat run. Spark's aggregation took substantially longer than the pandas workload on this small dataset, reflecting JVM, task scheduling, and conversion overhead. The Spark and pandas/threaded benchmarks now measure the same four tasks: popular movies, high-rated movies, rating distribution, and genre summary. Spark startup/input time is separate from aggregation time; ALS model training is also separate from that benchmark. The ALS held-out RMSE was 0.8817. Spark used local mode, so these figures do not represent a multi-machine cluster.

## 9. Conclusion and limitations

Summarize what the observed results show. Limitations include sparse ratings, cold-start users/items, the small dataset size, a single-machine default Spark setup, rating prediction not guaranteeing user satisfaction, and the selected recommendation method. Future work could test a larger MovieLens dataset and a true Spark cluster, compare additional ranking metrics, and add time-aware or content features.

## 10. Individual contribution

| Member | Actual work completed | Evidence / module explained |
|---|---|---|
| [Name] | [Contribution] | [Module or demo section] |
| [Name] | [Contribution] | [Module or demo section] |
| [Name] | [Contribution] | [Module or demo section] |

Only list contributions that each member actually performed and can explain.

## References

1. GroupLens Research, MovieLens datasets: https://grouplens.org/datasets/movielens/
2. Apache Spark, PySpark installation: https://spark.apache.org/docs/latest/api/python/getting_started/install.html
3. Apache Spark, MLlib ALS API: https://spark.apache.org/docs/latest/api/python/reference/api/pyspark.ml.recommendation.ALS.html
4. Streamlit documentation: https://docs.streamlit.io/
