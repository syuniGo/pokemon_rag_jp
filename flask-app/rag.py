import pandas as pd

from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch
import numpy as np
import os
import logging
from time import time
from groq import Groq
import json
import re


class VectorSearchEngine:
    def __init__(self):
        self.es_client = Elasticsearch([os.getenv('ES_HOST', 'http://elasticsearch:9200')])
        self.model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        self.groq = Groq(api_key=os.getenv('KEY_groq'))
        self.llm_model = 'llama-3.2-90b-vision-preview'
        
        self.prompt_template = """
            あなたはポケモンマスターアナリストであり、ポケモン怪談専門の小説家です。
            CONTEXTの各ポケモンについて、QUESTIONとの関係を分析・評価し、以下の形式で出力してください。
            注意事項:
            - 必ず有効なJSONフォーマットで出力すること
            - バックスラッシュ(\)や特殊文字、エスケープ文字を含めないこと
            - アンダースコア(_)は単独で使用し、\_のような形式は使用しないこと
            - 余計な文字や改行を含めないこと
            出力形式は以下のJSONで:
            
            {{
                "pokemon_entries": [
                    {{
                    "no": 数字で図鑑番号,
                    "name": "ポケモンの名前",
                    "relevance_score": 0から100までの数字,
                    "power_rating": "S/A/B/C/Dのいずれか",
                    "relevance_analysis": "日本語で関連性の分析を100文字以内で",
                    "background_story": "日本語で怪談を200文字以内で"
                    }}
                ],
                "summary": {{
                    "most_relevant_pokemon": {{
                    "no": "最も関連性の高いポケモンの図鑑番号",
                    "name": "ポケモン名",  
                    "explanation": "日本語で選択理由を100文字以内で"
                    }}
                }}
            }}
            
            実力ランクの基準:
            S: 種族値合計600以上または特に強力な特性
            A: 種族値合計500-599または優れた特性
            B: 種族値合計400-499で通常の特性
            C: 種族値合計300-399
            D: 種族値合計300未満

            分析の注意点:
            - 怪談は不気味さや恐怖を感じる要素を必ず含めること
            - 関連性分析は客観的な根拠に基づくこと
            - スコアは具体的な要素から算出すること

            QUESTION: {question}
            CONTEXT: {context}
        """
            
        self.entry_template = """
            "nameEn": {nameEn},
            "nameCn": {nameCn},
            "nameJa": {nameJa},
            "types": {types},
            "abilities": {abilities},
            "no": {no},
            "description": {description},
            "hp": {stats[hp]},
            "attack": {stats[attack]},
            "defense": {stats[defense]},
            "specialAttack": {stats[specialAttack]},
            "specialDefense": {stats[specialDefense]},
            "speed": {stats[speed]}
        """.strip()
            
        
        self.evaluation_prompt_template = """
            あなたはRAGシステムの専門評価者です。
                与えられた質問に対する生成された回答の関連性を分析することがあなたの任務です。
                生成された回答の関連性に基づいて、「無関係」、「部分関連」、または「関連あり」に分類してください。

                評価のためのデータは以下の通りです：

                質問: {question}
                生成された回答: {answer}

                生成された回答の内容と文脈を質問との関連で分析し、
                以下のような解析可能なJSONで評価を提供してください（コードブロックは使用しない、追加の説明なし、日本語）：

            {{
                "Relevance": "無関係" | "部分的に関連" | "関連あり",
                "relevance_explanation": "[評価の簡潔な説明を提供してください]"
            }}
            
        """.strip()
            
            
    def search(self, query, top_k=5):
        try:
            print(f'Search query: {query}, top_k: {top_k}')
            
            query_vector = self.model.encode(query).tolist()
            vector_dim = len(query_vector)
            print(f"Query vector dimension: {vector_dim}")
            search_body = {
                "knn": {
                    "field": "combined_text_vector",
                    "query_vector": query_vector,
                    "k": top_k,
                    "num_candidates": 100
                },
                "collapse": {
                    "field": "global_no"  
                },
                "_source": {
                    "excludes": ["combined_text_vector"]
                }
            }

            results = self.es_client.search(
                    index="pk",
                    body=search_body
                )

            return [{
                'nameEn': hit['_source']['name_english'],
                'nameCn': hit['_source']['name_chinese'],
                'nameJa': hit['_source']['name_japanese'],
                'types': hit['_source']['types'],
                'abilities': hit['_source']['abilities'],
                'no': hit['_source']['global_no'],
                'description': hit['_source']['description_scarlet'],
                'descriptionViolet': hit['_source']['description_violet'],
                'form': hit['_source']['form'],
                'stats': {
                    'hp': hit['_source']['stats_hp'],
                    'attack': hit['_source']['stats_attack'],
                    'defense': hit['_source']['stats_defense'],
                    'specialAttack': hit['_source']['stats_special_attack'],
                    'specialDefense': hit['_source']['stats_special_defense'],
                    'speed': hit['_source']['stats_speed']
                }
            } for hit in results['hits']['hits']]

        except Exception as e:
            return str(e)

    def build_prompt(self, query, search_results):
        context = ""

        for doc in search_results:
            context = context + self.entry_template.format(**doc) + "\n\n"

        prompt = self.prompt_template.format(question=query, context=context).strip()
        return prompt


    def llm(self, prompt):
        response = self.groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model= self.llm_model,
        )
        answer = response.choices[0].message.content
        token_stats = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens, 
            "total_tokens": response.usage.total_tokens
        }
        return answer, token_stats

    def evaluate_relevance(self, question, answer):
        prompt = self.evaluation_prompt_template.format(question=question, answer=answer)
        evaluation, token_stats = self.llm(prompt)
        print(f'Evaluation prompt: {prompt}')
        print(f'Evaluation result: {evaluation}')

        try:
            json_eval = json.loads(evaluation)
            return json_eval, token_stats
        except json.JSONDecodeError:
            result = {"Relevance": "UNKNOWN", "Explanation": "Failed to parse evaluation"}
            return result, token_stats

    def rag(self, query):
        t0 = time()
        print(f'Starting RAG pipeline for query: {query}')

        search_results = self.search(query)
        
        prompt = self.build_prompt(query, search_results)
        
        answer, token_stats = self.llm(prompt)

        answer_json = self.process_json_text(answer)
        relevance, rel_token_stats = self.evaluate_relevance(query, answer)
        
        took = time() - t0

        answer_data = {
            "answer": answer,
            "model_used": self.llm_model,
            "response_time": took,
            "relevance": relevance.get("Relevance", "UNKNOWN"),
            "relevance_explanation": relevance.get("relevance_explanation", "Failed to parse evaluation"),
            "prompt_tokens": token_stats["prompt_tokens"],
            "completion_tokens": token_stats["completion_tokens"], 
            "total_tokens": token_stats["total_tokens"],
            "eval_prompt_tokens": rel_token_stats["prompt_tokens"],
            "eval_completion_tokens": rel_token_stats["completion_tokens"],
            "eval_total_tokens": rel_token_stats["total_tokens"],
            "pokemon_entries": answer_json.get("pokemon_entries"),
            "summary": answer_json.get("summary"),
            "search_results": search_results,
        }
    
        return answer_data

    def process_json_text(self, input_str):
        cleaned_str = input_str.strip('[]')
        
        cleaned_str = cleaned_str.strip("'")  
        
        try:
            json_obj = json.loads(cleaned_str)
            return json_obj
        except json.JSONDecodeError as e:
            print(f"error: {e}")
            return None