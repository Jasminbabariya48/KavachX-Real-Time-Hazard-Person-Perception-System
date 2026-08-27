# Repository Architecture & Standards

1. **Production Code:** Only production-ready code belongs in `src/kavachx/` and `native/worker/`.
2. **No Milestone Naming:** Production filenames, symbols, and comments must never contain step/phase numbers.
3. **Tests:** All tests must live under `tests/` and be named `test_*.py`.
4. **Tools:** Diagnostic utilities belong in `tools/`.
5. **Historical Data:** Retained development evidence belongs in `archive/` or `reports/`.
