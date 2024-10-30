import pandas as pd

from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch
import numpy as np

class VectorSearchEngine:
    def __init__(self):
    # 初始化ES客户端和模型
        self.es_client = Elasticsearch([os.getenv('ES_HOST', 'http://elasticsearch:9200')])
        self.model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

    def search(query):
        try:
            query = data.get('query', '')
            top_k = data.get('top_k', 100)

            # 向量化查询
            query_vector = model.encode(query).tolist()

            # 构建搜索请求
            search_body = {
                "knn": {
                    "field": "combined_text_vector",
                    "query_vector": query_vector,
                    "k": top_k,
                    "num_candidates": 100
                },
                "_source": ["name_english", "name_chinese", "types", 
                        "abilities", "description_scarlet", "global_no"],
            }

            # 执行搜索
            results = es_client.search(
                index="pokemon_index",
                body=search_body
            )

            # 格式化结果
            formatted_results = [{
                'nameEn': hit['_source']['name_english'],
                'nameCn': hit['_source']['name_chinese'],
                'types': hit['_source']['types'],
                'abilities': hit['_source']['abilities'],
                'number': hit['_source']['global_no'],
                'description': hit['_source']['description_scarlet']
            } for hit in results['hits']['hits']]

            return jsonify({
                'success': True,
                'data': formatted_results
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
            