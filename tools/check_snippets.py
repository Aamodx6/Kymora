"""Execute every ```python snippet in README.md + docs/*.md (stdlib only).

Usage:
    python tools/check_snippets.py [--timeout 120]

Rules:
  - Sources: README.md and top-level docs/*.md (docs/internal/refactor/** and
    docs/naming/** excluded — records and raw evidence, not guides).
  - A fence opens with ```python plus optional space-separated flags:
      skip        do not execute (with reason printed)
      timeout=N   per-snippet timeout override (seconds)
  - A block containing `# snippets: skip` anywhere is also skipped.
  - Blocks containing `>>>` run as doctests (via doctest.testmod-style
    parsing); all other blocks EXECUTE IN ONE SHARED NAMESPACE PER FILE,
    in document order — guides build on earlier cells notebook-style, and
    the README sklearn/streaming examples are additionally self-contained.
  - Each run uses a FRESH `sys.executable` subprocess (one per file, or
    one per doctest block) with cwd=repo root and inherited env (CI
    installs the built wheel first, so `import kymora` resolves).
Exit non-zero on any failure, or if zero snippets executed.
"""
import doctest
import glob
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEOUT = int(os.environ.get("SNIPPET_TIMEOUT", "120"))

SOURCES = ["README.md"] + sorted(
    f.replace("\\", "/")
    for f in glob.glob(os.path.join(ROOT, "docs", "*.md"))
)
FENCE = re.compile(r"^```python([^\n]*)\n(.*?)^```", re.M | re.S)


def iter_blocks(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    for m in FENCE.finditer(text):
        yield m.group(1).strip().split(), m.group(2)


def run_doctest(src, idx, code, timeout):
    parser = doctest.DocTestParser()
    test = parser.get_doctest(code, globs={}, name=f"{src}#{idx}",
                              filename=src, lineno=0)
    runner = doctest.DocTestRunner(verbose=False)
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        runner.run(test)
        out = buf.getvalue()
    finally:
        sys.stdout = old
    res = runner.summarize(verbose=False)
    return res.failed == 0, out


def main(argv):
    timeout = TIMEOUT
    if "--timeout" in argv:
        timeout = int(argv[argv.index("--timeout") + 1])
    ran, skipped, failed = 0, 0, []
    for src in SOURCES:
        stmts, doctests = [], []
        for idx, (flags, code) in enumerate(iter_blocks(src), 1):
            if "skip" in flags or "# snippets: skip" in code:
                print(f"SKIP {src}#{idx} ({' '.join(flags) or 'marker'})")
                skipped += 1
                continue
            (doctests if ">>>" in code else stmts).append((idx, flags, code))
        if stmts:
            prog = "\n\n".join(
                f"# ---- {src}#{i} ----\n{c}" for i, _, c in stmts
            )
            t = timeout
            for _, flags, _ in stmts:
                for fl in flags:
                    if fl.startswith("timeout="):
                        t = max(t, int(fl.split("=", 1)[1]))
            p = subprocess.run(
                [sys.executable, "-c", prog],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=t,
            )
            tag = ",".join(str(i) for i, _, _ in stmts)
            if p.returncode == 0:
                print(f"ok   {src}#[{tag}] ({len(stmts)} blocks, shared ns)")
                ran += len(stmts)
            else:
                print(f"FAIL {src}#[{tag}] (exit {p.returncode})")
                print("--- stderr (first 1500 chars) ---")
                print(p.stderr[:1500])
                failed.append(f"{src}#[{tag}]")
        for idx, _, code in doctests:
            ok, out = run_doctest(src, idx, code, timeout)
            if ok:
                print(f"ok   {src}#{idx} (doctest)")
                ran += 1
            else:
                print(f"FAIL {src}#{idx} (doctest)")
                print(out[:1500])
                failed.append(f"{src}#{idx}")
    print(f"--- {ran} executed, {skipped} skipped, {len(failed)} failed ---")
    if not ran or failed:
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
