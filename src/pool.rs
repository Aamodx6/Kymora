//! Persistent spin-then-park thread pool for sub-millisecond batch execution.
//!
//! Provides dynamic self-scheduling with spin-parking to eliminate worker
//! wake-up latencies on low-latency batches. Rayon is retained as the fallback
//! via `TSXTRACT_POOL=rayon`.

use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::{Arc, Condvar, Mutex, OnceLock};
use std::thread::{self, JoinHandle};

/// Chunk size for dynamic self-scheduling (series count per steal).
pub const DEFAULT_CHUNK_SIZE: usize = 32;

/// Number of spin iterations before parking worker thread (~25-40 microseconds).
const SPIN_LIMIT: usize = 8000;

pub type TaskFn = Arc<dyn Fn(usize, usize, usize) + Send + Sync>;

struct InnerPool {
    epoch: AtomicUsize,
    next_index: AtomicUsize,
    total_items: AtomicUsize,
    chunk_size: AtomicUsize,
    remaining_workers: AtomicUsize,
    current_task: Mutex<Option<TaskFn>>,
    shutdown: AtomicBool,
    has_panic: AtomicBool,
    mutex: Mutex<()>,
    work_cv: Condvar,
    done_cv: Condvar,
    num_threads: usize,
}

pub struct SpinPool {
    inner: Arc<InnerPool>,
    _workers: Vec<JoinHandle<()>>,
}

static GLOBAL_POOL: OnceLock<SpinPool> = OnceLock::new();

impl SpinPool {
    pub fn new(num_threads: usize) -> Self {
        let n_threads = num_threads.max(1);
        let inner = Arc::new(InnerPool {
            epoch: AtomicUsize::new(0),
            next_index: AtomicUsize::new(0),
            total_items: AtomicUsize::new(0),
            chunk_size: AtomicUsize::new(DEFAULT_CHUNK_SIZE),
            remaining_workers: AtomicUsize::new(0),
            current_task: Mutex::new(None),
            shutdown: AtomicBool::new(false),
            has_panic: AtomicBool::new(false),
            mutex: Mutex::new(()),
            work_cv: Condvar::new(),
            done_cv: Condvar::new(),
            num_threads: n_threads,
        });

        let mut workers = Vec::with_capacity(n_threads);
        for thread_idx in 1..n_threads {
            let inner_clone = Arc::clone(&inner);
            let handle = thread::Builder::new()
                .name(format!("tsxtract-worker-{thread_idx}"))
                .spawn(move || {
                    worker_loop(inner_clone, thread_idx);
                })
                .expect("Failed to spawn tsxtract worker thread");
            workers.push(handle);
        }

        Self {
            inner,
            _workers: workers,
        }
    }

    pub fn global() -> &'static SpinPool {
        GLOBAL_POOL.get_or_init(|| {
            let n = thread::available_parallelism()
                .map(|p| p.get())
                .unwrap_or(4);
            SpinPool::new(n)
        })
    }

    /// Execute a task across all worker threads and the calling main thread.
    pub fn run<F>(&self, total_items: usize, chunk_size: usize, f: F)
    where
        F: Fn(usize, usize, usize) + Send + Sync + 'static,
    {
        if total_items == 0 {
            return;
        }

        if self.inner.num_threads <= 1 {
            f(0, total_items, 0);
            return;
        }

        let chunk = chunk_size.max(1);
        self.inner.total_items.store(total_items, Ordering::Release);
        self.inner.chunk_size.store(chunk, Ordering::Release);
        self.inner.next_index.store(0, Ordering::Release);
        self.inner.has_panic.store(false, Ordering::Release);

        let worker_count = self.inner.num_threads - 1;
        self.inner
            .remaining_workers
            .store(worker_count, Ordering::Release);

        let task_arc: TaskFn = Arc::new(f);
        {
            let mut t_lock = self.inner.current_task.lock().unwrap();
            *t_lock = Some(Arc::clone(&task_arc));
        }

        let _guard = self.inner.mutex.lock().unwrap();
        self.inner.epoch.fetch_add(1, Ordering::SeqCst);
        self.inner.work_cv.notify_all();
        drop(_guard);

        // Main thread participates in chunk execution (thread_idx = 0)
        loop {
            let start = self.inner.next_index.fetch_add(chunk, Ordering::Relaxed);
            if start >= total_items {
                break;
            }
            let end = (start + chunk).min(total_items);
            let res = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                task_arc(start, end, 0);
            }));
            if res.is_err() {
                self.inner.has_panic.store(true, Ordering::Release);
                break;
            }
        }

        // Wait for all workers to finish their portions
        let mut guard = self.inner.mutex.lock().unwrap();
        while self.inner.remaining_workers.load(Ordering::Acquire) > 0 {
            guard = self.inner.done_cv.wait(guard).unwrap();
        }

        let mut t_lock = self.inner.current_task.lock().unwrap();
        *t_lock = None;
    }
}

fn worker_loop(inner: Arc<InnerPool>, thread_idx: usize) {
    let mut last_epoch = 0;

    loop {
        // 1. Spin phase before parking
        let mut new_work = false;
        for _ in 0..SPIN_LIMIT {
            if inner.epoch.load(Ordering::Acquire) != last_epoch {
                new_work = true;
                break;
            }
            std::hint::spin_loop();
        }

        // 2. Park phase if spin expired
        if !new_work {
            let mut guard = inner.mutex.lock().unwrap();
            while inner.epoch.load(Ordering::Acquire) == last_epoch {
                if inner.shutdown.load(Ordering::Acquire) {
                    return;
                }
                guard = inner.work_cv.wait(guard).unwrap();
            }
        }

        last_epoch = inner.epoch.load(Ordering::Acquire);
        if inner.shutdown.load(Ordering::Acquire) {
            return;
        }

        let total = inner.total_items.load(Ordering::Acquire);
        let chunk = inner.chunk_size.load(Ordering::Acquire);

        let task_opt = {
            let t_lock = inner.current_task.lock().unwrap();
            t_lock.clone()
        };

        if let Some(task) = task_opt {
            loop {
                let start = inner.next_index.fetch_add(chunk, Ordering::Relaxed);
                if start >= total {
                    break;
                }
                let end = (start + chunk).min(total);
                let res = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    task(start, end, thread_idx);
                }));
                if res.is_err() {
                    inner.has_panic.store(true, Ordering::Release);
                    break;
                }
            }
        }

        // Signal completion of this worker
        if inner.remaining_workers.fetch_sub(1, Ordering::AcqRel) == 1 {
            let _g = inner.mutex.lock().unwrap();
            inner.done_cv.notify_all();
        }
    }
}

/// Check if Rayon execution pool is forced via environment variable.
#[inline]
pub fn should_use_rayon() -> bool {
    if let Ok(val) = std::env::var("TSXTRACT_POOL") {
        val.eq_ignore_ascii_case("rayon")
    } else {
        false
    }
}
