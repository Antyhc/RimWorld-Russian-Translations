import importlib.util
import json
from pathlib import Path
import shutil
import uuid
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("rwtranslations", Path(__file__).resolve().parents[1] / "scripts" / "rwtranslations.py")
rw = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rw)


class ProjectTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parents[1] / ".tests-tmp"
        parent.mkdir(exist_ok=True)
        # On managed Windows sandboxes tempfile's 0700 ACL can deny the sandbox
        # identity access. Normal mkdir inherits the workspace ACL instead.
        self.root = (parent / ("case-" + uuid.uuid4().hex)).resolve()
        self.root.mkdir()
        self.assertTrue(self.root.is_relative_to(parent.resolve()))
        self.folder = self.root / "mods" / "author.mod"
        self.folder.mkdir(parents=True)
        self.mod = {
            "schema_version": 1, "package_id": "author.mod", "name": "Example",
            "translation_package_id": "translations.author.mod.ru",
            "original": {"supported_versions": ["1.7"], "workshop_id": "1234"},
            "supported_versions": ["1.7"],
            "rights": {"translation": {"status": "confirmed", "license": "MIT", "evidence": "https://example.org/license", "attribution": "Original author and Russian translator"}, "icon": {"status": "unknown"}},
            "qa": {"technical": "passed", "linguistic": "ai_reviewed", "source_current": True, "checked_at": rw.utcnow(), "source_checked_at": rw.utcnow(), "evidence": "qa/report.json", "in_game": "not_tested"},
            "duplicate_translation": {"status": "checked_no_current_equivalent"}
        }
        self.payload = self.folder / "payload"
        (self.payload / "About").mkdir(parents=True)
        (self.payload / "About" / "About.xml").write_text("<ModMetaData><name>Example Russian</name><packageId>translations.author.mod.ru</packageId><supportedVersions><li>1.7</li></supportedVersions><modDependencies><li><packageId>author.mod</packageId></li></modDependencies><loadAfter><li>author.mod</li></loadAfter></ModMetaData>", encoding="utf-8")
        (self.payload / "About" / "License.txt").write_text("Example license text", encoding="utf-8")
        self.mod["rights"]["translation"]["required_notice_files"] = {"About/License.txt": rw.hashlib.sha256((self.payload / "About" / "License.txt").read_bytes()).hexdigest()}
        self.ru = self.payload / "Languages" / "Russian" / "Keyed"
        self.ru.mkdir(parents=True)
        (self.ru / "Main.xml").write_text("<LanguageData><Greeting>Привет, {0}!</Greeting></LanguageData>", encoding="utf-8")
        rw.write_json(self.folder / "source.snapshot.json", {"strings": rw.hashes({"Keyed|Greeting": "Hello, {0}!"}), "texts": {"Keyed|Greeting": "Hello, {0}!"}})
        self.mod["qa"]["payload_sha256"] = rw.payload_digest(self.payload)
        self.mod["qa"]["source_snapshot_sha256"] = rw.hashlib.sha256((self.folder / "source.snapshot.json").read_bytes()).hexdigest()
        self.save()

    def save(self):
        rw.write_json(self.folder / "manifest.json", self.mod)

    def tearDown(self):
        # Recursive cleanup target is verified against this test's private root.
        self.assertTrue(self.root.resolve().is_relative_to(Path(__file__).resolve().parents[1] / ".tests-tmp"))
        shutil.rmtree(self.root)

    def test_release_fixture_can_stage_without_claiming_game_test(self):
        output = rw.stage(self.root, "author.mod", self.root / "dist")
        report = rw.read_json(output.parent / "author.mod.release.json")
        self.assertEqual(report["qa"]["in_game"], "not_tested")
        self.assertIn("About/About.xml", report["files"])

    def test_pending_rights_blocks_release(self):
        self.mod["rights"]["translation"]["status"] = "unknown"
        self.save()
        with self.assertRaisesRegex(ValueError, "translation_rights_unconfirmed"):
            rw.stage(self.root, "author.mod", self.root / "dist")

    def test_steam_submission_does_not_claim_public_page_access(self):
        self.mod["publication"] = {"workshop_id": "12345", "workshop_url": "https://steamcommunity.com/sharedfiles/filedetails/?id=12345", "workshop_status": "submitted_public_automatic_content_check", "anonymous_page_verified": False}
        self.save()
        counts = rw.registry(self.root)["counts"]
        self.assertEqual(counts["workshop_submitted"], 1)
        self.assertEqual(counts["workshop_published"], 0)
        self.assertEqual(counts["workshop_content_check_pending"], 1)
        self.mod["publication"].update(workshop_status="published", anonymous_page_verified=True)
        self.save()
        counts = rw.registry(self.root)["counts"]
        self.assertEqual(counts["workshop_published"], 1)
        self.assertEqual(counts["workshop_content_check_pending"], 0)

    def test_missing_attribution_blocks_release(self):
        del self.mod["rights"]["translation"]["attribution"]
        self.assertIn("translation_rights_unconfirmed", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_binary_is_forbidden_even_with_approved_manifest(self):
        (self.payload / "Original.dll").write_bytes(b"MZ")
        self.assertIn("forbidden_payload_file:Original.dll", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_unlicensed_preview_forbidden(self):
        (self.payload / "About" / "Preview.png").write_bytes(b"image")
        self.assertIn("forbidden_payload_file:About/Preview.png", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_original_id_must_be_different(self):
        self.mod["translation_package_id"] = "AUTHOR.MOD"
        self.assertIn("translation_package_id_invalid", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_unknown_source_blocks_release(self):
        self.mod["qa"]["source_current"] = None
        self.assertIn("source_not_current", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_duplicate_check_required(self):
        self.mod["duplicate_translation"]["status"] = "unknown"
        self.assertIn("existing_translation_check_pending", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_duplicate_key_across_files_detected(self):
        (self.ru / "Duplicate.xml").write_text("<LanguageData><Greeting>Дубликат</Greeting></LanguageData>", encoding="utf-8")
        self.assertIn("duplicate_key:Keyed|Greeting", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_placeholder_damage_detected(self):
        (self.ru / "Main.xml").write_text("<LanguageData><Greeting>Привет!</Greeting></LanguageData>", encoding="utf-8")
        self.assertIn("placeholder_mismatch:Keyed|Greeting", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_formatting_damage_detected(self):
        self.assertEqual(rw.compare_tokens("<color=red>{0}</color>", "<color=blue>{0}</color>"), ["format_tag_mismatch"])

    def test_placeholder_reordering_permitted(self):
        self.assertEqual(rw.compare_tokens("{0} greets {1}", "{1} приветствует {0}"), [])

    def test_token_multiplicity_is_preserved(self):
        self.assertEqual(rw.compare_tokens("{0} and {0}", "{0} и {1}"), ["placeholder_mismatch"])

    def test_dtd_blocked(self):
        with self.assertRaisesRegex(ValueError, "DTD/entities"):
            rw.parse_xml(b'<!DOCTYPE x [<!ENTITY a "bad">]><LanguageData><x>&a;</x></LanguageData>')

    def test_traversal_blocked(self):
        with self.assertRaisesRegex(ValueError, "escapes"):
            rw.within(self.root / ".." / "private", self.root)

    def test_manifest_directory_must_match_id(self):
        self.mod["package_id"] = "another.mod"
        self.save()
        with self.assertRaisesRegex(ValueError, "directory must equal"):
            list(rw.manifests(self.root))

    def test_unknown_package_rejected(self):
        with self.assertRaisesRegex(ValueError, "Exactly one"):
            rw.stage(self.root, "../private", self.root / "dist")

    def test_pending_inventory_allowed_but_not_release(self):
        pending = self.root / "mods" / "pending.mod"
        pending.mkdir()
        rw.write_json(pending / "manifest.json", {"schema_version": 1, "package_id": "pending.mod", "name": "Pending"})
        report = rw.audit(self.root)
        item = next(x for x in report["mods"] if x["package_id"] == "pending.mod")
        self.assertEqual(item["errors"], [])
        self.assertIn("payload_missing", item["warnings"])
        release = rw.audit(self.root, release=True)
        self.assertGreater(release["error_count"], 0)

    def test_delta_detects_three_change_types(self):
        self.assertEqual(rw.delta({"a": "1", "b": "2", "gone": "3"}, {"a": "1", "b": "4", "new": "5"}), {"added": ["new"], "changed": ["b"], "removed": ["gone"]})

    def test_prepare_update_preserves_existing_russian(self):
        english = self.root / "English" / "Keyed"
        english.mkdir(parents=True)
        (english / "Main.xml").write_text("<LanguageData><Greeting>New {0}!</Greeting><NewKey>New string</NewKey></LanguageData>", encoding="utf-8")
        before = (self.ru / "Main.xml").read_bytes()
        destination = self.root / "reports" / "queue.json"
        rw.prepare_update(self.folder, english.parent, destination)
        result = rw.read_json(destination)
        self.assertEqual((self.ru / "Main.xml").read_bytes(), before)
        self.assertEqual(result["queue"][1]["previous_translation"], "Привет, {0}!")
        self.assertFalse(result["publication_allowed"])

    def test_monitor_fingerprint_stable_without_changes(self):
        self.mod["monitor"] = {"snapshot_url": "https://raw.githubusercontent.com/example/repo/main/snapshot.json"}
        self.save()
        with patch.object(rw, "fetch_json", return_value=rw.read_json(self.folder / "source.snapshot.json")["strings"]):
            first, second = rw.monitor(self.root), rw.monitor(self.root)
        self.assertFalse(first["action_required"])
        self.assertEqual(first["fingerprint"], second["fingerprint"])

    def test_monitor_network_allowlist(self):
        for url in ("http://raw.githubusercontent.com/x", "https://127.0.0.1/", "https://github.com@evil.example/", "https://raw.githubusercontent.com.evil.example/x"):
            with self.assertRaises(ValueError):
                rw.check_url(url)

    def test_stage_never_overwrites_existing_release(self):
        rw.stage(self.root, "author.mod", self.root / "dist")
        with self.assertRaisesRegex(ValueError, "Destination exists"):
            rw.stage(self.root, "author.mod", self.root / "dist")

    def test_auto_discovery_needs_no_code_change(self):
        other = self.root / "mods" / "new.package"
        other.mkdir()
        rw.write_json(other / "manifest.json", {"schema_version": 1, "package_id": "new.package", "name": "New"})
        self.assertEqual(rw.registry(self.root)["counts"]["translations"], 2)

    def test_hash_only_snapshot_cannot_bypass_placeholder_checks(self):
        rw.write_json(self.folder / "source.snapshot.json", {"strings": rw.hashes({"Keyed|Greeting": "Hello, {0}!"})})
        self.assertIn("source_signature_missing_or_unbound:Keyed|Greeting", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_signature_snapshot_validates_without_full_source_text(self):
        rows = {"Keyed|Greeting": "Hello, {0}!"}
        rw.write_json(self.folder / "source.snapshot.json", {"strings": rw.hashes(rows), "signatures": rw.signatures(rows)})
        self.mod["qa"]["source_snapshot_sha256"] = rw.hashlib.sha256((self.folder / "source.snapshot.json").read_bytes()).hexdigest()
        self.assertEqual(rw.validate_payload(self.folder, self.mod, True)[0], [])

    def test_stale_source_blocks_release(self):
        self.mod["qa"]["source_checked_at"] = "2020-01-01T00:00:00Z"
        self.assertIn("source_check_stale_or_undated", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_qa_is_bound_to_payload_bytes(self):
        (self.ru / "Main.xml").write_text("<LanguageData><Greeting>Здравствуйте, {0}!</Greeting></LanguageData>", encoding="utf-8")
        self.assertIn("qa_payload_digest_mismatch", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_unknown_source_key_blocks_release(self):
        (self.ru / "Other.xml").write_text("<LanguageData><Unverified>Новая строка</Unverified></LanguageData>", encoding="utf-8")
        self.assertIn("source_signature_missing_or_unbound:Keyed|Unverified", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_utf16_dtd_bypass_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            rw.parse_xml('<!DOCTYPE x [<!ENTITY a "bad">]><LanguageData><x>&a;</x></LanguageData>'.encode("utf-16"))

    def test_loadfolders_outside_fixed_root_layout_forbidden(self):
        (self.payload / "loadFolders.xml").write_text("<loadFolders><v1.7><li>../other</li></v1.7></loadFolders>", encoding="utf-8")
        self.assertIn("forbidden_payload_file:loadFolders.xml", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_crossed_tags_with_equal_multiset_rejected(self):
        source = "<b><i>word</i></b>"
        translated = "<b><i>слово</b></i>"
        self.assertEqual(rw.compare_tokens(source, translated), ["format_tags_unbalanced"])

    def test_literal_control_escapes_preserved(self):
        self.assertIn("placeholder_mismatch", rw.compare_tokens(r"line\nnext", "строка далее"))

    def test_empty_translation_rejected(self):
        (self.ru / "Main.xml").write_text("<LanguageData><Greeting>   </Greeting></LanguageData>", encoding="utf-8")
        self.assertIn("empty_translation:Keyed|Greeting", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_translation_package_id_strict(self):
        for identifier in ("noDot", "bad.hyphen-id", "bad.under_score", "long." + "a" * 60):
            self.mod["translation_package_id"] = identifier
            self.assertIn("translation_package_id_invalid", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_strings_key_relative_to_strings_directory(self):
        strings = self.payload / "Languages" / "Russian" / "Strings"
        strings.mkdir()
        (strings / "Names.txt").write_text("Первая\n\nТретья\n", encoding="utf-8")
        rows, errors = rw.extract_language(strings.parent)
        self.assertEqual(errors, [])
        self.assertEqual(rows["Strings|Names.txt|1"], "")
        self.assertNotIn("Strings|Strings/Names.txt|0", rows)

    def test_icon_rights_must_bind_actual_image(self):
        (self.payload / "About" / "Preview.png").write_bytes(b"fake")
        self.mod["rights"]["icon"] = {"status": "confirmed", "license": "MIT", "evidence": "permission", "attribution": "Artist"}
        self.assertIn("icon_source_or_preview_hash_unbound", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_required_license_notice_must_not_disappear(self):
        (self.payload / "About" / "License.txt").unlink()
        self.assertIn("required_notice_missing_or_changed:About/License.txt", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_notice_map_cannot_copy_other_assets(self):
        self.mod["rights"]["translation"]["required_notice_files"] = {"Original.dll": "ignored"}
        self.assertIn("required_notice_path_not_allowed:Original.dll", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_pr_merge_detected_without_mutating_manifest(self):
        self.mod["integration"] = {"pr_url": "https://github.com/author/mod/pull/7", "status": "pr_sent"}
        before = json.dumps(self.mod, sort_keys=True)
        with patch.object(rw, "fetch_bytes", return_value=b'{"state":"closed","merged_at":"2026-10-28T00:00:00Z","head":{"sha":"abc"}}'):
            result = rw.check_integration(self.mod)
        self.assertEqual(result["status"], "accepted")
        self.assertTrue(result["action_required"])
        self.assertEqual(json.dumps(self.mod, sort_keys=True), before)

    def test_pr_review_changes_requested_observed(self):
        self.mod["integration"] = {"pr_url": "https://github.com/author/mod/pull/7", "status": "pr_sent"}
        responses = [b'{"state":"open","merged_at":null}', b'[{"state":"CHANGES_REQUESTED","user":{"login":"maintainer"}}]']
        with patch.object(rw, "fetch_bytes", side_effect=responses):
            result = rw.check_integration(self.mod)
        self.assertEqual(result["status"], "changes_requested")

    def test_closed_unmerged_pr_is_not_claimed_rejected(self):
        self.mod["integration"] = {"pr_url": "https://github.com/author/mod/pull/7", "status": "pr_sent"}
        with patch.object(rw, "fetch_bytes", return_value=b'{"state":"closed","merged_at":null}'):
            result = rw.check_integration(self.mod)
        self.assertEqual(result["status"], "closed_unmerged")

    def test_acknowledged_pr_merge_does_not_repeat_alert(self):
        self.mod["integration"] = {"pr_url": "https://github.com/author/mod/pull/7", "status": "accepted"}
        with patch.object(rw, "fetch_bytes", return_value=b'{"state":"closed","merged_at":"2026-10-28T00:00:00Z"}'):
            result = rw.check_integration(self.mod)
        self.assertFalse(result["action_required"])

    def test_redirect_never_sends_api_token_to_raw_content(self):
        request = rw.urllib.request.Request("https://api.github.com/repos/author/mod", headers={"Authorization": "Bearer never-write-real-token"})
        redirected = rw.NoUnsafeRedirect().redirect_request(request, None, 302, "Found", {}, "https://raw.githubusercontent.com/author/mod/main/file")
        self.assertFalse(redirected.has_header("Authorization"))

    def test_tree_monitor_detects_new_changed_removed_files(self):
        self.mod["monitor"] = {"github_tree": {"repository": "author/mod", "ref": "main", "baseline_file": "source.tree.json"}}
        rw.write_json(self.folder / "source.tree.json", {"repository": "author/mod", "ref": "main", "files": {"translation.txt": "1" * 40, "Old.xml": "2" * 40}})
        upstream = {"tree_sha": "3" * 40, "files": {"translation.txt": "4" * 40, "New.xml": "5" * 40}}
        with patch.object(rw, "fetch_github_tree", return_value=upstream):
            result = rw.check_file_tree(self.folder, self.mod, {})
        self.assertEqual(result["status"], "changed_files")
        self.assertEqual(result["delta"], {"added": ["New.xml"], "changed": ["translation.txt"], "removed": ["Old.xml"]})

    def test_tree_monitor_baseline_cannot_escape_mod_directory(self):
        self.mod["monitor"] = {"github_tree": {"repository": "author/mod", "ref": "main", "baseline_file": "../../private.json"}}
        result = rw.check_file_tree(self.folder, self.mod, {})
        self.assertEqual(result["status"], "error")
        self.assertIn("escapes", result["error"])

    def test_tree_monitor_rejects_wrong_repository_baseline(self):
        self.mod["monitor"] = {"github_tree": {"repository": "author/mod", "ref": "main"}}
        rw.write_json(self.folder / "source.tree.json", {"repository": "other/mod", "ref": "main", "files": {}})
        result = rw.check_file_tree(self.folder, self.mod, {})
        self.assertEqual(result["status"], "error")

    def test_tree_fetch_rejects_truncated_inventory(self):
        with patch.object(rw, "fetch_bytes", return_value=b'{"sha":"123","truncated":true,"tree":[]}'):
            with self.assertRaisesRegex(ValueError, "truncated"):
                rw.fetch_github_tree("author/mod", "main")

    def test_tree_fetch_copies_hashes_without_original_content(self):
        body = json.dumps({"sha": "1" * 40, "tree": [{"type": "tree", "path": "Folder", "sha": "2" * 40}, {"type": "blob", "path": "Folder/Original.dll", "sha": "3" * 40}, {"type": "commit", "path": "Submodule", "sha": "4" * 40}]}).encode()
        with patch.object(rw, "fetch_bytes", return_value=body):
            result = rw.fetch_github_tree("author/mod", "main")
        self.assertEqual(result["files"], {"Folder/Original.dll": "3" * 40, "Submodule": "4" * 40})
        self.assertNotIn("content", result)

    def test_tree_monitor_reuses_fetch_for_shared_repository(self):
        self.mod["monitor"] = {"github_tree": {"repository": "author/mod", "ref": "main"}}
        rw.write_json(self.folder / "source.tree.json", {"repository": "author/mod", "ref": "main", "files": {"file": "1" * 40}})
        cache = {}
        with patch.object(rw, "fetch_github_tree", return_value={"tree_sha": "2" * 40, "files": {"file": "1" * 40}}) as mocked:
            first = rw.check_file_tree(self.folder, self.mod, cache)
            second = rw.check_file_tree(self.folder, self.mod, cache)
        self.assertEqual(first["status"], "unchanged")
        self.assertEqual(second["status"], "unchanged")
        self.assertEqual(mocked.call_count, 1)

    def test_saved_store_with_drafts_does_not_inflate_draft_only_count(self):
        self.mod["inventory"] = {"saved_translation_store": True, "draft_work": {"codex_tasks": 3}}
        self.save()
        for package, scope in (("author.draft", {"saved_translation_store": False, "draft_work": {"local_model_tasks": 2}}),
                               ("author.unknown", {"draft_work": {"codex_tasks": 1}})):
            rw.write_json(self.root / "mods" / package / "manifest.json", {**self.mod, "package_id": package, "inventory": scope})
        report = rw.registry(self.root)
        self.assertEqual(report["counts"]["saved_store_records"], 1)
        self.assertEqual(report["counts"]["draft_only_records"], 1)
        self.assertEqual(report["counts"]["store_scope_unverified"], 1)
        with patch.object(rw, "ROOT", self.root):
            status = rw.status_markdown(report)
        self.assertIn("1 saved-store records and 1 additional draft/review metadata records", status)
        self.assertIn("1 records have unverified store scope", status)


if __name__ == "__main__":
    unittest.main()
