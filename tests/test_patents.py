import unittest
from rag.ingestion.sources.patents import config as patents_config
from rag.ingestion.sources.patents import patents


class TestPatentsModule(unittest.TestCase):
    def test_patent_sources_defined_in_config(self):
        self.assertTrue(hasattr(patents_config, "PATENT_SOURCES"))
        self.assertIsInstance(patents_config.PATENT_SOURCES, list)
        self.assertTrue(len(patents_config.PATENT_SOURCES) > 0)
        source_names = [s["name"] for s in patents_config.PATENT_SOURCES]
        self.assertIn("NASA STI (NTRS)", source_names)
        self.assertIn("USPTO PatentsView", source_names)
        self.assertNotIn("USPTO Prior Art Database", source_names)

    def test_no_curated_servicing_patents_in_module(self):
        self.assertFalse(hasattr(patents, "CURATED_SERVICING_PATENTS"))

    def test_document_text_builders(self):
        mock_patent = {
            "patent_id": "12345678",
            "patent_title": "Test Space Docking",
            "patent_date": "2024-01-01",
            "patent_abstract": "A test docking system."
        }
        text = patents.build_patent_document_text(mock_patent)
        self.assertIn("Patent US12345678", text)
        self.assertIn("Test Space Docking", text)

        mock_sti = {
            "id": "20240001",
            "title": "NASA Servicing Report",
            "distributionDate": "2024-02-01",
            "abstract": "NASA orbital servicing research.",
            "stiTypeDetails": "Technical Report"
        }
        sti_text = patents.build_nasa_sti_document_text(mock_sti)
        self.assertIn("NASA-STI-20240001", sti_text)
        self.assertIn("NASA Servicing Report", sti_text)


if __name__ == "__main__":
    unittest.main()
