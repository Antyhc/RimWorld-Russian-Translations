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

    def test_one_community_pr_covering_two_mods_is_one_pr_and_two_records(self):
        self.mod["integration"] = {"status": "open", "pr_url": "https://github.com/community/translations/pull/47"}
        self.save()
        other = dict(self.mod, package_id="author.second", translation_package_id="translations.author.second.ru")
        other["integration"] = dict(self.mod["integration"], pr_url=self.mod["integration"]["pr_url"] + "/")
        rw.write_json(self.root / "mods/author.second/manifest.json", other)
        counts = rw.registry(self.root)["counts"]
        self.assertEqual(counts["translations"], 2)
        self.assertEqual(counts["pull_requests"], 1)
        self.assertEqual(counts["pull_request_monitors"], 1)
        self.assertEqual(counts["integration_records"], 2)

    def test_shared_pr_fetches_one_consistent_snapshot_for_multiple_mod_records(self):
        self.mod["integration"] = {"status": "open", "pr_url": "https://github.com/community/translations/pull/47", "target_kind": "community_translation"}
        other = dict(self.mod, package_id="author.second")
        cache = {}
        pr = {"state": "open", "merged_at": None, "head": {"sha": "current"}}
        with patch.object(rw, "fetch_bytes", side_effect=lambda url: json.dumps([] if "/reviews?" in url else pr).encode()) as fetch:
            first = rw.check_integration(self.mod, cache)
            second = rw.check_integration(other, cache)
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual((first["package_id"], second["package_id"]), ("author.mod", "author.second"))
        self.assertEqual((first["status"], second["status"]), ("open", "open"))

    def test_status_counts_minimal_readback_without_claiming_subscribed_ui_test(self):
        self.mod["qa"].update(in_game="passed", game_evidence="game-test-evidence.json")
        self.save()
        rw.write_json(self.folder / "game-test-evidence.json", {
            "game_version": "1.7.4990", "russian_candidate_matches": 108,
            "interactive_visual_review_of_every_text": False,
            "baseline_localization_error_count": 52,
        })
        text = rw.status_markdown(rw.registry(self.root), self.root)
        self.assertIn("108 expected Russian values", text)
        self.assertNotIn("subscribed Workshop copies were also loaded", text)
        self.assertNotIn("settings windows were inspected", text)
        self.assertNotIn("nine Core localization errors", text)

    def test_current_private_profile_status_preserves_changed_assembly_holds(self):
        rw.write_json(self.root / "reports/reviewed-batches-fresh.json", {
            "local_model_review": {"private_runtime_test": {
                "current_full_profile_freshness": "current_inputs_verified_by_fresh_game_readback",
                "runtime_ui_handlers": {"applied": 96, "held_changed_dubsmintmenus_assembly": 2},
            }},
        })
        text = rw.status_markdown(rw.registry(self.root), self.root)
        self.assertIn("96 applied / 2 held", text)
        self.assertIn("assembly guard was preserved", text)
        self.assertNotIn("pending fresh validation", text)

    def test_revoked_context_overrides_the_older_current_game_receipt(self):
        rw.write_json(self.root / "reports/reviewed-batches-fresh.json", {
            "current_source_context_revalidated": False,
            "local_model_review": {"private_runtime_test": {
                "current_full_profile_freshness": "current_inputs_verified_by_fresh_game_readback",
            }},
        })
        text = rw.status_markdown(rw.registry(self.root), self.root)
        self.assertIn("results above are historical", text)
        self.assertIn("launcher blocks a full-profile rerun", text)
        self.assertNotIn("launcher now passes", text)

    def test_status_counts_generic_actual_game_evidence_values(self):
        self.mod["qa"].update(in_game="passed", game_evidence="game-test-evidence.json")
        self.save()
        rw.write_json(self.folder / "game-test-evidence.json", {
            "game_version": "1.7.4990", "values_verified": 21,
            "additional_localization_errors": 0, "gameplay_tested": False,
        })
        text = rw.status_markdown(rw.registry(self.root), self.root)
        self.assertIn("21 expected Russian values", text)
        self.assertNotIn("subscribed Workshop copies were also loaded", text)

    def test_binary_is_forbidden_even_with_approved_manifest(self):
        (self.payload / "Original.dll").write_bytes(b"MZ")
        self.assertIn("forbidden_payload_file:Original.dll", rw.validate_payload(self.folder, self.mod, True)[0])

    def conditional_fixture(self, key="Optional", value="Дополнение, {0}!"):
        roots = [{"path": "Conditional/another.mod", "if_mod_active": "another.mod", "source_relative_root": "1.7/Mods/Another"}]
        proof = self.folder / "source-layout-evidence.json"
        rw.write_json(proof, {"schema": 1, "package_id": "author.mod", "version": "1.7", "roots": roots})
        self.mod["conditional_languages"] = {"version": "1.7", "roots": roots,
            "evidence": proof.name, "evidence_sha256": rw.hashlib.sha256(proof.read_bytes()).hexdigest()}
        (self.payload / "LoadFolders.xml").write_text('<loadFolders><v1.7><li>/</li><li IfModActive="another.mod">Conditional/another.mod</li></v1.7></loadFolders>', "utf-8")
        directory = self.payload / "Conditional/another.mod/Languages/Russian/Keyed"
        directory.mkdir(parents=True)
        (directory / "Optional.xml").write_text(f"<LanguageData><{key}>{value}</{key}></LanguageData>", "utf-8")
        rw.write_json(self.folder / "source.snapshot.json", {"strings": rw.hashes({"Keyed|Greeting": "Hello, {0}!", "Keyed|Optional": "Extra, {0}!"}),
            "texts": {"Keyed|Greeting": "Hello, {0}!", "Keyed|Optional": "Extra, {0}!"}})
        self.mod["qa"]["payload_sha256"] = rw.payload_digest(self.payload)
        self.mod["qa"]["source_snapshot_sha256"] = rw.hashlib.sha256((self.folder / "source.snapshot.json").read_bytes()).hexdigest()
        self.save()
        return directory

    def test_conditional_language_stages_both_reviewed_roots_without_runtime_claim(self):
        self.conditional_fixture()
        errors, warnings, rows = rw.validate_payload(self.folder, self.mod, True)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(set(rows), {"Keyed|Greeting", "Keyed|Optional"})
        output = rw.stage(self.root, "author.mod", self.root / "dist")
        self.assertTrue((output / "LoadFolders.xml").is_file())
        self.assertTrue((output / "Conditional/another.mod/Languages/Russian/Keyed/Optional.xml").is_file())
        self.assertEqual(self.mod["qa"]["in_game"], "not_tested")

    def test_pure_conditional_pack_requires_a_valid_keyless_base_container(self):
        self.conditional_fixture()
        (self.ru / "Main.xml").unlink()
        snapshot = {"strings": rw.hashes({"Keyed|Optional": "Extra, {0}!"}), "texts": {"Keyed|Optional": "Extra, {0}!"}}
        rw.write_json(self.folder / "source.snapshot.json", snapshot)
        self.mod["qa"]["source_snapshot_sha256"] = rw.hashlib.sha256((self.folder / "source.snapshot.json").read_bytes()).hexdigest()
        self.mod["qa"]["payload_sha256"] = rw.payload_digest(self.payload)
        self.save()
        errors = rw.validate_payload(self.folder, self.mod, True)[0]
        self.assertIn("conditional_package_missing_unconditional_language_xml", errors)
        (self.ru / "ConditionalCompatibility.xml").write_text("<LanguageData/>", encoding="utf-8")
        self.mod["qa"]["payload_sha256"] = rw.payload_digest(self.payload)
        self.save()
        errors, _, rows = rw.validate_payload(self.folder, self.mod, True)
        self.assertEqual(errors, [])
        self.assertEqual(set(rows), {"Keyed|Optional"})

    def second_conditional_fixture(self, filename):
        self.conditional_fixture()
        layout = self.mod["conditional_languages"]
        layout["roots"].append({"path": "Conditional/second.mod", "if_mod_active": "second.mod", "source_relative_root": "1.7/Mods/Second"})
        proof = self.folder / layout["evidence"]
        rw.write_json(proof, {"schema": 1, "package_id": "author.mod", "version": "1.7", "roots": layout["roots"]})
        layout["evidence_sha256"] = rw.hashlib.sha256(proof.read_bytes()).hexdigest()
        (self.payload / "LoadFolders.xml").write_text('<loadFolders><v1.7><li>/</li><li IfModActive="another.mod">Conditional/another.mod</li><li IfModActive="second.mod">Conditional/second.mod</li></v1.7></loadFolders>', "utf-8")
        directory = self.payload / "Conditional/second.mod/Languages/Russian/Keyed"
        directory.mkdir(parents=True)
        (directory / filename).write_text("<LanguageData><Third>Другое, {0}!</Third></LanguageData>", "utf-8")
        texts = rw.read_json(self.folder / "source.snapshot.json")["texts"]
        texts["Keyed|Third"] = "Other, {0}!"
        rw.write_json(self.folder / "source.snapshot.json", {"strings": rw.hashes(texts), "texts": texts})
        self.mod["qa"]["payload_sha256"] = rw.payload_digest(self.payload)
        self.mod["qa"]["source_snapshot_sha256"] = rw.hashlib.sha256((self.folder / "source.snapshot.json").read_bytes()).hexdigest()
        self.save()
        return directory

    def test_disjoint_keys_do_not_allow_colliding_xml_paths_between_active_roots(self):
        directory = self.second_conditional_fixture("oPTIONAL.XML")
        for filename, relative in [("oPTIONAL.XML", "keyed/optional.xml"), ("mAIN.XML", "keyed/main.xml")]:
            with self.subTest(collision=relative):
                path = next(directory.glob("*.XML"))
                if path.name != filename:
                    path.rename(directory / filename)
                self.mod["qa"]["payload_sha256"] = rw.payload_digest(self.payload)
                self.save()
                errors, _, rows = rw.validate_payload(self.folder, self.mod, True)
                self.assertEqual(set(rows), {"Keyed|Greeting", "Keyed|Optional", "Keyed|Third"})
                self.assertFalse(any(error.startswith("duplicate_key_across_language_roots:") for error in errors))
                self.assertIn("duplicate_xml_path_across_language_roots:" + relative, errors)
                with self.assertRaisesRegex(ValueError, "duplicate_xml_path_across_language_roots"):
                    rw.stage(self.root, "author.mod", self.root / "dist")

    def test_distinct_xml_paths_stage_disjoint_keys_from_base_and_two_conditions(self):
        self.second_conditional_fixture("Second.xml")
        errors, warnings, rows = rw.validate_payload(self.folder, self.mod, True)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(set(rows), {"Keyed|Greeting", "Keyed|Optional", "Keyed|Third"})
        output = rw.stage(self.root, "author.mod", self.root / "dist")
        self.assertTrue((output / "Languages/Russian/Keyed/Main.xml").is_file())
        self.assertTrue((output / "Conditional/another.mod/Languages/Russian/Keyed/Optional.xml").is_file())
        self.assertTrue((output / "Conditional/second.mod/Languages/Russian/Keyed/Second.xml").is_file())

    def test_conditional_only_supplement_needs_no_unconditional_strings(self):
        self.conditional_fixture()
        (self.ru / "Main.xml").unlink()
        (self.ru / "ConditionalCompatibility.xml").write_text("<LanguageData/>", encoding="utf-8")
        self.mod["qa"]["payload_sha256"] = rw.payload_digest(self.payload)
        errors, _, rows = rw.validate_payload(self.folder, self.mod, True)
        self.assertEqual(errors, [])
        self.assertEqual(set(rows), {"Keyed|Optional"})

    def test_conditional_layout_does_not_expand_ordinary_manifest_allowlist(self):
        self.conditional_fixture()
        del self.mod["conditional_languages"]
        errors = rw.validate_payload(self.folder, self.mod)[0]
        self.assertIn("forbidden_payload_file:LoadFolders.xml", errors)
        self.assertIn("forbidden_payload_file:Conditional/another.mod/Languages/Russian/Keyed/Optional.xml", errors)

    def test_conditional_layout_traversal_cannot_expand_allowlist(self):
        self.conditional_fixture()
        self.mod["conditional_languages"]["roots"][0]["path"] = "Conditional/../another.mod"
        errors = rw.validate_payload(self.folder, self.mod)[0]
        self.assertIn("conditional_language_path_or_condition_invalid", errors)
        self.assertIn("forbidden_payload_file:LoadFolders.xml", errors)

    def test_conditional_layout_requires_same_pinned_source_evidence(self):
        self.conditional_fixture()
        rw.write_json(self.folder / "source-layout-evidence.json", {"schema": 1, "package_id": "wrong.mod"})
        self.assertIn("conditional_language_evidence_missing_or_changed", rw.validate_payload(self.folder, self.mod)[0])

    def test_conditional_evidence_cannot_reference_an_outside_json(self):
        self.conditional_fixture()
        self.mod["conditional_languages"]["evidence"] = "../private.json"
        self.assertIn("conditional_language_evidence_invalid", rw.validate_payload(self.folder, self.mod)[0])

    def test_conditional_unknown_condition_is_rejected_instead_of_ignored(self):
        self.conditional_fixture()
        p = self.payload / "LoadFolders.xml"
        p.write_text(p.read_text("utf-8").replace("IfModActive=", "IfModActiveAny="), "utf-8")
        errors = rw.validate_payload(self.folder, self.mod)[0]
        self.assertIn("conditional_loadfolders_missing_or_invalid", errors)
        self.assertIn("forbidden_payload_file:LoadFolders.xml", errors)

    def test_conditional_extra_version_section_is_rejected(self):
        self.conditional_fixture()
        p = self.payload / "LoadFolders.xml"
        p.write_text(p.read_text("utf-8").replace("</loadFolders>", "<default><li>/</li></default></loadFolders>"), "utf-8")
        self.assertIn("conditional_loadfolders_missing_or_invalid", rw.validate_payload(self.folder, self.mod)[0])

    def test_conditional_loader_cannot_name_a_different_dependency(self):
        self.conditional_fixture()
        p = self.payload / "LoadFolders.xml"
        p.write_text(p.read_text("utf-8").replace('IfModActive="another.mod"', 'IfModActive="unknown.mod"'), "utf-8")
        self.assertIn("conditional_loadfolders_missing_or_invalid", rw.validate_payload(self.folder, self.mod)[0])

    def test_conditional_cross_root_collision_is_rejected_even_for_equal_text(self):
        self.conditional_fixture(key="Greeting", value="Привет, {0}!")
        self.assertIn("duplicate_key_across_language_roots:Keyed|Greeting", rw.validate_payload(self.folder, self.mod)[0])

    def test_conditional_roots_never_allow_original_defs_or_assemblies(self):
        self.conditional_fixture()
        p = self.payload / "Conditional/another.mod/Assemblies"
        p.mkdir()
        (p / "Original.dll").write_bytes(b"MZ")
        p = self.payload / "Conditional/another.mod/Defs"
        p.mkdir()
        (p / "Original.xml").write_text("<Defs />", "utf-8")
        errors = rw.validate_payload(self.folder, self.mod)[0]
        self.assertIn("forbidden_payload_file:Conditional/another.mod/Assemblies/Original.dll", errors)
        self.assertIn("forbidden_payload_file:Conditional/another.mod/Defs/Original.xml", errors)

    def test_conditional_source_placeholder_checks_are_not_skipped(self):
        self.conditional_fixture(value="Утерянный аргумент")
        self.assertIn("placeholder_mismatch:Keyed|Optional", rw.validate_payload(self.folder, self.mod, True)[0])

    def test_conditional_unknown_source_is_not_release_ready(self):
        self.conditional_fixture(key="Unbound")
        self.assertIn("source_signature_missing_or_unbound:Keyed|Unbound", rw.validate_payload(self.folder, self.mod, True)[0])

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

    def test_community_translation_merge_stays_distinct_and_acknowledged(self):
        self.mod["integration"] = {"pr_url": "https://github.com/author/community/pull/7",
            "target_kind": "community_translation", "status": "accepted_into_community_translation",
            "original_native_accepted": False}
        self.save()
        merged = b'{"state":"closed","merged_at":"2026-10-30T00:00:00Z"}'
        with patch.object(rw, "fetch_bytes", return_value=merged):
            result = rw.check_integration(self.mod)
        self.assertEqual(result["status"], "accepted_into_community_translation")
        self.assertFalse(result["action_required"])
        self.assertFalse(self.mod["integration"]["original_native_accepted"])
        self.assertEqual(rw.registry(self.root)["counts"]["accepted"], 0)
        self.mod["integration"]["status"] = "pr_submitted"
        with patch.object(rw, "fetch_bytes", return_value=merged):
            result = rw.check_integration(self.mod)
        self.assertTrue(result["action_required"])

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

    def test_private_model_review_counts_do_not_promote_release_or_native_acceptance(self):
        self.mod["inventory"] = {
            "draft_work": {"semantic_review": {"reviewed_tasks": 2, "decisions": {"approve": 1, "hold": 1}}},
            "reviewed_model_private_test": {"verified_target_values": 1},
        }
        self.mod["rights"]["translation"]["status"] = "unknown"
        self.mod["integration"] = {"status": "pr_submitted", "target_kind": "community_translation",
                                   "pr_url": "https://github.com/community/translations/pull/1"}
        self.save()
        rw.write_json(self.root / "reports/reviewed-batches-future.json", {
            "reviewed_managed_batch": {"packages": 1, "matching_values": 7},
            "local_model_review": {"reviewed_tasks": 2, "private_runtime_test": {
                "verified_target_values": 1, "provider_count": 1, "combined_matching_values": 8}},
        })
        result = rw.registry(self.root)
        self.assertEqual(result["counts"]["model_reviewed_tasks"], 2)
        self.assertEqual(result["counts"]["model_held_tasks"], 1)
        self.assertEqual(result["counts"]["private_model_test_values"], 1)
        self.assertEqual(result["counts"]["game_tested"], 0)
        self.assertEqual(result["counts"]["accepted"], 0)
        self.assertEqual(result["counts"]["awaiting_rights"], 1)
        status = rw.status_markdown(result, self.root)
        self.assertIn("2 local-model tasks processed", status)
        self.assertIn("1 values verified across 1 providers", status)
        self.assertIn("original-native acceptance not claimed", status)


if __name__ == "__main__":
    unittest.main()
