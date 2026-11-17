---
name: xian-release-skill
description: Plan, publish, verify, and recover coordinated Xian package and container releases across sibling repos, including dependency pins and immutable release sources.
---

# Xian Release Skill

Start with `xian-meta/docs/WORKSPACE.md`, `workspace-repos.json`,
`docs/REPO_CONVENTIONS.md`, and `docs/CHANGE_WORKFLOW.md`, then each edited
repo's `AGENTS.md` and `README.md`. This is a sibling-repo workspace, not a
monorepo. Keep local defaults and draft network status intact. `xian-intentkit`
is an exempt upstream fork; include it only for explicitly requested fork work.
A request to plan or assess releases does not authorize publishing them.

## Discover and freeze the train

Use stable versions unless the user requests a prerelease. From `xian-stack`:

```bash
python3 scripts/release_orchestrator.py plan
```

The orchestrator models the shared contracting packages, SDKs, ABCI, CLI,
linter, browser wallet and stack. Inspect other repos' actual workflows as
well: mobile wallet, contracting hub, DEX, DEX automation and MCP server have
independent release flows. Do not infer release support from a version field
or invent a publishing destination. Private packages and source-only crates
may deliberately have no registry release.

Record the intended units, versions, immutable source SHAs, dependency edges,
tag names and publishing destinations in a repo-local release ledger. Track
per-destination completion and workflow URLs there as work proceeds. This lets
a resumed run distinguish planned, tagged, published and failed units without
creating another version for work already released.

Choose patch/minor/major from the public changes since the matching unit tag.
Use an appropriate pre-bumped source version when present. Check package-specific
tag prefixes; the greatest semver tag in a multi-package or historical repo
need not be the current release line. Avoid `--force-all` when resuming a train.

Resolve every sibling build/test checkout in release workflows, including refs
outside `release-manifest.json`, and compare it with the frozen train. Main CI
may replace pinned refs with matching branches: green main does not validate a
release using older sibling fixtures. Validate the pinned release input set
when it differs from the set already tested; repair stale refs before tagging.

Before pushing tags, inspect build matrices, toolchains, registry credentials/
trusted-publisher setup and available disk. Verify questionable runner labels
against current GitHub runner documentation; ordinary main CI may not exercise
all release platforms. See [recovery and handoff](references/recovery-and-handoff.md)
when a platform or publishing step fails.

## Prepare, validate, then tag

The orchestrator is the preferred tagging tool, but inspect its current
implementation before `apply`. It currently checks input refs **before**
creating metadata commits and does not wait for the new commits' CI or for
registry publication. An initial green check is not sufficient for a version
commit that `apply` would create afterward.

1. Prepare version metadata, required dependency changes and lockfiles first.
   Use existing sync helpers or edit the owning files; do not assume a `prepare`
   CLI subcommand exists. Align Python, Cargo, npm, extension/Expo/Android
   versions and build numbers where the repo's release contract requires them.
2. Validate each affected repo, commit and push the preparation changes.
3. Wait for required validations on the **exact commit to be tagged**. Require
   clean `main` matching `origin/main` for a new release. Missing or pending
   checks block tagging. Use the latest applicable attempt of each required
   validation; retain failed publication attempts as recovery history.
4. Recheck the selected plan against the ledger. Apply only ready units using
   the orchestrator's supported selection controls (currently `--skip-unit`).
   All metadata synchronization for those units must already be a no-op;
   otherwise prepare the changes and validate their new SHA before tagging.
5. Record tag SHAs and publishing workflow URLs. A pushed tag starts a release;
   it does not prove that its packages were published.

Inspect checks when needed:

```bash
gh api "repos/xian-technology/<repo>/commits/<sha>/check-runs?per_page=100"
gh run list --repo xian-technology/<repo> --limit 10
```

Do not move an existing release tag to repair CI. Fix the relevant cause and
use an immutable-tag backfill when supported; see the recovery reference.

## Publish in dependency order

Use the actual dependency graph, including extras and build inputs. The usual
order is shared contracting packages → contracting → Python SDK/ABCI/linter/JS
SDK → CLI/wallets/apps → stack. Independent ready units can run concurrently;
a consumer must wait for its required provider artifacts, not just their tags.
For example, a compiler release is not complete when npm succeeds but its
Python wheel publication fails.

| Repo or unit | Publishing surface |
| --- | --- |
| Contracting accounts/runtime-types/compiler-core/VM/zk/root | Separate PyPI packages and tag prefixes; compiler also publishes npm |
| Python SDK, ABCI, CLI, linter | PyPI and GitHub releases |
| JS SDK | Coordinated `@xian-tech/*` npm packages and GitHub release |
| Browser wallet | `@xian-tech/wallet-core` npm package and extension assets |
| Mobile, contracting hub, DEX, automation, MCP server | Their existing GitHub release assets; inspect workflows for precise formats |
| Stack | Container images and release evidence; run last |

Consumers may be prepared and tested against sibling sources while providers
build. Publish them only after the provider versions required by their supported
install paths are available. Recheck any standalone install path after publication.

## Keep pins coherent

- Update direct requirements when the new provider is required, and regenerate
  locks for changed sibling metadata. Check other affected repos even when they
  do not publish; stale local-package versions break locked installs there too.
- Keep published extras split correctly, such as SDK compile/eth/hd and runtime
  zk extras. Do not let a sibling checkout hide a missing registry dependency.
- Resolve release manifests and workflow checkouts to immutable **released
  source** commits. A later infrastructure-only fix on `main` need not change
  the source used for an existing tag. Do not blindly replace pins with latest
  `main` during recovery.
- After the relevant registry release works, remove temporary source overrides
  only where they were a bridge to that release; refresh locks and standalone
  tests, README instructions and Docker references together. Preserve deliberate
  historical pins, especially migration tooling, and the exempt fork.
- Refresh stack component refs and localnet product/CLI pins after the selected
  source commits are final. Review embedded network release manifests and the
  release hygiene in `MAINNET_LAUNCH_PLAN.md`; updating pins does not authorize
  a public-network launch or changing local defaults.

## Verify and hand off

Check publishing workflow results and actual destinations: PyPI version JSON
and distributions, npm version metadata/dist-tags, or GitHub asset names and
checksums as appropriate. Smoke-test an affected standalone install without
sibling or temporary source overrides, including the relevant extras. Report
partial publication precisely rather than calling the whole release complete.

Resolve the stack's final source manifest, validate its exact tag commit, and
trigger its image release last. When the user asks for a build-only handoff,
look up the new workflow URL once, give it to them, and do not poll/watch its
jobs. Do not invent an image digest before publication. Record the pending
handoff and any investigation checkpoint needed for later work; see
[recovery and handoff](references/recovery-and-handoff.md).

A repo without a release workflow needs a supported release path before tagging;
a manual publishing exception requires explicit user authorization. Do not
normalize IntentKit's upstream `0.0.0` version: its fork release flow injects
release metadata independently.
