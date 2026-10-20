# Static GitHub Pages demo

The public demo is a static snapshot of freshly executed synthetic experiments.
It has no backend, paid service, credentials, database download, or live model
connection. Visitors can inspect captured evidence, filter scenarios, compare two
executions of the same fixed suites, and download JSON. They cannot execute tools
or start workers on the hosted page.

## Build locally

```sh
python -m tools.build_site
```

The builder runs fresh suites and the regression gate, then writes exactly
`index.html`, `report.json`, `.nojekyll`, and `SHA256SUMS` to `artifacts/site`.
The SQLite history database stays in a temporary build directory and is removed.
An existing output directory containing other files is rejected, not emptied or
published. A full Git SHA can be recorded with `--source-commit SHA`.

Browser acceptance tests include deployment under `/agent-reliability-lab/`,
matching GitHub Pages project URLs:

```sh
python -m tools.browser_smoke --static
```

The static report embeds all evidence and uses no absolute API paths, CDN scripts,
or external assets. No Python server is required after the build.

## Publish through GitHub Actions

The `Verified static demo` workflow in `.github/workflows/pages.yml` runs on
`main`, on `codex/reliability-public-demo`, and by manual workflow dispatch. It
runs ordinary tests, Hypothesis properties, the versioned regression gate, and
static browser acceptance before building and uploading the public artifact.
Deployment uses GitHub's Pages artifact/OIDC actions, not a personal access token.

A repository administrator must select **Settings → Pages → Build and deployment
→ Source: GitHub Actions**. If the `github-pages` environment restricts deployment
branches, allow the feature branch or use the reviewed main-branch workflow.
After Pages is enabled, rerun the workflow; use its deployment output URL as the
confirmed public demo address. Feature work is not automatically merged into main.

## Current publication evidence

GitHub confirms successful publication to [the demo](https://sairamande5-svg.github.io/agent-reliability-lab/) in
[workflow run 39508786286, attempt 3](https://github.com/sairamande5-svg/agent-reliability-lab/actions/runs/39508786286). All ten PR checks passed for
commit `3c091fa`, including the Python 3.11–3.13 matrix, browser checks, verified
static build, and deployment. The repository administrator enabled Pages with
GitHub Actions and allowed `codex/reliability-public-demo` alongside `main` in
the `github-pages` environment. No protection rules were removed.

The environment proxy still returns 403 for direct access to the public hostname.
Deployment success is independently confirmed through GitHub's deployment status,
but post-deployment browser interaction has not been checked from this machine.
Local Pages-style browser checks passed before publication.
