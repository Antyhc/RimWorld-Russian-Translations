import copy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import Mock, patch
import uuid

SPEC = importlib.util.spec_from_file_location("steam_test_rw", Path(__file__).resolve().parents[1] / "scripts/rwtranslations.py")
rw = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rw)


class PublicSteamMonitorTests(unittest.TestCase):
    def test_fetch_discards_creator_and_never_forwards_github_auth(self):
        payload = {"response": {"publishedfiledetails": [{"publishedfileid": "1234", "result": 1,
            "consumer_app_id": 294100, "time_updated": 100, "file_size": "20", "hcontent_file": "55",
            "creator": "PRIVATE_CREATOR", "description": "unneeded original text", "file_url": "unneeded"}]}}
        opener = Mock()
        opener.open.return_value = io.BytesIO(json.dumps(payload).encode())
        with patch.object(rw.urllib.request, "build_opener", return_value=opener), patch.dict(rw.os.environ, {"GITHUB_TOKEN": "DO_NOT_FORWARD"}):
            result = rw.fetch_steam_details(["1234"])
        request = opener.open.call_args.args[0]
        self.assertNotIn("Authorization", request.headers)
        self.assertNotIn("Cookie", request.headers)
        self.assertNotIn(b"DO_NOT_FORWARD", request.data)
        self.assertNotIn("creator", result["1234"])
        self.assertNotIn("description", result["1234"])
        self.assertNotIn("file_url", result["1234"])

    def test_invalid_and_oversize_batches_are_refused(self):
        for values in ([], ["0"], ["no"], [str(2**64)], [str(i) for i in range(1, 52)]):
            with self.assertRaises(ValueError):
                rw.fetch_steam_details(values)

    def test_redirects_are_not_followed(self):
        with self.assertRaises(ValueError):
            rw.NoSteamRedirect().redirect_request(None, None, 302, "redirect", {}, "https://example.org")

    def test_missing_requested_item_is_not_a_passing_check(self):
        opener = Mock()
        opener.open.return_value = io.BytesIO(b'{"response":{"publishedfiledetails":[]}}')
        with patch.object(rw.urllib.request, "build_opener", return_value=opener), self.assertRaises(ValueError):
            rw.fetch_steam_details(["1234"])

    def test_changed_content_handle_and_new_mod_require_review_without_approval(self):
        root = Path(__file__).resolve().parents[1] / ".tests-tmp" / ("steam-" + uuid.uuid4().hex)
        root.mkdir(parents=True)
        try:
            baseline = {"publishedfileid": "1234", "result": 1, "consumer_app_id": 294100,
                        "time_updated": 100, "file_size": 20, "hcontent_file": "55"}
            source = {"schema_version": 1, "endpoint": rw.STEAM_DETAILS_URL, "items": {"1234": baseline}}
            rw.write_json(root / "source.workshop.json", source)
            for package, item_id in (("author.old", "1234"), ("author.new", "5678")):
                rw.write_json(root / "mods" / package / "manifest.json", {"schema_version": 1, "package_id": package,
                    "name": package, "original": {"workshop_id": item_id}, "qa": {"source_current": False}})
            changed = {**baseline, "hcontent_file": "56"}
            with patch.object(rw, "fetch_steam_details", return_value={"1234": changed, "5678": {**baseline, "publishedfileid": "5678"}}):
                results = {row["package_id"]: row for row in rw.check_workshop(root)}
            self.assertEqual(results["author.old"]["status"], "updated")
            self.assertEqual(results["author.old"]["changed_fields"], ["hcontent_file"])
            self.assertEqual(results["author.new"]["status"], "baseline_missing")
            self.assertFalse(rw.read_json(root / "mods/author.old/manifest.json")["qa"]["source_current"])
            self.assertEqual(rw.read_json(root / "source.workshop.json"), source)
        finally:
            shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
