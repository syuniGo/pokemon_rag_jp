from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch
import os
import rag
import logging

# 初始化ES客户端和模型
es_client = Elasticsearch([os.getenv('ES_HOST', 'http://elasticsearch:9200')])
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
app = Flask(__name__)
CORS(app)  # Allows all origins by default
@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    print("I am inside hello world")
    return 'Hello World! CD'

@app.route('/echo/<name>')
def echo(name):
    print(f"This was placed in the url: new-{name}")
    val = {"new-name": name}
    return jsonify(val)

@app.route('/api/search', methods=['POST'])
def search():
    try:
        print('Search starting')
        data = request.get_json()
        print(f'Request data: {data}')
        
        engine = rag.VectorSearchEngine()
        query = data.get('query', '')
        print(f'Search query: {query}')
        result = engine.rag(query)
        print(f'Search result: {result}')
        
        return jsonify(result)
    except Exception as e:
        print(f'Error: {str(e)}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
