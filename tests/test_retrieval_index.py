import unittest

from scripts.retrieval_index import build_retrieval_evidence


FIELD_WEIGHTS = {
    "title": 4.5,
    "summary": 3.5,
    "keywords": 3.5,
    "rules": 3.0,
    "confirmedUnderstanding": 2.5,
    "noteContent": 2.5,
}


class RetrievalIndexTests(unittest.TestCase):
    def test_build_retrieval_evidence_returns_ranked_fts_matches(self) -> None:
        catalog = [
            {
                "caseId": "case-implementation",
                "entryType": "mistake",
                "title": "read implementation first",
                "summary": "read source code before editing documentation",
                "keywords": ["implementation", "docs"],
                "rules": ["read implementation before docs"],
                "confirmedUnderstanding": ["source code is the authority"],
            },
            {
                "caseId": "case-cache",
                "entryType": "note",
                "title": "refresh memory cache",
                "summary": "refresh memory after archiving new notes",
                "keywords": ["memory"],
                "rules": ["refresh memory after archive"],
                "noteContent": ["memory cache must be refreshed"],
            },
        ]

        evidence = build_retrieval_evidence(
            catalog,
            "read implementation before updating docs",
            "project",
            FIELD_WEIGHTS,
        )

        top = evidence["case-implementation"]
        self.assertIn(top["retrievalMethod"], {"sqlite_fts5", "lexical_fallback"})
        self.assertGreater(top["retrievalScore"], evidence["case-cache"]["retrievalScore"])
        self.assertIn("exact_keyword:implementation", top["whyMatched"])
        self.assertTrue(top["fieldHits"])
        self.assertIn("implementation", top["matchedTerms"])


if __name__ == "__main__":
    unittest.main()
