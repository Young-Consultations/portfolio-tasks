# Required branch protection

Repository administrators must configure the `main` branch ruleset in GitHub under
**Settings → Rules → Rulesets** (or **Branches → Branch protection rules**) to require
a pull request and require status checks to pass before merging. Require branches to
be up to date before merging, and do not allow bypasses for ordinary contributors.

Select these required checks after they have run at least once:

* **PR CI / Python test suite**
* **PR CI / Workflow contract tests**
* **PR CI / Stubbed Codex end-to-end**
* **PR CI / actionlint**
* **PR CI / Codex wrapper integration tests**

The checks intentionally use a deterministic executable and receive neither
`CODEX_API_KEY` nor `OPENAI_API_KEY`. The production execution workflow remains a
separately dispatched, authorization-gated workflow. Branch protection is a manual
GitHub repository setting: committing this document and workflow does not itself
make checks mandatory.
