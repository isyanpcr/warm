---
description: How to ask questions, report bugs, contribute code and docs, and report a security problem for WARM.
next_steps:
  - title: Governance
    text: Who decides what, and how.
    url: ../GOVERNANCE.md
  - title: How these docs are built
    text: The pipeline, the checks and how to run them.
    url: docs-pipeline.md
  - title: Security policy
    text: Report a vulnerability privately.
    url: ../SECURITY.md
---

# Community

WARM is maintained by WritersLogic under an Apache-2.0 license. Everything happens in public on
[GitHub](https://github.com/writerslogic/warm).

## Ask and report

| I want to | Go to |
|---|---|
| Ask how something works | [Discussions](https://github.com/writerslogic/warm/discussions), after checking the [FAQ](../reference/faq.md) and the [glossary](../reference/glossary.md) |
| Report a bug | [Open an issue](https://github.com/writerslogic/warm/issues/new/choose) with the smallest input that reproduces it, your OS, Rust and Node versions and the enabled Cargo features |
| Suggest a feature | An issue first, so the approach can be agreed before code is written |
| Report a vulnerability | Privately, as described in the [security policy](../SECURITY.md). Never in a public issue |

## Contribute

Start from a [good first issue](https://github.com/writerslogic/warm/labels/good%20first%20issue);
each names the files involved and how to check the result. [CONTRIBUTING.md](../../CONTRIBUTING.md)
covers setup, the checks CI runs and the DCO sign-off (no CLA). A change that compiles under only
one Cargo feature set is not done: `default = []`, so nothing is on unless asked for.

Docs: every page is Markdown under `docs/` with an edit button, and pages are listed by folder, so
a new page needs no configuration. Quickstart code is included from files CI runs, so keep
examples there. Checks to run before a pull request: [docs pipeline](docs-pipeline.md).

## Governance and conduct

- [Governance](../GOVERNANCE.md): roles, how decisions are made, how to become a committer.
- [Code of Conduct](../../CODE_OF_CONDUCT.md)
- [Security policy](../SECURITY.md)
