#!/usr/bin/env python3
"""Discover, audit and stage translation-only RimWorld packages.

The registry describes work in progress. A registry entry is not a release approval.
Only standard-library modules are required; no Steam credentials are used.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 10 * 1024 * 1024
TOKEN = re.compile(r"(?<!\{)\{[^{}\r\n]+\}(?!\})|\$\([^\r\n)]+\)|\[[A-Za-z_][A-Za-z0-9_.: /=-]*\]|%(?:\d+\$)?[sdif]|\\[nrt]")
TAG = re.compile(r"</?[A-Za-z][^<>]*>")
PACKAGE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
TRANSLATION_PACKAGE_ID = re.compile(r"^[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)+$")
NOTICE_FILES = {"About/License.txt", "About/Credits.txt", "LICENSE", "LICENSE.txt", "CREDITS.txt", "NOTICE"}


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def within(path, root):
    """Resolve before checking: junctions/symlinks must not escape the project."""
    resolved, base = Path(path).resolve(), Path(root).resolve()
    if not resolved.is_relative_to(base):
        raise ValueError(f"Path escapes permitted directory: {path}")
    return resolved


def parse_xml(data):
    if len(data) > MAX_BYTES:
        raise ValueError(f"XML larger than {MAX_BYTES} bytes")
    if b"\x00" in data:
        raise ValueError("Only UTF-8-compatible XML is accepted; transcode UTF-16/32 first")
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("DTD/entities are forbidden")
    return ET.fromstring(data)


def safe_xml(path):
    return parse_xml(Path(path).read_bytes())


def compare_tokens(source, translated):
    errors = []
    if Counter(TOKEN.findall(source)) != Counter(TOKEN.findall(translated)):
        errors.append("placeholder_mismatch")
    if Counter(TAG.findall(source)) != Counter(TAG.findall(translated)):
        errors.append("format_tag_mismatch")
    if not balanced_tags(translated):
        errors.append("format_tags_unbalanced")
    return errors


def balanced_tags(value):
    stack = []
    standalone = {"br", "sprite", "quad", "space", "page", "pos"}
    for tag in TAG.findall(value):
        match = re.match(r"<(/?)([A-Za-z][A-Za-z0-9_-]*)", tag)
        if not match:
            return False
        closing, name = match.groups()
        if tag.endswith("/>") or name.lower() in standalone:
            continue
        if closing:
            if not stack or stack.pop() != name:
                return False
        else:
            stack.append(name)
    return not stack


def extract_language(root):
    """Read language files only. This does not extract arbitrary C# literals/Defs."""
    root = Path(root)
    rows, errors = {}, []
    if not root.is_dir():
        return {}, [f"language_directory_missing:{root}"]
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        within(path, root)
        rel = path.relative_to(root)
        parts = rel.parts
        if parts[0] in ("Keyed", "DefInjected") and path.suffix.lower() == ".xml":
            try:
                doc = safe_xml(path)
                if doc.tag != "LanguageData":
                    errors.append(f"wrong_xml_root:{rel}")
                    continue
                if parts[0] == "DefInjected" and len(parts) < 3:
                    errors.append(f"def_type_directory_missing:{rel}")
                    continue
                prefix = "Keyed|" if parts[0] == "Keyed" else f"DefInjected|{parts[1]}|"
                for node in doc:
                    key = prefix + node.tag
                    if list(node):
                        errors.append(f"nested_language_node:{rel}:{node.tag}")
                    if key in rows:
                        errors.append(f"duplicate_key:{key}")
                    rows[key] = node.text or ""
            except (ET.ParseError, ValueError) as ex:
                errors.append(f"invalid_xml:{rel}:{ex}")
        elif parts[0] == "Strings" and path.suffix.lower() == ".txt":
            text = path.read_text(encoding="utf-8-sig")
            for i, value in enumerate(text.splitlines()):
                rows[f"Strings|{Path(*rel.parts[1:]).as_posix()}|{i}"] = value
        else:
            errors.append(f"unsupported_language_file:{rel}")
    return rows, errors


