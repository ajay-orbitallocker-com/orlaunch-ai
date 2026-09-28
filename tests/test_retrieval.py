import unittest
from rag.retrieval.search import (
    build_where_clause,
    calculate_per_category_document_count,
    get_all_categories,
)
from rag.ingestion.config import get_default_categories


class TestRetrievalHelpers(unittest.TestCase):
    def test_build_where_clause_empty(self):
        self.assertIsNone(build_where_clause())

    def test_build_where_clause_single_category(self):
        where = build_where_clause(category_filter="Technical & TRL")
        self.assertEqual(where, {"category": "Technical & TRL"})

    def test_build_where_clause_multiple_categories(self):
        where = build_where_clause(category_filter=["Technical & TRL", "Patents & IP"])
        self.assertEqual(where, {"category": {"$in": ["Technical & TRL", "Patents & IP"]}})

    def test_build_where_clause_category_and_source(self):
        where = build_where_clause(category_filter="Market Intelligence", source_filter="SpaceNews")
        self.assertEqual(where, {
            "$and": [
                {"category": "Market Intelligence"},
                {"source": "SpaceNews"}
            ]
        })

    def test_build_where_clause_additional_filters(self):
        where = build_where_clause(trl_current=5)
        self.assertEqual(where, {"trl_current": 5})

    def test_calculate_per_category_document_count(self):
        cats = ["Technical & TRL", "Market Intelligence", "Financial Intelligence", "Patents & IP"]
        self.assertEqual(calculate_per_category_document_count(4, cats), 1)
        self.assertEqual(calculate_per_category_document_count(8, cats), 2)
        self.assertEqual(calculate_per_category_document_count(2, cats), 1)
        self.assertEqual(calculate_per_category_document_count(10, []), 10)

    def test_get_all_categories_not_empty(self):
        cats = get_all_categories()
        self.assertTrue(len(cats) > 0)
        default_cats = get_default_categories()
        for dc in default_cats:
            self.assertIn(dc, cats)


if __name__ == "__main__":
    unittest.main()
