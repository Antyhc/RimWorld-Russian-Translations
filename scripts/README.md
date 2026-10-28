# Project tools

Run commands from the repository root with Python 3.12 or newer. The main CLI uses only the standard library. The tools do not log into Steam, publish packages, translate text with a model, or run RimWorld.

```powershell
python scripts/rwtranslations.py registry
python scripts/rwtranslations.py validate
python scripts/rwtranslations.py validate --release
python -m unittest discover -s tests -v
```

Inventory validation permits records without distributable files. `--release` applies the stricter rights, provenance, review, current-source and package checks and reports each blocker. A pending record is useful inventory, not approval to publish. `github_metadata_records` counts linked inventory records; `github_published` counts linked translation payloads explicitly marked published.

Each new `mods/<package_id>/manifest.json` is discovered automatically. The JSON schema in `schemas/manifest.schema.json` documents fields. CLI validation implements the release-critical checks; it does not run a general JSON Schema engine.

Each distributable package resides in `mods/<package_id>/payload/`, with `About/About.xml` and `Languages/Russian/{Keyed,DefInjected,Strings}/...`. The translation has a distinct PackageId, declares the original as a dependency, and loads after the original. Release versions must match the manifest and be a subset of the original mod's declared versions. Files outside the localization allowlist are refused. `About/Preview.png` additionally needs confirmed icon rights. No original DLLs, textures or sounds are allowed.

Necessary UTF-8 notices are allowed at `About/License.txt`, `About/Credits.txt`, `LICENSE`, `LICENSE.txt`, `CREDITS.txt` and `NOTICE`. Record exact required paths and SHA256 file hashes in `rights.translation.required_notice_files`; release checks require a nonempty notice map and every declared file unchanged. This records reviewed license conditions without guessing what a particular license requires. Translation PackageIds must use dotted alphanumeric segments and fit the game's 60-character limit; choose a stable shorter identifier where the original PackageId plus translation prefix would exceed that limit.

```powershell
python scripts/rwtranslations.py snapshot "C:/local/original/Languages/English" mods/example.mod/source.snapshot.json
python scripts/rwtranslations.py snapshot "C:/local/updated/Languages/English" reports/example.mod.new.json
python scripts/rwtranslations.py diff mods/example.mod/source.snapshot.json reports/example.mod.new.json reports/example.mod.delta.json
python scripts/rwtranslations.py prepare-update example.mod "C:/local/updated/Languages/English"
python scripts/rwtranslations.py stage example.mod --output dist
```

Snapshots contain keys, SHA256 text hashes and placeholder/tag signatures, not complete original English text. Every release key must match a source-bound signature; a bare hash without a signature is insufficient. The extractor covers localization files; C# literals, custom dynamic fields, arbitrary XML Def inheritance and runtime-generated text require the established local project's additional tools and real game testing. A snapshot does not prove full coverage. Local snapshots may include a `texts` mapping when rights permit; signatures are then derived from those texts.

