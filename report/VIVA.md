# Viva preparation

1. **What is parallel computing versus distributed computing?** Parallel computing performs work at the same time using multiple processing units. Distributed computing coordinates work across multiple networked machines. Our default Spark `local[*]` run is parallel on one machine, not a multi-machine cluster.
2. **Why MovieLens?** It is a public real-world ratings dataset with user IDs, movie IDs, ratings, timestamps, titles, and genres, so the results are reproducible and do not depend on synthetic data.
3. **What does Spark do here?** It partitions DataFrame work into tasks and aggregates rating data; MLlib ALS trains a collaborative-filtering model.
4. **What does multithreading do?** A thread pool runs independent analysis functions concurrently in one process. It demonstrates concurrency; Python's GIL means CPU-bound code may not become faster.
5. **Why can threads be slower?** The workload may be CPU-bound, pandas operations may contend for resources, and thread scheduling adds overhead.
6. **What is collaborative filtering?** It recommends items using patterns in user-item interactions, such as similarities in ratings across users, rather than relying only on movie metadata.
7. **How does ALS work?** It approximates the sparse user-movie rating matrix with lower-dimensional user and item factor matrices, alternating updates to estimate latent factors. Their dot product estimates a rating.
8. **Popular versus personalized?** Popularity ranks by global rating count. A personalized ALS result estimates ratings for unseen items for one selected user.
9. **How is model quality assessed?** The pipeline uses a fixed-seed held-out split and reports RMSE on test ratings for which ALS produced predictions. Lower RMSE means smaller average prediction error, but it does not prove recommendations are satisfying.
10. **How are performance metrics computed?** Speedup is sequential time divided by method time. Throughput is ratings divided by elapsed seconds. Efficiency is speedup divided by worker count.
11. **Why can Spark be slower here?** The dataset is small, while Spark must initialize a JVM, schedule tasks, and move/materialize data. The pipeline reports startup separately from warmed aggregation time.
12. **Why use a minimum rating count?** It reduces the chance that a movie with only one unusually high rating dominates the high-rated list.
13. **Does this run on multiple computers?** By default it uses `local[*]` and one computer. A cluster requires configuring a Spark master and workers; we must not describe local mode as cluster execution.
14. **What is cold start?** A new user or movie has too few interaction ratings for collaborative filtering to learn useful factors. ALS is configured to drop unsupported test predictions when calculating RMSE.
15. **What are the limitations?** Dataset sparsity, cold start, potential popularity bias, only a small dataset, rating prediction as an imperfect proxy for relevance, and no multi-node cluster in the default setup.

## Demonstration sequence

1. Show the dataset source and CSV columns.
2. Run `python -m src.pipeline --benchmark-repeats 3` and explain the generated metrics.
3. Open the dashboard with `streamlit run app.py`.
4. Explain popular versus highly rated lists, then user genre preferences and recommendations.
5. Show that recommendation method and Spark execution mode are labeled in the output.
6. Discuss actual benchmark results and limitations without inventing figures.
