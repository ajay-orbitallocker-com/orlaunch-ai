import unittest
from rag.ingestion import ingest_all


class TestIngestionModule(unittest.TestCase):
    def test_no_legacy_or_duplicate_helpers(self):
        self.assertFalse(hasattr(ingest_all, "clean_legacy_unidentified_chunks"))
        self.assertFalse(hasattr(ingest_all, "ingest_small_sources_sync"))

    def test_registry_contains_all_four_sources(self):
        registry = ingest_all.get_source_registry()
        labels = [item[0] for item in registry]
        self.assertEqual(len(labels), 4)
        self.assertIn("NASA TechPort", labels)
        self.assertIn("SEC EDGAR", labels)
        self.assertIn("USPTO Patents", labels)
        self.assertIn("RSS Market News", labels)

    def test_collect_with_selected_sources_filtering(self):
        # Pass non-existent source label to verify filtering logic without making network calls
        docs = ingest_all.collect_all_raw_documents(selected_sources=["NonExistentSource"])
        self.assertEqual(docs, [])


if __name__ == "__main__":
    unittest.main()
