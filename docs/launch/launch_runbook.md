# Kymora Launch-Day Runbook & Operations Guide

> **STATUS:** MAINTAINER OPERATIONAL RUNBOOK.

---

## 1. Staged Launch Schedule

Do not post to all channels simultaneously. Use a staged roll-out to gather early technical feedback, catch unexpected environment issues, and refine FAQs before broad exposure.

| Stage | Target Channel | Timing | Primary Objective |
|---|---|---|---|
| **Stage 1: Soft Launch** | `/r/rust` & PyData Discourse | Day 1 (14:00 UTC) | Review Rust internals, PyO3 bindings, and packaging with technical communities. |
| **Stage 2: Main Launch** | **Show HN** | Day 3 (Tuesday/Wednesday 13:00 UTC / 08:00 EST) | Broad developer & data science visibility. Maintainer active in comments. |
| **Stage 3: Ecosystem Expansion** | `/r/Python`, `/r/MachineLearning`, LinkedIn, X | Day 4–5 | Machine learning practitioners, ecosystem integration tutorials. |

---

## 2. Maintainer Responsibilities & SLA

During the first 6 hours of any major launch stage (especially Show HN):
- **Presence:** At least one core maintainer actively monitoring comments and notifications.
- **Response SLA:** Aim for initial response within $< 2\ \text{hours}$ (ideally $< 30\ \text{minutes}$ on Show HN).
- **Tone:** Objective, technical, and appreciative. Emphasize reproducibility and transparent tradeoffs. Never become defensive.

---

## 3. Protocol for Handling Benchmark Disputes

Benchmark numbers frequently attract scrutiny. Follow this protocol when someone questions or contests published numbers:

1. **Acknowledge and Thank:**  
   *"Thank you for checking our numbers and running tests on your hardware!"*
2. **Request Environment Telemetry:**  
   Ask for their exact hardware environment:
   - CPU model and core layout (P/E-core configuration if Intel)
   - Operating system and kernel version
   - Power management profile (e.g., Performance vs Balanced)
   - Python and NumPy versions
3. **Offer One-Command Reproduction:**  
   Direct them to run the automated reproduction suite:
   ```bash
   git clone https://github.com/Aamodx6/Kymora.git
   cd Kymora
   ./reproduce.sh
   ```
4. **Update the Loss Ledger if Slower:**  
   If a user discovers a workload, shape, or architecture where Kymora underperforms or where a competitor achieves higher throughput:
   - Verify their artifact.
   - Commit the findings directly into `CLAIMS.md` under the Loss Ledger.
   - Credit the reporter in release notes.

---

## 4. Launch Day Checklist
- [ ] Verify `pip install kymora==0.8.2` works in a clean venv across Linux, macOS, and Windows.
- [ ] Confirm GitHub Discussions is enabled on `Aamodx6/Kymora`.
- [ ] Confirm issue templates and PR templates are active.
- [ ] Prepare drafted responses from FAQ in `docs/launch/show_hn.md`.
- [ ] Keep `reproduce.sh` link handy.
