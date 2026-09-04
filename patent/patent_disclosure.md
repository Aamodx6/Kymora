# PATENT TECHNICAL DISCLOSURE & PATENT APPLICATION DRAFT

**CONFIDENTIAL ATTORNEY-CLIENT PRIVILEGED DOCUMENT**  
*Prepared for Patent Filing & Review by Registered Patent Attorney / Agent*

---

## TITLE OF THE INVENTION
**APPARATUS, METHOD, AND NON-TRANSITORY COMPUTER-READABLE MEDIUM FOR HIGH-THROUGHPUT BATCH AND INCREMENTAL STREAMING TIME-SERIES FEATURE EXTRACTION**

---

## 1. INVENTORSHIP & STATUTORY TIMELINE STATEMENT
- **Inventor**: Aamod Kumar
- **Assignee**: Independent / Pending Assignment
- **Public Disclosure Date**: July 31, 2026 (Initial open-source release v0.1.0 on PyPI / GitHub).
- **Statutory Grace Period Invocation (35 U.S.C. § 102(b)(1))**:
  - The subject matter of this disclosure was published by the inventor within the one-year period prior to the effective filing date of this application.
  - The US statutory 1-year grace period expires on **July 31, 2027**.
  - **Foreign Patent Rights Notice**: Because jurisdictions outside the United States (including the European Patent Office under Art. 54 EPC, China CNIPA, and Japan JPO) enforce an absolute novelty standard with no general inventor grace period, this application primarily targets filing with the United States Patent and Trademark Office (USPTO). Any international PCT application must focus on newly introduced, unpublished enhancements (specifically, the $O(1)$ stateful incremental streaming engine introduced in v0.3.x).

---

## 2. FIELD OF THE INVENTION
The present invention relates generally to digital signal processing, edge computing, telemetry analytics, and machine learning feature engineering. More specifically, the present invention relates to an optimized computer hardware-software architecture for extracting compact, non-redundant feature representations from high-dimensional time-series data using zero-copy memory ingestion, multi-threaded batch parallelization, fused memory traversals, and $O(1)$ incremental streaming sliding-window accumulators.

---

## 3. BACKGROUND OF THE INVENTION & PRIOR ART DEFICIENCIES

### 3.1 Technical Deficiencies of Prior Art
Feature extraction from temporal sensor signals (e.g., vibration monitors, seismic telemetry, medical biosignals, financial order books) is an essential precursor to automated anomaly detection and classification. Prior art software libraries exhibit major architectural bottlenecks:

1. **Exhaustive Feature Over-Parameterization (The Redundancy Problem)**:
   - Toolkits like `tsfresh` compute upwards of 1,500 features per series, while `TSFEL` computes ~390 features.
   - Rigorous empirical studies show that >90% of the variance across these large feature sets is captured by as few as 4 principal components. The remaining 90%+ of FLOPs represent redundant mathematical computation that wastes computational power, exhausts mobile/edge battery life, and increases machine learning model overfitting.
2. **Interpreter Lock and Serialization Overhead (The FFI Bottleneck)**:
   - Python-based tools or naive C-wrapper libraries (e.g., `catch22`) require iterating over batches of series using interpreted Python loops, invoking foreign function interfaces (FFI) once per series. This causes massive call-stack overhead, prevents hardware vectorization, and is constrained by the Python Global Interpreter Lock (GIL).
3. **Sliding-Window Computational Explosions (The Rolling Recomputation Problem)**:
   - Conventional sliding-window processors extract features by slicing windows of length $W$ with stride $S$, recomputing every feature from scratch on every window. For a time series of length $N$, this induces an overall time complexity of $O(N \cdot W)$, creating latency spikes that prevent real-time deployment on low-power edge IoT devices.

---

## 4. SUMMARY OF THE INVENTION

The present invention solves these technical problems by providing an integrated computing apparatus and method that combines:

