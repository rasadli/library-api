"""Documentation checks that never execute mutating library operations."""
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from app import app


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and "src" in attrs:
            self.urls.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.urls.append(attrs["href"])


class DocumentationTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        with self.client.get("/openapi.json") as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, "application/json")
            self.spec = response.get_json()

    def test_spec_metadata_and_operations(self):
        self.assertEqual(self.spec["openapi"], "3.0.3")
        self.assertEqual(self.spec["info"]["title"], "Library Management API")
        self.assertEqual(self.spec["info"]["version"], "1.0.0")
        operation_ids = []
        for path in self.spec["paths"].values():
            for operation in path.values():
                self.assertTrue(operation["summary"])
                self.assertTrue(operation["description"])
                self.assertTrue(operation["responses"])
                self.assertIn(operation["tags"][0], ("Books", "Members", "Loans", "Reports"))
                operation_ids.append(operation["operationId"])
        self.assertEqual(len(operation_ids), len(set(operation_ids)))

    def test_documented_operations_match_library_routes(self):
        actual = set()
        for rule in app.url_map.iter_rules():
            if rule.endpoint.split(".")[0] in ("books", "members", "loans", "reports"):
                path = re.sub(r"<int:(\w+)>", r"{\1}", rule.rule)
                actual.update((path, method.lower()) for method in rule.methods - {"HEAD", "OPTIONS"})
        documented = {(path, method) for path, item in self.spec["paths"].items() for method in item}
        self.assertEqual(documented, actual)
        self.assertEqual(len(documented), 16)

    def test_all_schema_references_resolve(self):
        def walk(value):
            if isinstance(value, dict):
                if "$ref" in value:
                    self.assertTrue(value["$ref"].startswith("#/"))
                    target = self.spec
                    for part in value["$ref"][2:].split("/"):
                        target = target[part]
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(self.spec)

    def test_docs_and_local_assets_are_available(self):
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/html")
        html = response.get_data(as_text=True)
        self.assertIn("SwaggerUIBundle", html)
        self.assertIn("/openapi.json", html)
        parser = AssetParser()
        parser.feed(html)
        self.assertEqual(len(parser.urls), 2)
        for url in parser.urls:
            self.assertTrue(url.startswith("/static/swagger-ui/"))
            with self.client.get(url) as asset:
                self.assertEqual(asset.status_code, 200)
                self.assertGreater(len(asset.get_data()), 1000)

    def test_loading_documentation_does_not_touch_library_data(self):
        paths = [Path("library.db"), Path("outbox.txt")]
        def fingerprints():
            return {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                    if path.exists() else None for path in paths}
        before = fingerprints()
        with patch("db.connect", side_effect=AssertionError("Documentation accessed database")), \
             patch("notifications.send_email", side_effect=AssertionError("Documentation sent email")):
            for url in ("/docs", "/openapi.json", "/static/swagger-ui/swagger-ui.css",
                        "/static/swagger-ui/swagger-ui-bundle.js"):
                with self.client.get(url) as response:
                    self.assertEqual(response.status_code, 200)
        self.assertEqual(before, fingerprints())


if __name__ == "__main__":
    unittest.main()
