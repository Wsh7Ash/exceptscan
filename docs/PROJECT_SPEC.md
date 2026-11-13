# PROJECT_SPEC — exceptscan

- **Name:** exceptscan
- **Category:** source-review
- **Target user:** Python reviewers and teams adopting an error-handling standard
- **Problem:** swallowed and silent exception handlers survive review because
  they read as "defensive" while deleting evidence of failure
- **Solution:** an AST-based scanner with four precise rules, file:line output,
  and a CI gate
- **Core workflow:** `exceptscan scan <path>` → findings → threshold exit code
- **Must-have features:** bare, pass-only, broad and no-response handlers;
  recursive scan with skips; parse-error handling; text/JSON; rule help
- **Nice-to-have features:** baseline file, inline suppressions, return-None check
- **Stack:** Python 3.10+ standard library (`ast`)
- **Test strategy:** inline source fixtures per rule, clean handlers, directory
  skip behaviour, syntax errors, CLI thresholds
- **Demo/result strategy:** scan `examples/bad_handler.py`, store text and JSON
- **Safety considerations:** read-only static analysis, no execution of scanned code
- **Definition of done:** tests pass, install works, demo recorded, docs accurate
