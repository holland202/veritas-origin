# DPC-001 withheld cases: commitment only

The contents are **not** in this repository. Chad Holland holds the file, which Claude sent him privately on 2026-10-09. It is released only after a checker implementation is frozen, for the single authorised acceptance run (spec §6).

- Count: **6** cases (H01–H06). At least one is from outside the known historical experiment families.
- File: `withheld_cases.json`, SHA-256 of the exact bytes: `abb0120e9f5dffcb4665bfbc98d53accff55f1583157b7ebe68d8d7a97d7cb92`
- Per-case SHA-256: `sha256(json.dumps(case, sort_keys=True, ensure_ascii=False).encode())`:

| id | SHA-256 |
|---|---|
| H01 | `24a5d17f913ae2c83c9ba6df0b3a9e743ffeba0a0b3e534dac1fc9fa0715bb84` |
| H02 | `83a45d34ec35a7dcfda4431f43960022c522d59e5c3950160d5e8ceff7360dfc` |
| H03 | `fad6cdd3671b8f35b3978c72f81b7b7cb55e5320d904e04e7e5f9c4571db2e87` |
| H04 | `edddd18e8fbe61745912f05d5260a24ff8086713a1d4c26edb2aa9b88c268cef` |
| H05 | `a854821aea646ef543c6098317d93db62e2fcfd872e55bbd8ecb206e16b37888` |
| H06 | `a42253e9d5230ba6632d143b83dcf571b97e7c0cbb32862f0227e68e688120dc` |

Expected labels are deliberately not listed here. Limitation, as the spec says: a hash commits the contents, but it doesn't stop an AI from guessing likely cases. The withheld cases reuse the visible base contract and merge rule.