1. **A Closed, High-Signal 33-Feature Orthogonal Representation**: An optimized set of 33 statistical, temporal, and spectral features adhering strictly to $O(n)$ or $O(n \log n)$ bounds.
2. **A Zero-Copy Multi-Core Ingestion Pipeline**: Ingests multi-dimensional array memory buffers without defensive copying, releases thread locks, and parallelizes across the series dimension using dynamic work-stealing thread pools.
3. **Five Fused Memory Traversals**: Compresses memory scans from $>20$ passes down to exactly 5 cache-aligned passes per series, achieving optimal operational intensity on modern CPU memory hierarchies.
4. **An $O(1)$ Incremental Streaming Sliding-Window Accumulator Engine**: Employs a circular ring buffer and maintains running state accumulators (power sums, linear trend covariance, successive differences, and zero crossings) such that advancing a rolling window by a new sample requires only $O(1)$ arithmetic operations, reducing sliding-window extraction complexity from $O(N \cdot W)$ to $O(N)$.

---

## 5. DETAILED DESCRIPTION OF PREFERRED EMBODIMENTS

### 5.1 $O(1)$ Incremental State Update Formulations
Let a rolling window have length $W$. When a new digital sample $x_{\text{new}}$ is received, the oldest sample $x_{\text{old}}$ is evicted from the circular buffer.

#### A. Central Moments & Power Sums
Running power sums $S_k = \sum_{i=0}^{W-1} x_i^k$ for $k \in \{1, 2, 3, 4\}$ are updated in $O(1)$ time:
$$S_k \leftarrow S_k + x_{\text{new}}^k - x_{\text{old}}^k$$
The mean $\mu$, variance $\sigma^2$, skewness $\gamma_1$, and excess kurtosis $\gamma_2$ are directly computed from $S_1, S_2, S_3, S_4$ without scanning the window:
$$\mu = \frac{S_1}{W}, \quad \sigma^2 = \frac{S_2}{W} - \mu^2$$
$$m_3 = \frac{S_3}{W} - 3\mu \frac{S_2}{W} + 2\mu^3 \implies \gamma_1 = \frac{m_3}{\sigma^3}$$
$$m_4 = \frac{S_4}{W} - 4\mu \frac{S_3}{W} + 6\mu^2 \frac{S_2}{W} - 3\mu^4 \implies \gamma_2 = \frac{m_4}{\sigma^4} - 3.0$$

#### B. Linear Trend Covariance Recurrence
The linear trend sum $T = \sum_{i=0}^{W-1} i \cdot x_i$ is updated in $O(1)$ time without re-multiplying indices:
$$T \leftarrow T - (S_{1, \text{prev}} - x_{\text{old}}) + (W - 1) \cdot x_{\text{new}}$$

#### C. Successive Differences & CID_CE
With $x_{\text{prev\_new}}$ being the sample preceding $x_{\text{new}}$, and $x_{\text{second\_old}}$ being the sample following $x_{\text{old}}$:
$$\sum |\Delta x| \leftarrow \sum |\Delta x| - |x_{\text{second\_old}} - x_{\text{old}}| + |x_{\text{new}} - x_{\text{prev\_new}}|$$
$$\sum (\Delta x)^2 \leftarrow \sum (\Delta x)^2 - (x_{\text{second\_old}} - x_{\text{old}})^2 + (x_{\text{new}} - x_{\text{prev\_new}})^2$$
The Complexity-Invariant Distance measure ($CID\_CE$) is computed directly as $\frac{\sqrt{\sum (\Delta x)^2}}{\sigma}$.

---

## 6. FORMAL PATENT CLAIMS

### WE CLAIM:

#### Claim 1 (Independent Method Claim):
A computer-implemented method for real-time incremental sliding-window feature extraction over a digital time-series data stream, the method comprising:
1. allocating, in a physical memory of a digital computing device, a circular ring buffer having a predefined window capacity $W$, and a plurality of numeric state accumulators;
2. receiving, by an ingestion interface, a continuous stream of digital time-series data samples;
3. for each incoming data sample $x_{\text{new}}$ received after the circular ring buffer is filled:
   - identifying an oldest stored data sample $x_{\text{old}}$ scheduled for eviction from the circular ring buffer;
   - updating, via an arithmetic processor in $O(1)$ computational time, a set of numeric power sums $S_k \leftarrow S_k + x_{\text{new}}^k - x_{\text{old}}^k$ for $k \in \{1, 2, 3, 4\}$;
   - updating, in $O(1)$ computational time, a linear trend covariance accumulator $T \leftarrow T - (S_1 - x_{\text{old}}) + (W - 1) \cdot x_{\text{new}}$;
   - updating, in $O(1)$ computational time, a running successive difference accumulator;
   - overwriting the oldest stored data sample $x_{\text{old}}$ in the circular ring buffer with the incoming data sample $x_{\text{new}}$; and
