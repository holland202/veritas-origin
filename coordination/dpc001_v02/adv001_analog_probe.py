"""ADV-001 analog probe against the FROZEN DPC-001 v0.2 checker (bc43adf).

Origin: Gemini 3.1 proposed an adversarial suite "ADV-001" (four cases) relayed to Claude by Chad
Holland on 2026-10-09. Gemini wrote it without seeing this code, so its field names (author/auditor,
evidence_sha256, a facts *array*, an outcome label) do not exist in the v0.2 schema. Claude (Opus 5.5)
mapped each attack to the nearest v0.2 field and applied it as a single edit to the visible READY
case V15. These are VISIBLE adversarial cases, not blind: Claude saw the attack designs.

Expected labels (spec section in brackets). NOT PREREGISTERED: Claude ran an informal version of these
edits once before writing this file, so the expectations below were written after seeing results.
They are justified from the spec text, but this is a recorded regression probe, not a prediction test.
  control           READY_FOR_COMPARISON
  ADV-03a/b/c       CONTRACT_INVALID   [§1.4, §1.5 strict facts]
  ADV-04a/b         CONTRACT_INVALID   [§1.5 enum types]
  ADV-01            CONTRACT_INVALID   [§1.5 unknown key rejected]
  ADV-02            READY_FOR_COMPARISON  -- known limitation [§4: artifact links are declared, unverified]
Anti-vacuity: the control must stay READY; if every case came back INVALID the probe would be useless.

Usage: python3 -I adv001_analog_probe.py     (exit 0 = every result matched its expectation)
"""
import copy, hashlib, importlib.util, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN_SHA = "f2746a43e1e7360f645be912e552a84e53eca950d07d93d98adbc4d087eeca34"


def merge(base, over):  # identical rule to run_acceptance.py
    out = copy.deepcopy(base)
    for k, v in over.items():
        if v is None:
            out.pop(k, None)
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def main():
    path = os.path.join(HERE, "checker.py")
    got = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print(f"checker.py sha256 {got} {'== frozen' if got == FROZEN_SHA else '!= FROZEN -- not the frozen object'}")
    if got != FROZEN_SHA:
        return 2
    spec = importlib.util.spec_from_file_location("ck", path)
    ck = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ck)
    data = json.load(open(os.path.join(HERE, "visible_cases_v02.json"), encoding="utf-8"))
    v15 = next(c for c in data["cases"] if c["id"] == "V15")
    base = merge(data["base_contract"], v15["overrides"])

    def edit(fn):
        s = copy.deepcopy(base)
        fn(s)
        return s

    def set_att(k, v):
        return lambda s: s["facts"]["attestation"].__setitem__(k, v)

    R, I = "READY_FOR_COMPARISON", "CONTRACT_INVALID"
    cases = [
        ("control  V15 unchanged", base, R),
        ("ADV-03a  ATTESTED, every other facts section removed",
         edit(lambda s: s.__setitem__("facts", {"attestation": s["facts"]["attestation"]})), I),
        ("ADV-03b  facts = {}", edit(lambda s: s.__setitem__("facts", {})), I),
        ("ADV-03c  facts = []", edit(lambda s: s.__setitem__("facts", [])), I),
        ("ADV-04a  attestation.status = ['FAIL','PASS']", edit(set_att("status", ["FAIL", "PASS"])), I),
        ("ADV-04b  attestation.status = ['ATTESTED']", edit(set_att("status", ["ATTESTED"])), I),
        ("ADV-01   attestation.auditor added (self-review field)", edit(set_att("auditor", "claude")), I),
        ("ADV-02   bound_artifact = sha256('')@deadbeef",
         edit(set_att("bound_artifact", hashlib.sha256(b"").hexdigest() + "@deadbeef")), R),
    ]
    ok = 0
    for name, contract, want in cases:
        try:
            out = ck.classify(contract)
            got_l, codes = out.get("primary"), out.get("reason_codes")
        except Exception as e:  # a crash is a finding, never a pass
            got_l, codes = f"CRASH {type(e).__name__}", [str(e)]
        hit = got_l == want
        ok += hit
        print(f"{'as expected' if hit else 'UNEXPECTED '}  {name:55s} -> {got_l} {codes}")
    print(f"\nVERDICT  {ok} of {len(cases)} as expected  (ADV-02 READY = documented limitation, spec §4)")
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