def hashes(rows):
    return {key: hashlib.sha256(value.encode("utf-8")).hexdigest() for key, value in sorted(rows.items())}


def signatures(rows):
    return {key: {"source_hash": hashlib.sha256(value.encode("utf-8")).hexdigest(), "tokens": sorted(TOKEN.findall(value)), "tags": sorted(TAG.findall(value)), "source_empty": not bool(value.strip())} for key, value in sorted(rows.items())}


def file_hashes(folder):
    folder = Path(folder)
    result = {}
    for path in sorted(folder.rglob("*")):
        within(path, folder)
        if path.is_file():
            result[path.relative_to(folder).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def payload_digest(folder):
    return hashlib.sha256(json.dumps(file_hashes(folder), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def fresh_timestamp(value, max_age):
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if moment.tzinfo is None:
            return False
        age = datetime.now(timezone.utc) - moment
        return timedelta(minutes=-5) <= age <= max_age
    except (ValueError, TypeError):
        return False


def delta(old, new):
    return {
        "added": sorted(new.keys() - old.keys()),
        "changed": sorted(key for key in old.keys() & new.keys() if old[key] != new[key]),
        "removed": sorted(old.keys() - new.keys()),
    }


def manifests(root=ROOT):
    for path in sorted((Path(root) / "mods").glob("*/manifest.json")):
        within(path, root)
        obj = read_json(path)
        package = obj.get("package_id", "")
        if not isinstance(package, str) or not PACKAGE_ID.fullmatch(package):
            raise ValueError(f"Invalid package_id in {path}")
        if path.parent.name != package:
            raise ValueError(f"Manifest directory must equal package_id: {path}")
        yield path, obj


def metadata_errors(manifest):
    errors = []
    if manifest.get("schema_version") != 1:
        errors.append("unsupported_manifest_schema")
    if not manifest.get("name"):
        errors.append("name_missing")
    original = manifest.get("original", {})
    if original.get("workshop_id") and not str(original["workshop_id"]).isdigit():
        errors.append("invalid_workshop_id")
    for key in ("workshop_url", "repository_url"):
        if original.get(key) and not str(original[key]).startswith("https://"):
            errors.append(f"invalid_original_{key}")
    return errors


def confirmed_rights(manifest, material):
    rights = manifest.get("rights", {}).get(material, {})
    return rights.get("status") == "confirmed" and all(rights.get(key) for key in ("license", "evidence", "attribution"))


def validate_payload(folder, manifest, release=False):
    folder = Path(folder)
    errors, warnings = [], []
    payload = folder / "payload"
    if not payload.is_dir():
        return ["payload_missing"], warnings, {}
    within(payload, folder)
    for path in sorted(payload.rglob("*")):
        within(path, payload)
        if not path.is_file():
            continue
        rel = path.relative_to(payload).as_posix()
        allowed = rel == "About/About.xml" or rel in NOTICE_FILES or rel.startswith("Languages/Russian/") and path.suffix.lower() in (".xml", ".txt")
        if rel in NOTICE_FILES:
            try:
                content = path.read_bytes()
                if len(content) > 256 * 1024 or b"\x00" in content:
                    raise ValueError("Notice must be bounded UTF-8 text")
                content.decode("utf-8-sig")
            except (UnicodeDecodeError, ValueError):
                errors.append(f"invalid_notice_text:{rel}")
        if rel == "About/Preview.png":
            allowed = confirmed_rights(manifest, "icon")
            icon = manifest.get("rights", {}).get("icon", {})
            if not re.fullmatch(r"[0-9a-f]{64}", str(icon.get("source_sha256", ""))) or icon.get("preview_sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
                errors.append("icon_source_or_preview_hash_unbound")
        if not allowed:
            errors.append(f"forbidden_payload_file:{rel}")
        if path.suffix.lower() == ".xml":
            try:
                safe_xml(path)
            except (ET.ParseError, ValueError) as ex:
                errors.append(f"invalid_xml:{rel}:{ex}")
    about = payload / "About" / "About.xml"
    if not about.is_file():
        errors.append("about_missing")
    else:
        try:
            doc = safe_xml(about)
            original_id = manifest["package_id"]
            translation_id = manifest.get("translation_package_id", "")
            if doc.tag != "ModMetaData":
                errors.append("about_root_invalid")
            if not translation_id or len(translation_id) > 60 or not TRANSLATION_PACKAGE_ID.fullmatch(translation_id) or translation_id.lower() == original_id.lower():
                errors.append("translation_package_id_invalid")
            if (doc.findtext("packageId") or "").lower() != translation_id.lower():
                errors.append("about_package_id_mismatch")
            dependencies = [(n.findtext("packageId") or "").lower() for n in doc.findall("modDependencies/li")]
            if original_id.lower() not in dependencies:
                errors.append("original_dependency_missing")
            after = [(n.text or "").lower() for n in doc.findall("loadAfter/li")]
            if original_id.lower() not in after:
                errors.append("original_load_after_missing")
            declared = [n.text for n in doc.findall("supportedVersions/li")]
            supported = manifest.get("supported_versions", [])
            upstream_versions = manifest.get("original", {}).get("supported_versions", [])
            if not supported or set(declared) != set(supported) or not set(supported).issubset(upstream_versions):
                errors.append("supported_versions_not_confirmed")
        except (ET.ParseError, ValueError, KeyError) as ex:
            errors.append(f"about_invalid:{ex}")
    rows, language_errors = extract_language(payload / "Languages" / "Russian")
    errors.extend(language_errors)
    if not rows:
        errors.append("translation_empty")
    source = folder / "source.snapshot.json"
    if source.is_file():
        snapshot = read_json(source)
        source_hashes = snapshot.get("strings", {})
        for key, value in rows.items():
            if key not in source_hashes:
                warnings.append(f"key_without_source_baseline:{key}")
        # Optional private source texts enable exact placeholder/tag comparison.
        # Public hash-only snapshots are deliberately insufficient to claim that check.
        texts = snapshot.get("texts", {})
        source_signatures = snapshot.get("signatures", signatures(texts))
        for key in rows.keys() & texts.keys():
            errors.extend(f"{kind}:{key}" for kind in compare_tokens(texts[key], rows[key]))
        for key, value in rows.items():
            signature = source_signatures.get(key)
            if key not in source_hashes or not signature or signature.get("source_hash") != source_hashes[key]:
                (errors if release else warnings).append(f"source_signature_missing_or_unbound:{key}")
                continue
            if sorted(TOKEN.findall(value)) != signature.get("tokens"):
                errors.append(f"placeholder_mismatch:{key}")
            if sorted(TAG.findall(value)) != signature.get("tags"):
                errors.append(f"format_tag_mismatch:{key}")
            if not balanced_tags(value):
                errors.append(f"format_tags_unbalanced:{key}")
            if not value.strip() and signature.get("source_empty") is not True:
                errors.append(f"empty_translation:{key}")
    else:
        warnings.append("source_snapshot_missing")
    if release:
        if not confirmed_rights(manifest, "translation"):
            errors.append("translation_rights_unconfirmed")
        required_notices = manifest.get("rights", {}).get("translation", {}).get("required_notice_files", {})
        if not required_notices:
            errors.append("license_notice_requirements_unrecorded")
        elif not isinstance(required_notices, dict):
            errors.append("license_notice_requirements_invalid")
        else:
            for notice, digest in required_notices.items():
                if notice not in NOTICE_FILES:
                    errors.append(f"required_notice_path_not_allowed:{notice}")
                    continue
                notice_path = payload / notice
                if not notice_path.is_file() or hashlib.sha256(notice_path.read_bytes()).hexdigest() != digest:
                    errors.append(f"required_notice_missing_or_changed:{notice}")
        qa = manifest.get("qa", {})
        if qa.get("technical") != "passed":
            errors.append("technical_qa_not_passed")
        if qa.get("linguistic") not in ("ai_reviewed", "human_reviewed"):
            errors.append("linguistic_review_pending")
        if qa.get("source_current") is not True:
            errors.append("source_not_current")
        if not qa.get("checked_at") or not qa.get("evidence"):
            errors.append("qa_evidence_missing")
        if not fresh_timestamp(qa.get("checked_at"), timedelta(days=7)):
            errors.append("qa_check_stale_or_undated")
        if not fresh_timestamp(qa.get("source_checked_at"), timedelta(days=1)):
            errors.append("source_check_stale_or_undated")
        if qa.get("payload_sha256") != payload_digest(payload):
            errors.append("qa_payload_digest_mismatch")
        if source.is_file() and qa.get("source_snapshot_sha256") != hashlib.sha256(source.read_bytes()).hexdigest():
            errors.append("qa_source_snapshot_digest_mismatch")
        if qa.get("in_game") == "failed":
            errors.append("in_game_failed")
        if manifest.get("duplicate_translation", {}).get("status") != "checked_no_current_equivalent":
            errors.append("existing_translation_check_pending")
        if not source.is_file():
            errors.append("source_snapshot_missing")
        if any(key.startswith("Strings|") for key in rows) and not qa.get("strings_semantics_evidence"):
            errors.append("strings_runtime_semantics_unverified")
    return sorted(set(errors)), sorted(set(warnings)), rows


def audit(root=ROOT, release=False):
    reports, seen = [], set()
    for path, manifest in manifests(root):
        errors = metadata_errors(manifest)
        package = manifest["package_id"]
        if package.lower() in seen:
            errors.append("duplicate_package_id")
        seen.add(package.lower())
        payload_errors, warnings, rows = validate_payload(path.parent, manifest, release)
        # Pending inventory rows may intentionally have no distributable payload.
        if not release and not (path.parent / "payload").exists():
            warnings.extend(payload_errors)
        else:
            errors.extend(payload_errors)
        reports.append({"package_id": package, "errors": errors, "warnings": warnings, "language_entries": len(rows), "release_eligible": release and not errors})
    return {"generated_at": utcnow(), "scope": "Static files only; no RimWorld game test is performed.", "release_gates": release, "mods": reports, "error_count": sum(len(x["errors"]) for x in reports)}


def registry(root=ROOT):
    root = Path(root)
    records = []
    for path, manifest in manifests(root):
        item = dict(manifest)
        item["manifest"] = path.relative_to(root).as_posix()
        records.append(item)
    static = [m.get("inventory", {}).get("local_static_audit", {}) for m in records]
    return {"schema_version": 1, "generated_at": utcnow(), "mods": records, "counts": {
        "translations": len(records),
        "technically_checked": sum(m.get("qa", {}).get("technical") == "passed" for m in records),
        "game_tested": sum(m.get("qa", {}).get("in_game") == "passed" for m in records),
        "github_metadata_records": sum(bool(m.get("publication", {}).get("github_url")) for m in records),
        "github_published": sum(bool(m.get("publication", {}).get("github_url")) and m.get("publication", {}).get("github_status") in ("translation_published", "published") and (root / "mods" / m["package_id"] / "payload").is_dir() for m in records),
        "workshop_published": sum(bool(m.get("publication", {}).get("workshop_url")) for m in records),
        "pull_requests": sum(bool(m.get("integration", {}).get("pr_url")) for m in records),
        "accepted": sum(m.get("integration", {}).get("status") == "accepted" for m in records),
        "awaiting_rights": sum(not confirmed_rights(m, "translation") for m in records),
        "needs_update": sum(m.get("qa", {}).get("update_required") is True or "source_snapshot_drift" in m.get("inventory", {}).get("local_static_audit", {}).get("issue_kinds", []) for m in records),
        "freshness_unverified": sum(m.get("qa", {}).get("source_current") is not True for m in records),
        "static_inventory_pass": sum(x.get("status") == "no_detected_issues" for x in static),
        "static_inventory_flagged": sum(bool(x.get("issue_kinds") or x.get("issues")) for x in static),
        "static_findings": sum(x.get("issue_count", sum(i.get("count", 1) for i in x.get("issues", []))) for x in static),
        "repository_monitors": sum(bool(m.get("monitor", {}).get("github_tree")) for m in records),
        "pull_request_monitors": sum(bool(m.get("integration", {}).get("pr_url")) for m in records),
        "icon_permission_requests": sum(m.get("rights", {}).get("icon", {}).get("permission_requested") is True for m in records),
    }}


def status_markdown(reg):
    counts = reg["counts"]
    lines = ["# PROJECT_STATUS", "", "Generated from `mods/*/manifest.json` by `python scripts/rwtranslations.py registry`.", "", f"Last inventory generation (UTC): {reg['generated_at']}", "", "| Metric | Count |", "|---|---:|"]
    lines.extend(f"| {key} | {value} |" for key, value in counts.items())
    lines += ["", "Static QA and in-game testing are separate states. Static inventory findings include changed inputs and stale field evidence; they are not a count of broken translations. Freshness unverified does not mean a confirmed upstream change. A manifest is an inventory record; pending rights or QA prevents staging a release.", "", "| Translation | Technical QA | Game test | Integration | Workshop |", "|---|---|---|---|---|"]
    for mod in reg["mods"]:
        qa = mod.get("qa", {})
        name = mod.get("name", mod["package_id"]).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| [{name}]({mod['manifest']}) | {qa.get('technical', 'pending')} | {qa.get('in_game', 'not_tested')} | {mod.get('integration', {}).get('status', 'not_sent')} | {mod.get('publication', {}).get('workshop_url') or 'unpublished'} |")
    return "\n".join(lines) + "\n"


def prepare_update(folder, language_directory, output):
    """Write a private review queue; never edit reviewed Russian or its baseline."""
    folder = Path(folder)
    before = read_json(folder / "source.snapshot.json")["strings"]
    rows, errors = extract_language(language_directory)
    if errors:
        raise ValueError("; ".join(errors))
    after = hashes(rows)
    changes = delta(before, after)
    russian, ru_errors = extract_language(folder / "payload" / "Languages" / "Russian")
    queue = [{"key": key, "source": rows[key], "previous_translation": russian.get(key), "proposed_translation": None, "status": "needs_translation" if key in changes["added"] else "source_changed_needs_review"} for key in changes["added"] + changes["changed"]]
    write_json(output, {"generated_at": utcnow(), "delta": changes, "queue": queue, "removed_translation_keys": [key for key in changes["removed"] if key in russian], "existing_translation_errors": ru_errors, "translations_modified": False, "publication_allowed": False})
    return changes


class NoUnsafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected and urllib.parse.urlsplit(newurl).hostname != "api.github.com":
            redirected.remove_header("Authorization")
        return redirected


def check_url(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ("raw.githubusercontent.com", "api.github.com") or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("Monitor URLs must be HTTPS on raw.githubusercontent.com or api.github.com")


def fetch_bytes(url):
    check_url(url)
    opener = urllib.request.build_opener(NoUnsafeRedirect())
    headers = {"User-Agent": "RimWorld-Russian-Translations-source-monitor"}
    token = os.environ.get("GITHUB_TOKEN")
    if urllib.parse.urlsplit(url).hostname == "api.github.com" and token:
        headers["Authorization"] = "Bearer " + token
    with opener.open(urllib.request.Request(url, headers=headers), timeout=25) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Monitor response too large")
    return data


def fetch_json(url):
    data = fetch_bytes(url)
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("Remote source snapshot must be a JSON object")
    strings = value.get("strings", value)
    if not isinstance(strings, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in strings.items()):
        raise ValueError("Remote source snapshot must map keys to string hashes")
    return strings


def fetch_language_files(files):
    rows = {}
    for item in files:
        data = fetch_bytes(item["url"])
        kind = item.get("kind", "Keyed")
        if kind == "Strings":
            path = item.get("path", "").replace("\\", "/")
            if path.startswith("Strings/"):
                path = path[len("Strings/"):]
            if not path or Path(path).is_absolute() or ":" in path or ".." in Path(path).parts:
                raise ValueError("Strings monitoring requires a safe relative path")
            incoming = {f"Strings|{path}|{index}": line for index, line in enumerate(data.decode("utf-8-sig").splitlines())}
        else:
            doc = parse_xml(data)
            if doc.tag != "LanguageData" or kind not in ("Keyed", "DefInjected"):
                raise ValueError("Only Keyed/DefInjected LanguageData or Strings are supported")
            prefix = "Keyed|" if kind == "Keyed" else f"DefInjected|{item['def_type']}|"
            incoming = {}
            for node in doc:
                if list(node) or prefix + node.tag in incoming:
                    raise ValueError("Malformed/duplicate source language key")
                incoming[prefix + node.tag] = node.text or ""
        if rows.keys() & incoming.keys():
            raise ValueError("Duplicate source key across monitored files")
        rows.update(incoming)
    return hashes(rows)


def fetch_github_tree(repository, ref):
    if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("GitHub repository must be owner/name")
    if not isinstance(ref, str) or not ref or len(ref) > 250 or any(ord(x) < 32 for x in ref):
        raise ValueError("A known upstream branch/tag/ref is required")
    url = f"https://api.github.com/repos/{repository}/git/trees/{urllib.parse.quote(ref, safe='')}?recursive=1"
    tree = json.loads(fetch_bytes(url))
    if tree.get("truncated"):
        raise ValueError("GitHub returned a truncated tree; no complete comparison is possible")
    if not isinstance(tree.get("tree"), list) or not tree.get("sha"):
        raise ValueError("Unexpected GitHub tree result")
    files = {}
    for entry in tree["tree"]:
        if entry.get("type") not in ("blob", "commit"):
            continue
        path, sha = entry.get("path"), entry.get("sha")
        if not isinstance(path, str) or path.startswith("/") or ".." in path.split("/") or not re.fullmatch(r"[0-9a-f]{40,64}", str(sha)):
            raise ValueError("Malformed GitHub tree entry")
        if path in files:
            raise ValueError("Duplicate GitHub tree path")
        files[path] = sha
    return {"schema_version": 1, "generated_at": utcnow(), "repository": repository, "ref": ref, "tree_sha": tree["sha"], "scope": "Whole repository: Git blob/gitlink object IDs only; no original file content.", "files": dict(sorted(files.items()))}


def check_file_tree(folder, mod, cache):
    config = mod.get("monitor", {}).get("github_tree")
    if not config:
        return None
    try:
        repository, ref = config["repository"], config["ref"]
        baseline_name = config.get("baseline_file", "source.tree.json")
        baseline_path = within(Path(folder) / baseline_name, folder)
        before = read_json(baseline_path)
        if before.get("repository") != repository or before.get("ref") != ref or not isinstance(before.get("files"), dict):
            raise ValueError("Tree baseline repository/ref/scope does not match configured monitor")
        key = (repository, ref)
        if key not in cache:
            cache[key] = fetch_github_tree(repository, ref)
        after = cache[key]
        changes = delta(before["files"], after["files"])
        return {"package_id": mod["package_id"], "repository": repository, "ref": ref, "status": "changed_files" if any(changes.values()) else "unchanged", "delta": changes, "tree_sha": after["tree_sha"], "scope": "File-level repository change detection; does not imply changed translation keys or broken Russian text."}
    except Exception as ex:
        return {"package_id": mod["package_id"], "status": "error", "error": str(ex), "scope": "GitHub repository tree monitor"}


def check_integration(mod):
    integration = mod.get("integration", {})
    url = integration.get("pr_url")
    if not url:
        return None
    match = re.fullmatch(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/pull/([0-9]+)/?", url)
    if not match:
        return {"package_id": mod["package_id"], "status": "error", "action_required": True, "error": "Only public github.com pull request URLs can be monitored"}
    owner, repo, number = match.groups()
    api = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    try:
        pr = json.loads(fetch_bytes(api))
        if pr.get("merged_at"):
            status = "accepted"
        elif pr.get("state") == "closed":
            status = "closed_unmerged"
        elif pr.get("state") == "open":
            decisive = {}
            for page in range(1, 11):
                batch = json.loads(fetch_bytes(api + f"/reviews?per_page=100&page={page}"))
                if not isinstance(batch, list):
                    raise ValueError("Unexpected review API result")
                for review in batch:
                    if review.get("state") in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
                        decisive[review.get("user", {}).get("login", str(review.get("id")))] = review["state"]
                if len(batch) < 100:
                    break
            else:
                raise ValueError("More than 1000 reviews; manual status review needed")
            status = "changes_requested" if "CHANGES_REQUESTED" in decisive.values() else "open"
        else:
            raise ValueError("Unexpected pull request state")
        action_required = status in ("accepted", "closed_unmerged", "changes_requested") and integration.get("status") != status
        return {"package_id": mod["package_id"], "pr_url": url, "status": status, "recorded_status": integration.get("status"), "action_required": action_required, "head_sha": pr.get("head", {}).get("sha"), "merged_at": pr.get("merged_at")}
    except Exception as ex:
        return {"package_id": mod["package_id"], "pr_url": url, "status": "error", "action_required": True, "error": str(ex)}


def monitor(root=ROOT):
    reports, integrations, file_monitors, tree_cache = [], [], [], {}
    for path, mod in manifests(root):
        file_report = check_file_tree(path.parent, mod, tree_cache)
        if file_report:
            file_monitors.append(file_report)
        integration = check_integration(mod)
        if integration:
            integrations.append(integration)
        config = mod.get("monitor", {})
        url = config.get("snapshot_url")
        files = config.get("files", [])
        baseline = path.parent / "source.snapshot.json"
        if not url and not files:
            reports.append({"package_id": mod["package_id"], "status": "not_configured"})
            continue
        try:
            if not baseline.is_file():
                raise ValueError("source baseline is missing")
            before = read_json(baseline).get("strings", {})
            if url and files:
                raise ValueError("Configure either snapshot_url or files, not both")
            after = fetch_json(url) if url else fetch_language_files(files)
            changes = delta(before, after)
            reports.append({"package_id": mod["package_id"], "status": "changed" if any(changes.values()) else "unchanged", "delta": changes, "source_urls": [url] if url else [x["url"] for x in files]})
        except Exception as ex:
            reports.append({"package_id": mod["package_id"], "status": "error", "error": str(ex)})
    meaningful = [r for r in reports if r["status"] in ("changed", "error")] + [r for r in integrations if r["action_required"]] + [r for r in file_monitors if r["status"] in ("changed_files", "error")]
    # No generated timestamp in fingerprint: unchanged reports never churn issues.
    fingerprint = hashlib.sha256(json.dumps(meaningful, sort_keys=True).encode()).hexdigest()
    return {"generated_at": utcnow(), "fingerprint": fingerprint, "action_required": bool(meaningful), "scope": "Configured source endpoints, GitHub repository file trees and recorded public upstream PRs; no Workshop login/download, C# literal extraction or auto-translation. File-level changes do not prove translation-key changes. Observations do not alter manifests.", "mods": reports, "integrations": integrations, "file_monitors": file_monitors}


def stage(root, package, output):
    selected = [(path, obj) for path, obj in manifests(root) if obj["package_id"] == package]
    if len(selected) != 1:
        raise ValueError("Exactly one known package_id must be selected")
    path, mod = selected[0]
    errors = metadata_errors(mod) + validate_payload(path.parent, mod, release=True)[0]
    if errors:
        raise ValueError("Release blocked: " + "; ".join(errors))
    destination = within(Path(output) / package, Path(output))
    if destination.exists():
        raise ValueError("Destination exists; choose a fresh staging directory")
    # Copy only after the whole payload has passed the allowlist and symlink checks.
    shutil.copytree(path.parent / "payload", destination)
    write_json(destination.parent / (package + ".release.json"), {"package_id": package, "staged_at": utcnow(), "qa": mod["qa"], "rights": mod["rights"], "files": file_hashes(destination), "steam_upload": "manual authenticated Steam client upload; no upload has occurred"})
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("registry")
    validate = sub.add_parser("validate")
    validate.add_argument("--release", action="store_true")
    validate.add_argument("--output", type=Path, default=Path("reports/validation.json"))
    snap = sub.add_parser("snapshot")
    snap.add_argument("language_directory", type=Path)
    snap.add_argument("output", type=Path)
    tree_snapshot = sub.add_parser("tree-snapshot")
    tree_snapshot.add_argument("repository")
    tree_snapshot.add_argument("ref")
    tree_snapshot.add_argument("output", type=Path)
    diff = sub.add_parser("diff")
    diff.add_argument("before", type=Path)
    diff.add_argument("after", type=Path)
    diff.add_argument("output", type=Path)
    update = sub.add_parser("prepare-update")
    update.add_argument("package_id")
    update.add_argument("language_directory", type=Path)
    update.add_argument("--output", type=Path)
    check = sub.add_parser("monitor")
    check.add_argument("--output", type=Path, default=Path("reports/source-monitor.json"))
    package = sub.add_parser("stage")
    package.add_argument("package_id")
    package.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == "registry":
        reg = registry(root)
        write_json(root / "registry.json", reg)
        (root / "PROJECT_STATUS.md").write_text(status_markdown(reg), encoding="utf-8")
        print(json.dumps(reg["counts"]))
    elif args.command == "validate":
        report = audit(root, args.release)
        write_json(args.output if args.output.is_absolute() else root / args.output, report)
        print(f"{len(report['mods'])} manifests; {report['error_count']} errors; game testing not performed")
        return bool(report["error_count"])
    elif args.command == "snapshot":
        rows, errors = extract_language(args.language_directory)
        if errors:
            raise ValueError("; ".join(errors))
        write_json(args.output, {"schema_version": 1, "generated_at": utcnow(), "scope": "language files only; hashes and token/tag signatures, no complete source text", "strings": hashes(rows), "signatures": signatures(rows)})
    elif args.command == "tree-snapshot":
        result = fetch_github_tree(args.repository, args.ref)
        write_json(args.output, result)
        print(f"{len(result['files'])} upstream file hashes; no original file content copied")
    elif args.command == "diff":
        change = delta(read_json(args.before)["strings"], read_json(args.after)["strings"])
        write_json(args.output, {"generated_at": utcnow(), "delta": change, "review_required": any(change.values()), "translations_modified": False})
        print(json.dumps({k: len(v) for k, v in change.items()}))
    elif args.command == "monitor":
        result = monitor(root)
        write_json(args.output if args.output.is_absolute() else root / args.output, result)
        print(f"String sources: {sum(x['status'] != 'not_configured' for x in result['mods'])}; file trees: {len(result['file_monitors'])}; PRs: {len(result['integrations'])}; action required: {result['action_required']}")
    elif args.command == "prepare-update":
        if not PACKAGE_ID.fullmatch(args.package_id):
            raise ValueError("Invalid package_id")
        folder = within(root / "mods" / args.package_id, root / "mods")
        output = args.output or root / "reports" / "pending" / (args.package_id + ".json")
        print(json.dumps({key: len(value) for key, value in prepare_update(folder, args.language_directory, output).items()}))
    elif args.command == "stage":
        print(stage(root, args.package_id, args.output if args.output.is_absolute() else root / args.output))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, json.JSONDecodeError) as ex:
        print(f"ERROR: {ex}", file=sys.stderr)
        sys.exit(2)