Release QA must record `payload_sha256` (canonical SHA256 of the sorted relative-path to file-hash map; `rwtranslations.payload_digest(payload_dir)`), `source_snapshot_sha256` (the snapshot file's byte SHA256), `checked_at` within seven days and `source_checked_at` within 24 hours, all in timezone-aware ISO format. Changed payload or source snapshot bytes invalidate the approval. These bindings supplement the required recorded QA evidence, reviewed language state and confirmed rights. The tool does not manufacture a source-current approval from old snapshots. This conservative first package layout uses root `Languages/Russian`; custom `loadFolders.xml` layouts are refused until separately supported.

`prepare-update` creates an ignored local review queue under `reports/pending/`. Added or changed English sources receive empty proposed translations and a review-required state. Existing Russian text is copied into the report for comparison and is never overwritten. Removed source keys are reported without deleting their translations. Review new machine translations before changing a manifest's approval state.

`stage` creates a fresh output folder and a SHA256 release manifest. Existing staged folders are never overwritten. It does not upload to Steam. In the authenticated Steam client, upload the prepared package, set and verify the original Workshop dependency, verify the public page, then record the actual Workshop ID/URL in the manifest and regenerate the registry. A package with `in_game: not_tested` must be described that way; staging is a static check.

## Monitoring

For each known official upstream, configure either a JSON hash snapshot URL or explicit source language file URLs. Both are restricted to HTTPS `raw.githubusercontent.com` or `api.github.com` (redirects too). Set a baseline containing exactly the monitored key scope. Example shape only; replace URLs after verifying the official repository, branch and files:

```json
{
  "monitor": {
    "files": [
      {"url": "https://raw.githubusercontent.com/OWNER/REPO/BRANCH/Languages/English/Keyed/Main.xml", "kind": "Keyed"}
    ]
  }
}
```

DefInjected files also set `def_type`; Strings files set `path` relative to their `Strings/` directory (an optional leading `Strings/` is normalized). `snapshot_url` instead expects a JSON `strings` map of key to SHA256 hash. Explicit-file monitors do not discover newly added files; update the list after a source-tree audit. No source endpoint is invented automatically. Unconfigured records are reported as `not_configured`, not as up to date. Strings are indexed by lines with empty lines retained and final newline ignored by this extractor; real game merge/line semantics require separate `qa.strings_semantics_evidence` before release.

```powershell
python scripts/rwtranslations.py monitor
```

The scheduled workflow checks only configured sources once daily. It keeps one bot issue for changed/failed sources and does not update the issue when the same fingerprint recurs. Changes and failures are reported; Russian translations and baselines remain unchanged. The workflow does not contact developers or upload Workshop packages. The repository's normal GitHub Actions token is sufficient; no Steam passwords or tokens are needed. An Actions-disabled repository or unavailable source endpoint is a separate deployment blocker.

Recorded public `integration.pr_url` links are also checked through the GitHub API. Merged PRs report `accepted`; closed but unmerged PRs report `closed_unmerged` rather than assuming rejection. Latest decisive reviews per reviewer detect `changes_requested`; API errors require attention. The monitor reports these observations without rewriting manifests or editing upstream PRs. After review, set the corresponding `integration.status` to acknowledge the state; unchanged acknowledged states do not generate repeated issue edits. The Actions job supplies its normal ephemeral `GITHUB_TOKEN` to API requests for rate limits; the token is never written to files or passed to raw-content endpoints.

For mods whose source format requires custom extraction, whole-repository tree monitoring catches updates without guessing translation keys or copying original assets. It records Git blob/gitlink object hashes and compares added, changed and removed repository files, including new files not known when the baseline was made. Use a known moving upstream branch in the monitor and preserve the reviewed baseline until the change is investigated:

```powershell
python scripts/rwtranslations.py tree-snapshot OWNER/REPO main mods/example.mod/source.tree.json
```

```json
{
  "monitor": {
    "github_tree": {
      "repository": "OWNER/REPO",
      "ref": "main",
      "baseline_file": "source.tree.json"
    }
  }
}
```

The tree baseline contains `repository`, `ref`, `files` (repository-relative path → Git object SHA), plus optional provenance metadata. It must match the configured repository/ref and remain inside that mod directory. Whole-tree reports appear under `file_monitors`; a changed file requires impact review and is not reported as a changed translation string. Truncated API trees fail explicitly. Repositories shared by several translations are fetched once per monitor run. This can be combined with exact language-file/key monitoring; the key snapshot and repository tree baseline have different scopes.

## Public Steam update metadata

`python scripts/rwtranslations.py workshop-snapshot source.workshop.json` captures
public update times, sizes and UGC content handles for every original Workshop ID
discovered from the manifests, in batches of at most 50. This uses Valve's documented
[GetPublishedFileDetails](https://partner.steamgames.com/doc/webapi/ISteamRemoteStorage#GetPublishedFileDetails)
POST endpoint without API keys, cookies or account access. Creator SteamIDs,
descriptions and resource URLs are discarded. The normal scheduled monitor compares
these fields without downloading mods or replacing Russian text. An updated Workshop
publication requires local source/key comparison and review; it grants no freshness
or publication approval. Newly registered IDs without a baseline are reported explicitly.
Keep the old baseline until changes are reviewed; capture a new one to a separate file.

## Covers

`cover.py` uses the original pixels, dimensions and proportions. It adds one translucent bottom band and the word `RUSSIAN`. The original is never overwritten. It refuses unknown icon reuse/modification rights and requires a local bold TTF font path, allowing the same font to be used consistently. No cover should be generated from or published with an unlicensed original. Set `rights.icon.source_sha256` to the exact authorized original image hash. After generation, copy the reported `preview_sha256` into `rights.icon.preview_sha256`; release validation binds the cover bytes to this record.

```powershell
python -m pip install -r requirements.txt
python scripts/cover.py "C:/authorized-original.png" "mods/example.mod/payload/About/Preview.png" --manifest mods/example.mod/manifest.json --font "C:/licensed-fonts/SomeBold.ttf"
```

Optional Pillow installation is a user/environment operation; this task does not silently install software. Review every resulting cover at thumbnail size and ensure the bottom band does not obscure important art before publishing.
