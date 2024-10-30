import unittest
from unittest.mock import Mock, patch
import numpy as np
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
from vector_search import VectorSearchEngine # Add this import

class TestVectorSearchEngine(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.base_url = 'http://localhost:8080'
        self.key_groq = os.getenv('KEY_groq')
        
        with patch('elasticsearch.Elasticsearch'), \
             patch('sentence_transformers.SentenceTransformer'):
            self.engine = VectorSearchEngine()
            self.engine.es_client = Mock()
            self.engine.model = Mock()

    def test_search(self):
        self.engine.model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_hits = {
            'hits': {
                'hits': [{
                    '_source': {
                        'name_english': 'Pikachu',
                        'name_chinese': '皮卡丘',
                        'types': ['Electric'],
                        'abilities': ['Static'],
                        'global_no': '025',
                        'description_scarlet': 'Mouse Pokemon'
                    }
                }]
            }
        }
        self.engine.es_client.search.return_value = mock_hits

        results = self.engine.search("electric pokemon")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['nameEn'], 'Pikachu')
        self.engine.es_client.search.assert_called_once()

    def test_build_prompt(self):
        query = "Who is Pikachu?"
        search_results = [{
            'nameEn': 'Pikachu',
            'nameCn': '皮卡丘',
            'types': ['Electric'],
            'abilities': ['Static'],
            'number': '025',
            'description': 'Mouse Pokemon'
        }]

        prompt = self.engine.build_prompt(query, search_results)
        self.assertIn('Pikachu', prompt)
        self.assertIn('Mouse Pokemon', prompt)
        self.assertIn(query, prompt)

    @patch('builtins.client')
    def test_llm(self, mock_client):
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_response.usage = Mock(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15
        )
        mock_client.chat.completions.create.return_value = mock_response

        answer, token_stats = self.engine.llm("test prompt")
        
        self.assertEqual(answer, "Test response")
        self.assertEqual(token_stats['total_tokens'], 15)

    def test_evaluate_relevance(self):
        with patch.object(self.engine, 'llm') as mock_llm:
            mock_llm.return_value = ('{"Relevance": "RELEVANT", "Explanation": "Test"}', {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            })

            result, tokens = self.engine.evaluate_relevance(
                "test question",
                "test answer"
            )

            self.assertEqual(result["Relevance"], "RELEVANT")
            self.assertEqual(tokens["total_tokens"], 15)

    def test_rag(self):
        with patch.object(self.engine, 'search') as mock_search, \
             patch.object(self.engine, 'llm') as mock_llm, \
             patch.object(self.engine, 'evaluate_relevance') as mock_eval:
            
            mock_search.return_value = [{"nameEn": "Pikachu"}]
            mock_llm.return_value = ("Test answer", {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            })
            mock_eval.return_value = (
                {"Relevance": "RELEVANT", "Explanation": "Test"},
                {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}
            )

            result = self.engine.rag("test query")

            self.assertIn("answer", result)
            self.assertIn("relevance", result)
            self.assertIn("total_tokens", result)

if __name__ == '__main__':
    unittest.main()