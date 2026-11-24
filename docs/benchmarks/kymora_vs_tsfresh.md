# Kymora vs tsfresh: Time Series Feature Extraction Comparison

**Kymora** is a high-performance alternative to **tsfresh** (Time Series Feature Extraction based on Scalable Hypothesis Tests) for Python data science, machine learning, and quantitative finance.

While tsfresh extracts hundreds of exploratory features, its architecture requires melting 2D time series matrices into long-format Pandas DataFrames and serializing batches via Python multiprocessing. This introduces massive memory overhead and slow execution. Kymora bypasses these bottlenecks completely with zero-copy Rust buffers and lock-free thread parallelism.

---

## At a Glance: Kymora vs. tsfresh

| Metric / Feature | Kymora (v0.8.3) | tsfresh (v0.21.2) | Kymora Advantage |
| :--- | :---: | :---: | :---: |
| **Engine / Backend** | Rust + Rayon work-stealing | Python multiprocessing + IPC | Native multi-core CPU saturation |
| **Extraction Time (1k × 500)** | **1.94 ms** | 23,540.62 ms (23.5 sec) | **12,106× faster** |
| **Throughput** | **514,245 series/sec** | 42 series/sec | **12,106× throughput** |
| **Normalized per-feature** | 0.0589 ms / feat | 30.30 ms / feat | **514× faster per feature** |
| **Memory Overhead (10k × 500)** | **~2.29–3.33 MiB scratch** | **+410.3 MiB** | Bounded $O(T \times L)$ worker footprint |
| **Input Format** | Direct 2D NumPy array | Long DataFrame melt required | No data transformation needed |
| **GIL Behavior** | Fully released across execution | Subject to Python serialization | Full CPU thread utilization |
| **Downstream RF Accuracy** | **83.12%** (`extended` profile) | **84.79%** (777 features) | Closes accuracy gap at 10,000× speed |

---

## Memory Footprint & Architecture Comparison

### The tsfresh Bottleneck:
To extract features with tsfresh, users must reshape wide 2D arrays into tall, narrow DataFrames with column identifiers:
```python
# tsfresh requires reshaping to long format:
df_long = pd.melt(df_wide, id_vars=['id'])
# Data is duplicated into memory, pickled, and sent across process pipes.
```
At 10,000 series of 500 steps, tsfresh consumes an extra **410.3 MiB of RAM** just for internal conversion structures.

### The Kymora Zero-Copy Architecture:
Kymora directly borrows contiguous NumPy buffers through PyO3:
```python
import kymora as km

# Direct 2D array ingestion - zero copies:
features = km.extract_features(X)  # X is shape (10000, 500)
```
Total process memory overhead is bounded to tiny thread-local scratchpads (2–3 MiB), preventing OOM crashes on large datasets.

---

## When to Use Which?

- **Use Kymora when:** You need high-throughput batch extraction, real-time sensor ingestion, low-latency scoring pipelines, clean Scikit-Learn workflows, or bounded memory constraints.
- **Use tsfresh when:** You need exploratory hypothesis testing with hundreds of niche combinatorial features and execution time is not a constraint.
