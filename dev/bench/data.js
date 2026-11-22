window.BENCHMARK_DATA = {
  "lastUpdate": 1795345420276,
  "repoUrl": "https://github.com/Aamodx6/Kymora",
  "entries": {
    "Kymora Core33 1kx500 Benchmark": [
      {
        "commit": {
          "author": {
            "email": "119789532+Aamodx6@users.noreply.github.com",
            "name": "Aamod",
            "username": "Aamodx6"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "f695a0e75a64659d13f31b762e71fbb6e2ae8185",
          "message": "Phase 2: CI, Regression Gates, Wheels, and Release Hardening (#26)\n\n* ci(phase-2): add regression benchmark gate, clean-install verification, and hardened release pipeline\n\n* ci: use valid commit SHA for benchmark-action/github-action-benchmark\n\n* ci: export benchmark to runner.temp and clean tree before branch switch",
          "timestamp": "2026-11-22T16:32:12+05:30",
          "tree_id": "74b68b0c6e6dae909148ad285a8909558a7d5d54",
          "url": "https://github.com/Aamodx6/Kymora/commit/f695a0e75a64659d13f31b762e71fbb6e2ae8185"
        },
        "date": 1795345419543,
        "tool": "customSmallerIsBetter",
        "benches": [
          {
            "name": "core33_1000x500",
            "value": 5.8653,
            "range": "0.0568",
            "unit": "ms",
            "extra": "runs=30, cv=0.016"
          }
        ]
      }
    ]
  }
}