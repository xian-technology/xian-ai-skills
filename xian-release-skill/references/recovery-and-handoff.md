# Release recovery and handoff

Read this for failed publishing jobs, partially published versions, resumed
release trains or asynchronous image handoffs.

## Identify what failed

Separate the tag's source validation, artifact build and registry publication.
Inspect the failing job and its first actionable error before retrying. A
cancelled runner job with no steps can indicate an unavailable platform rather
than a source failure. Verify platform support and architecture using current
[GitHub runner images documentation](https://github.com/actions/runner-images).
For example, GitHub retired `macos-14` on 2026-11-02; changing ordinary main CI
would not fix a separate release matrix still using that label.

Check each destination independently. A dual Python/npm package can have its
npm release published even when Python wheel collection failed. Record that
partial state before choosing a recovery. Do not rerun an unchanged failure
repeatedly: a retry needs a specific fix or evidence that a transient condition
cleared. Continue other independent authorized work when possible.

## Preserve immutable source

Do not delete or move the failed release tag, or automatically bump all versions
again because a fresh plan sees a later CI-only commit. Keep the original tag
SHA and intended versions in the ledger. If the package source itself needs a
fix, prepare and validate a new version instead.

For an infrastructure-only failure, prefer a documented backfill that runs the
repaired workflow against the original tag. In `xian-contracting`:

```bash
gh workflow run release.yml --repo xian-technology/xian-contracting \
  --ref main -f release_tag=compiler-core-v0.2.1
```

Use the actual pending tag, not the example version. Confirm that the workflow:

- uses `refs/tags/<selected-tag>` in every validation/build checkout;
- derives expected package versions and final release names from that selected
  tag, rather than the dispatch branch's `github.ref_name`;
- keeps the artifact collection and publication gates, including every supported
  wheel platform and each publishing destination;
- preserves already published files and handles any supported retry/skip behavior
  deliberately. Do not hide arbitrary publication errors with skip-existing flags.

Wait for an obsolete attempt to finish or cancel only that superseded attempt
before retrying, to avoid competing publishers. Use existing successful artifacts
only if the workflow supports provenance-preserving reuse. Changing a workflow
on main does not change an old tag-triggered workflow when rerun.

The dispatch run's workflow SHA may be newer than the artifact source SHA. Record
both. Keep consumer source manifests pinned to the release's source, not to the
new workflow commit merely because it is now `origin/main`.

## Publication evidence

Useful probes, after selecting the correct versions and package names:

```bash
curl --fail https://pypi.org/pypi/<package>/<version>/json
npm view '<package>@<version>' version dist.integrity --prefer-online
npm view '<package>' dist-tags --json --prefer-online
gh release view '<tag>' --repo xian-technology/<repo> --json url,assets
```

A successful publish can precede registry processing and cache propagation.
If a version is temporarily missing, use fresh metadata and allow that processing
to complete before releasing dependents. Do not republish or bump a version
merely because a cached lookup returns an older tag or a 404.

Use the repo's release toolchain for install/package smoke tests. Compare the
expected artifact set with what published, including relevant wheels and extras.
A version in a registry is not evidence that another destination or architecture
finished. Keep source-only/private packages outside registry claims.

When resuming a train, reconcile the ledger with tags, workflow results and
registries before using the orchestrator again. Skip completed units so a
workflow-only fix does not cause another unrequested round of version bumps.

## Image handoff and deferred investigation

For a user-requested handoff without monitoring:

1. Finish the authorized package releases and source pins first.
2. Validate the final stack source commit and trigger its existing image workflow.
3. Identify that invocation with a creation lookup, not a watch loop. For a
   tag-triggered release, a useful lookup is:

   ```bash
   gh run list --repo xian-technology/xian-stack --workflow release.yml \
     --branch <stack-tag> --limit 1 --json databaseId,url,headSha
   ```

4. Save and return the actual run URL. Record images as triggered/pending, not
   published. Do not poll job status or inspect build logs afterward when the
   user has asked to monitor it themselves.
5. Resolve immutable image digests and update any pending digest pins only after
   publication is confirmed. A workflow URL or image tag is not a digest.

For deferred analysis/testing, save a repo-owned checkpoint with the question,
source/runtime versions, established observations versus hypotheses, exact
artifact locations, test commands/harness limitations, and the next experiment.
State what user event resumes the work. Release work does not itself authorize
upgrading a live chain, resetting its state or starting a saturation workload.
