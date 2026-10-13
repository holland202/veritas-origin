# AUTO-TWIN-001 — Multi-domain automation authorization boundary

**Status: Registered; no device run performed.** The eight domains are drone, mobile robot, robotic arm, industrial machine, warehouse AGV, building actuator, marine robot and software agent. Their simple braking/latency numbers are **invented illustrative parameters**, not engineering specifications or calibrated physics. The software-agent distance metric is purely abstract.

## Hypothesis and limitations
P1: A reference policy with current evidence accepts 320 nominal cases and defers/refuses 2,560 simulated negative cases.
P2: An intentionally broken cached-ALLOW comparator accepts all 2,560 negative cases.
P3: Claude-generated cases may expose violated registered invariants; **zero new counterexamples is an ordinary negative result** and does not establish safety.

No Sovereign Veritas Gate is imported in this stage. It is a reference policy versus negative control, NOT integrated SV verification, external penetration testing, drone dynamics, real robotics safety or adaptive learning. The scenarios are hand-defined with deterministic outcomes; the first run tests the harness, not a newly established capability. Avoid reporting 100% as evidence of operational safety.

## Freeze and spending policy
The baseline is offline and free. Optional Claude pilot uses the pinned model `claude-haiku-4-5-20251001`, maximum 2 synchronous requests, maximum 700 output tokens each. Input is fixed and restricted to a simple JSON scenario schema. This limits the number and size of submitted requests but is **not a guaranteed dollar billing cap**. API account usage must be checked separately. No batch endpoint, no continuous loop and no model-selection comparison. Do not retry blindly after timeouts because the API may have processed a request.

Each run creates a new timestamped local directory. Pilot ledger is updated within that directory and final SHA-256 hashes are stored; preserve intermediate states by making external checkpoint copies as needed. Errors count as failures/unevaluable, not as safe actions. No confidential third-party research inputs. Do not publish raw output until reviewed for sensitive material.

## Termux commands
```bash
cd ~
git clone --branch experiments/automation-twin-001 --single-branch https://github.com/holland202/veritas-origin.git vo-auto-twin
cd ~/vo-auto-twin/experiments/automation_twin_001
git rev-parse HEAD
python3 -I auto_twin.py selftest
python3 -I auto_twin.py baseline
```

For **separately authorized billable pilot**, after inspecting the baseline and verifying the API Console balance:
```bash
cd ~/vo-auto-twin/experiments/automation_twin_001
test -n "$ANTHROPIC_API_KEY" && echo "API key set" || echo "API key missing"
python3 -I auto_twin.py claude-pilot --calls 1
```
The second command sends **one** request and therefore incurs a charge. Nothing should run until the operator intentionally issues it. Never paste keys in chat, terminal logs or repository. Existing unrelated COLD-REVIEW-002 batch must be accounted for in the budget.
