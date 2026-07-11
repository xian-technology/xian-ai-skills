---
name: xian-release-skill
description: Plan, validate, and create Xian workspace releases across sibling repos. Use when asked to decide whether Xian repos need new GitHub/PyPI/npm/GHCR releases, fix release-blocking validations, update dependent packages to newly released versions, or run the coordinated release order without beta/prerelease versioning unless explicitly requested.
---

# Xian Release Skill

Use this skill for release work in the local Xian sibling-repo workspace. Start
from `xian-meta/docs/WORKSPACE.md`, `xian-meta/workspace-repos.json`,
`xian-meta/docs/REPO_CONVENTIONS.md`, and `xian-meta/docs/CHANGE_WORKFLOW.md`,
then read each edited repo's `AGENTS.md` and `README.md`.

Do not treat the workspace as a monorepo. Keep changes inside the owning repo,
respect dirty worktrees, and do not modify `xian-intentkit` unless the user
explicitly asks for fork-specific work there.

## Default Release Path

Use the stable release flow by default. Do not pass `--beta` or another
prerelease channel unless the user explicitly requests a prerelease.

```bash
cd /Users/endogen/Projekte/xian/xian-stack
python3 ./scripts/release_orchestrator.py plan
python3 ./scripts/release_orchestrator.py apply
```

The orchestrator is the preferred path for repos it models because it:

- compares release units against their latest matching tag on `origin/main`
- plans releases in dependency order
- applies stable semver bumps when source files are not already prebumped
- updates dependent package versions where the release contract requires it
- blocks `apply` if required repos are dirty, off `main`, ahead/behind, missing
  GitHub checks, or have pending/failed GitHub checks on the exact release refs

## Release Order

Release dependency providers before consumers:

1. `xian-contracting` shared packages:
   `compiler-core-vX.Y.Z`, `accounts-vX.Y.Z`, `runtime-types-vX.Y.Z`, `zk-vX.Y.Z`
2. `xian-contracting`: `contracting-vX.Y.Z`
3. `xian-py`: `vX.Y.Z`
4. `xian-abci`: `vX.Y.Z`
5. `xian-cli`: `vX.Y.Z`
6. `xian-linter`: `vX.Y.Z`
7. `xian-js`: `vX.Y.Z`
8. `xian-wallet-browser`: `vX.Y.Z`
9. independent apps, when their own repo changed:
   `xian-wallet-mobile`, `xian-contracting-hub-web`
10. `xian-stack`: `vX.Y.Z`

`xian-wallet-browser` rolls after `xian-js`. `xian-stack` rolls last because
its release manifest pins component refs. `xian-wallet-mobile` and
`xian-contracting-hub-web` have independent tag-driven GitHub Release
workflows and should still wait for their own `main` validations before tags.

## Validation Gate

Never create or push a release tag for a failed ref. Before tagging:

1. Fetch origin and tags.
2. Confirm the repo is on clean `main` and matches `origin/main`.
3. Check GitHub validation on the exact SHA to be tagged.
4. Fix failing validations, push the fix to `main`, and wait for green checks.
5. Re-run the release plan after checks are green.

For repos outside the orchestrator, inspect checks directly:

```bash
gh run list --repo xian-technology/<repo> --branch main --limit 10
gh api "repos/xian-technology/<repo>/commits/<sha>/check-runs?per_page=100"
```

Treat missing, queued, in-progress, cancelled, timed-out, or failed check runs
as release blockers.

## Versioning

Choose the next stable semver version from the changes since the previous
release:

- patch: fixes, CI/release-flow repairs, dependency pin corrections, compatible
  documentation or packaging corrections
- minor: compatible public API or user-facing feature additions
- major: breaking public API, runtime, wire-format, or operator workflow changes

If a repo already contains the correct stable source version on `main`, use it.
Otherwise bump conservatively. Do not add `-beta` just because a previous
release used beta versioning.

## Dependencies After Release

After a provider release publishes successfully, update consumers that pin or
range-depend on that provider when the new release is required for their build,
tests, runtime behavior, or packaging. Validate the consumer before releasing it.

Common dependencies:

- `xian-wallet-browser` consumes `xian-js`
- `xian-stack` pins `xian-abci`, `xian-configs`, `xian-contracting`, and
  `xian-py` refs in `release-manifest.json`
- Python packages using `xian-tech-contracting`, `xian-tech-py`, or related
  workspace packages may need `pyproject.toml`, lockfile, and test updates
- npm consumers may need `package.json` and lockfile updates

## Repos Without Release Flow

If a repo has GitHub releases but no tag-driven release workflow, add or fix
the release flow before creating new tags. If the user explicitly accepts a
manual release as a temporary exception, still require green GitHub checks,
stable semver, and a clear GitHub Release tied to an immutable tag.
