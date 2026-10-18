# Movie Recommendation and User Preference Analysis

A PDS mini-project using the public MovieLens Latest Small dataset. It analyzes popular and highly rated movies, user genre preferences, and personalized recommendations. The same aggregation workload is measured sequentially, with Python threads, and with Apache Spark in local mode.

## Requirements

- Python 3.10 or newer
- Java 11 or newer for PySpark (check Spark's current supported Java versions if your installed Spark differs)
- Internet access once to download the dataset

## Quick start (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.download_data
python -m src.pipeline --benchmark-repeats 3
streamlit run app.py
```

On macOS/Linux, activate `.venv` with `source .venv/bin/activate`.

The first run downloads MovieLens Latest Small (about 100,000 ratings) from GroupLens. Dataset source: https://grouplens.org/datasets/movielens/ and direct archive: https://files.grouplens.org/datasets/movielens/ml-latest-small.zip. The data is extracted under `data/ml-latest-small/`. Keep the included `README.txt` with the dataset; it identifies the version and licensing/usage information.

## Outputs

`python -m src.pipeline` validates the CSV inputs, computes movie summaries and user insights, trains/evaluates Spark MLlib ALS when Spark is available, and writes reproducible outputs to `results/`:

- `popular_movies.csv`, `top_rated_movies.csv`
- `user_preferences.csv`, `recommendations.csv`
- `performance.csv` (measured elapsed time, speedup, and throughput)
- `run_summary.json` (input counts, split seed, RMSE and environment details)

The app reads these files and lets you select a user. If Spark/Java is unavailable, the pipeline still produces the analysis, benchmark and a transparent item-based fallback recommendation list; it marks the fallback in the run summary. To require Spark rather than fallback, pass `--require-spark`.

## Parallel/distributed concepts

1. **Multithreading:** `ThreadPoolExecutor` executes independent analytics over the same in-memory ratings. This demonstrates concurrent task scheduling on one machine. Python's GIL and task size can make CPU-bound threads slower; the measured result is what should be discussed.
2. **Apache Spark:** DataFrame aggregations use Spark's partition/task engine, and MLlib ALS factorizes the user-item rating matrix. This project uses Spark `local[*]` by default: parallel across local cores, not a multi-machine cluster. A real cluster can be configured by setting `SPARK_MASTER` (for example `spark://host:7077`) before running.

The benchmark compares equivalent summary computations, not the time to train ALS. Spark startup and its aggregation time are reported separately. Re-run at least three times and report the observed values; small data can favor sequential execution because Spark has startup and scheduling overhead. Benchmark figures are never hard-coded.

## Recommendation and evaluation

Ratings are split deterministically into train/test sets. ALS is trained only on the training set; RMSE is measured against held-out ratings. The chosen user receives predicted ratings for unseen items. The content fallback uses a user's mean genre preference and movie rating average and is labeled as a fallback, not ALS collaborative filtering. Cold-start users/items are a limitation.

## Project files

```text
app.py                 Streamlit demonstration dashboard
src/download_data.py   Dataset downloader and extractor
src/analytics.py       Sequential/threaded analytics and shared metrics
src/spark_model.py     Spark aggregation, ALS, and held-out RMSE
src/pipeline.py        End-to-end command line runner and artifact writer
report/REPORT_TEMPLATE.md  Submission-ready report structure with result placeholders
report/VIVA.md         Viva questions and concise answer guide
results/               Generated data products (created by pipeline)
```

## Troubleshooting

- If PySpark cannot find Java, install a supported JDK and set `JAVA_HOME` to the JDK root (the directory containing `bin\java.exe`), then open a new terminal. Spark 4.x requires Java 17 or newer.
- On Windows, Spark Python workers must use the same interpreter as the project. `src/spark_model.py` sets `PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` to the active interpreter by default.
- If Spark fails on Windows due to Hadoop native utilities, use a current supported Java/PySpark setup and follow Spark's official Windows setup guidance. The non-Spark paths still run.
- The first Spark action includes startup/JVM initialization. The pipeline warms Spark before timing the aggregation and records the startup separately.
- No screenshots or performance claims are supplied as measured results. Capture the running dashboard and use your own `results/performance.csv` in the report.

## References

- GroupLens MovieLens datasets: https://grouplens.org/datasets/movielens/
- PySpark getting started: https://spark.apache.org/docs/latest/api/python/getting_started/install.html
- Spark MLlib ALS: https://spark.apache.org/docs/latest/api/python/reference/api/pyspark.ml.recommendation.ALS.html
- Streamlit documentation: https://docs.streamlit.io/