4. outputting, to an execution target, a multi-dimensional feature vector derived from the updated state accumulators, wherein the feature vector characterizes the dynamic properties of the current sliding window.

#### Claim 2 (Dependent Claim):
The method of claim 1, further comprising:
computing, from the updated power sums $S_1, S_2, S_3, S_4$, a population mean, a population variance, a skewness metric, an excess kurtosis metric, an absolute energy metric, and a root-mean-square metric, all in $O(1)$ computational time.

#### Claim 3 (Dependent Claim):
The method of claim 1, wherein updating the running successive difference accumulator comprises:
subtracting an outgoing difference magnitude $|x_{\text{second\_old}} - x_{\text{old}}|$ and adding an incoming difference magnitude $|x_{\text{new}} - x_{\text{prev\_new}}|$, wherein $x_{\text{second\_old}}$ is a sample adjacent to $x_{\text{old}}$ and $x_{\text{prev\_new}}$ is a sample adjacent to $x_{\text{new}}$ in the circular ring buffer.

#### Claim 4 (Dependent Claim):
The method of claim 1, further comprising maintaining a running zero-crossing accumulator, wherein updating the running zero-crossing accumulator comprises evaluating a first boolean state change between $x_{\text{old}}$ and $x_{\text{second\_old}}$ and a second boolean state change between $x_{\text{prev\_new}}$ and $x_{\text{new}}$.

#### Claim 5 (Dependent Claim):
The method of claim 1, further comprising performing periodic numerical re-anchoring of the numeric state accumulators directly from the data samples stored in the circular ring buffer after a predetermined threshold count of incoming samples, thereby bounding floating-point roundoff drift within IEEE 754 precision.

#### Claim 6 (Dependent Claim):
The method of claim 1, wherein the multi-dimensional feature vector includes a permutation entropy metric computed using a precomputed branchless permutation lookup table indexed by bitwise-packed pairwise comparisons of consecutive window values.

#### Claim 7 (Dependent Claim):
The method of claim 1, wherein the multi-dimensional feature vector includes spectral features computed by applying a real-to-complex Fast Fourier Transform (FFT) utilizing a thread-local workspace cache pre-allocated to fit within an L1 or L2 CPU hardware cache.

---

#### Claim 11 (Independent System Claim):
An edge computing telemetry apparatus for real-time sensor feature extraction and anomaly detection, comprising:
- a network or sensor bus interface configured to ingest high-frequency digital time-series measurements;
- a physical memory configured to store a circular ring buffer having a capacity of $W$ measurements and a plurality of streaming state accumulators;
- one or more hardware processing cores operatively coupled to the physical memory; and
- a feature extraction module executable by the one or more hardware processing cores to:
  - continuously ingest incoming measurements into the circular ring buffer;
  - execute $O(1)$ incremental state updates to the streaming state accumulators upon eviction of an oldest measurement and ingestion of a newest measurement;
  - synthesize a compact feature vector from the streaming state accumulators without performing an $O(W)$ iteration over the circular ring buffer; and
  - transmit the synthesized compact feature vector to a machine learning classifier or an edge anomaly trigger.

#### Claim 12 (Dependent Claim):
The edge computing telemetry apparatus of claim 11, wherein the streaming state accumulators occupy less than 32 kilobytes of physical memory and reside entirely within a hardware L1 data cache of the one or more hardware processing cores during active ingestion.

#### Claim 13 (Dependent Claim):
The edge computing telemetry apparatus of claim 11, wherein the edge computing telemetry apparatus is an industrial vibration sensor, an electrocardiogram (ECG) monitor, or an acoustic telemetry monitor.

---

#### Claim 21 (Independent Computer-Readable Medium Claim):
A non-transitory computer-readable storage medium comprising instructions that, when executed by one or more processors of a computing system, cause the computing system to perform operations comprising:
- allocating a circular ring buffer of capacity $W$ and a plurality of state accumulators in memory;
- ingesting a succession of time-series data points;
- for each incoming data point, updating power sums, linear trend covariance, and successive difference sums in $O(1)$ arithmetic operations;
- generating a feature vector representing statistical, temporal, and change characteristics of the window bounded by the circular ring buffer; and
- providing the feature vector to a downstream machine learning classification or clustering model.
