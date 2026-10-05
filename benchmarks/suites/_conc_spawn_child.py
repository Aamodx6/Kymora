"""Child payload for the B3 concurrency spawn_mp case.

Lives in a real importable module (not __main__) so that multiprocessing's
spawn start method can pickle the Process target by module reference on
Windows, where the parent is launched via `python -c` (no __main__.__file__).
"""

from __future__ import annotations

import multiprocessing as mp
import time
from typing import Any

import numpy as np


def worker(idx: int, arr: np.ndarray, q: Any) -> None:
    """Extract core33 for one chunk and put (idx, bytes) on the queue."""
    import kymora

    r = kymora.extract_features(np.ascontiguousarray(arr), n_jobs=1)
    q.put((idx, r.tobytes()))


def run_chunks(chunks: list[np.ndarray]) -> tuple[float, np.ndarray]:
    """Spawn one child per chunk, gate shape/dtype, return (wall_s, stacked_out)."""
    ctx = mp.get_context("spawn")
    q: Any = ctx.Queue()
    procs = [ctx.Process(target=worker, args=(i, c, q)) for i, c in enumerate(chunks)]
    t0 = time.perf_counter()
    for p in procs:
        p.start()
    got = [q.get() for _ in procs]
    for p in procs:
        p.join()
    wall = time.perf_counter() - t0
    got.sort(key=lambda kv: kv[0])
    y = np.vstack([np.frombuffer(b, dtype=np.float64).reshape(-1, 33) for _, b in got])
    return wall, y
