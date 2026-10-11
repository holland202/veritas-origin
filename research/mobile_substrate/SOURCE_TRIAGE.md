# Termux and AI-security GitHub source triage — implementation map

**Date:** 2026-10-11 (US Central). **Status:** source-level reconnaissance + bounded implementation, not package adoption, independent verification or authorized deployment.

## Classification

| Class | Source | Result | Current adoption decision |
|---|---|---|---|
| Official platform | [termux/termux-app](https://github.com/termux/termux-app/tree/8629e632fcb95da272221be327db653fb24befe9) | App/terminal is different from Termux packages. Android 12+ may kill background child processes or CPU-hungry tasks. | **ADOPTED IDEA**: passive substrate state, explicit runtime limits; no Android background daemon |
| Official package ecosystem | [termux/termux-packages](https://github.com/termux/termux-packages/tree/538b6e77f1aec908dad15d5e80d5015dff2bc7a5) | Source for Termux packages and build patches | **ADOPTED IDEA**: environment provenance rather than ordinary Ubuntu-pip assumptions; no package install |
| Official Android bridge | [termux/termux-api](https://github.com/termux/termux-api/tree/fc26ce17e3badf85d4df191af364fcf7798047f1) and [termux-api-package](https://github.com/termux/termux-api-package) | Android app + command helper and matching signatures/permissions; helper name presence is not app authority | **IMPLEMENTED**: read-only PATH indicators only. **DEFER** calls to actual Android API and sensitive data |
| Official boot integration | [termux/termux-boot](https://github.com/termux/termux-boot/tree/a8493bd6ba016bc370af34aa65fcbe065cc00ced) | Can autostart scripts | **DEFER**: no persistence or automatic research-agent startup; battery/process risks and authorization need separate study |
| Official external caller | [termux/termux-tasker](https://github.com/termux/termux-tasker/tree/dbf685fe2973c3490a27cbd37f31909ad5eb3bb3) | Tasker/plugin hosts can execute Termux commands | **DEFER**: app-invoked command does not prove the command passed a Veritas permission gate |
| Official launcher | [termux/termux-widget](https://github.com/termux/termux-widget/tree/b3aacb8175fb2d7167ce8d1ad6817087498aa044) | Home-screen shortcuts execute scripts | **DEFER**: explicit human invocation useful later, but need immutable signed task descriptor and mock effect |
| Optional display | [termux/termux-x11](https://github.com/termux/termux-x11/tree/fa3a8b430e2896a19f44c99a9cb056254615ae06) | Graphical display setup and signature/foreground priority caveats | **NOT NEEDED**: headless sensorless substrate check remains Python-only |
| Third-party Android agent platform | [mithun50/openclaw-termux](https://github.com/mithun50/openclaw-termux) | Flutter AI gateway, proot Ubuntu, Node/OpenClaw; docs describe optional SSH server and API-provider configuration | **REVIEW LATER**: significantly broader attack and secrets surface; not installed or run; proot is not assumed to be a strong sandbox |
| Third-party spec review | [TEKIMAX/speckit-security](https://github.com/TEKIMAX/speckit-security/tree/48312d105dfffecbdd5c963ab707a70e7de72ea6) | Third-party *alpha* Spec Kit extension for security gates, model/revision, privacy and prompt-injection review | **ADOPT METHOD ONLY**: preregister constraints and tests; neither tool nor template imported |
| Third-party agent developer harness | [tom-nwachuku/tgl](https://github.com/tom-nwachuku/tgl) | Plan/implementation split and per-slice adversarial review | **ADOPT METHOD ONLY**: bounded prospective plan and diff review, not autonomy or independent evidence |
| AI safety bibliography | [brandonhimpfen/awesome-ai-safety-alignment](https://github.com/brandonhimpfen/awesome-ai-safety-alignment) | Secondary index of safety literature | **DISCOVERY ONLY**: follow links to original papers and pinned source |
| Broad exploit/pentest installers or credential brute-force scripts shown in screenshots | SocialBox-Termux, Metasploit-in-Termux, generic “hacking toolkit” installers, unofficial sudo/root/proot packages | Popularity and one-line setup claims cannot establish supply-chain safety or scientific usefulness; may invoke privileged or credential-targeting operations | **EXCLUDED FROM RESEARCH BUILD**: no clones, scripts, root attempts, credential/target operations |
| Low-evidence “uncensored” assistant, speculative security datasets | Screenshot search hits only | No verified data lineage, license, test-oracle quality or safety methodology | **ACCESS/QUALITY UNVERIFIED**: not imported or used as benchmark |

## What was actually assimilated into executable code

`substrate_probe.py` emits a coarse, normalized manifest of current-process Linux confinement indicators, passive command lookup, and a **DEFER** response for any operation intent. It includes deterministic unsigned manifest fingerprinting, a preregistered synthetic matrix and separate CI Linux smoke tests.

**It does not enforce or install anything.** A future action broker would require separate in-scope proof of effective rules and enforcement and would not trust these self-observations as authority.

## Next implementable but *not yet built*

1. **TSP-002 (scope candidate):** source- and model-revision security checklist for reproducible experiments (inspired by spec-kit-security). Prospective typed schema and negative tests first; avoid claiming static checks prove security.
2. **TSP-003 (scope candidate):** explicitly owner-initiated Termux:API battery/thermal session with opt-in data categories, mocked API first, bounded events; raw health/location/contacts excluded.
3. **TSP-004 (scope candidate):** isolate an inert Work/Judge LDE experiment, with no network, separately held-out cases and budget limits. Requires Codeberg access; not already integrated.
4. **TSP-005 (scope candidate):** compare *actual* Android Termux and Linux host feature availability; independently measured S25 stdout, exit status, source hashes and process capabilities without assuming portability.

**No Android hardware, VEC, Sovereign Veritas or Codeberg LDE code was altered; all work is confined to an experimental Veritas-Origin branch.**
