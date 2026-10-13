# SV-ADAPT-BOUNDARY-001

**Preregistered demonstration, not yet run. $0 cloud/API cost.** Veritas-Origin hosts the experiment; it imports your actual Sovereign Veritas Gate but does not modify it.

The narrower research decision: *What externally verifiable evidence would a safe adaptation executor need to bind the update, approval, source, and epoch?* The script contrasts simulator-derived facts against forged booleans to expose the dependency. It does **not** implement NVIDIA's LoGRA method or test trained-model capabilities.

## Termux (paste commands separately)

```bash
cd ~
git clone --branch experiments/adaptation-evidence-boundary-001 --single-branch https://github.com/holland202/veritas-origin.git vo-adapt-study
```

```bash
test -f ~/sovereign-veritas/sovereign_veritas/decision.py || git clone https://github.com/holland202/sovereign-veritas.git ~/sovereign-veritas
```

```bash
cd ~/vo-adapt-study/experiments/adaptation_evidence_boundary_001
git rev-parse HEAD
git status --short
git -C ~/sovereign-veritas rev-parse HEAD
git -C ~/sovereign-veritas status --short
python3 -I sv_adapt_boundary.py selftest
```

```bash
python3 -I sv_adapt_boundary.py run
```

Run is local; output to a new folder inside `~/sv-adapt-boundary-evidence/`. Preserve printed output and include both repository revisions when sending results.

## Future paid work

Do **not** repeat commercial-model comparison. An actionable next experiment would use verified LDE learning on novel hidden affine/nonlinear worlds with frozen no-learning and scripted-learning baselines and negative controls (poisoned feedback, stale evidence, regression). Only pay for externally hosted experiments after the local demonstration verifies the input-boundary contract, and record an explicit spending cap and kill criterion. No paid work is preregistered here.

See [PREREGISTRATION.md](PREREGISTRATION.md).
