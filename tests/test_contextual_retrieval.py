import unittest
from code_reviewer_agent.services.contextual_retrieval import ContextualRetrieval

class TestContextualRetrieval(unittest.TestCase):
    document = "This is my whole document."
    chunks = ("This is my", "whole document.")

    def test_chunks_and_document_valid(self):
        contextual_retrieval = ContextualRetrieval(self.document, self.chunks)
        self.assertEqual(contextual_retrieval.document, self.document)
        self.assertEqual(contextual_retrieval.chunks, self.chunks)

    def test_contextual_returned_with_chunk(self):
        pass

if __name__ == "__main__":
    unittest.main()
