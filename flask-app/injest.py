import sqlite3
import pandas as pd
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch
from typing import List, Dict, Any
import ast
import logging
from tqdm import tqdm

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PokemonIngest:
    def __init__(self, model_path: str = "paraphrase-multilingual-mpnet-base-v2", es_host: str = "http://localhost:9200"):
        """
        イニシャライザー
        Args:
            model_path: sentence-transformerモデルのパス
            es_host: Elasticsearchホストアドレス
        """
        self.model = SentenceTransformer(model_path)
        self.es = Elasticsearch([es_host])
        
    def prepare_data(self, db_path: str = 'pokedex.db') -> pd.DataFrame:

        logger.info("loading...")
        
        with sqlite3.connect(db_path) as conn:
            # 读取数据
            df_paldea = pd.read_sql_query("SELECT * FROM paldea", conn)
            df_pokedex = pd.read_sql_query("SELECT * FROM pokedex", conn).drop('form', axis=1)
            
            # 合并数据
            merged_df = pd.merge(df_paldea, df_pokedex, 
                            left_on='globalNo', right_on='id', 
                            how='left')
        
        # 使用pandas的矢量化操作处理数据
        result_df = pd.DataFrame({
            'name_japanese': merged_df['jpn'].astype(str).replace('nan', ''),
            'name_english': merged_df['eng'].astype(str).replace('nan', ''),
            'name_chinese': merged_df['chs'].astype(str).replace('nan', ''),
            'global_no': merged_df['globalNo'].astype(str).where(merged_df['globalNo'].notna(), None),
            'form': merged_df['form'].astype(str).replace('nan', ''),
            'types': merged_df.apply(lambda x: [t for t in [x['type1'], x['type2']] if pd.notna(t)], axis=1),
            'abilities': merged_df.apply(lambda x: [a for a in [x['ability1'], x['ability2'], x['dream_ability']] 
                                                if pd.notna(a)], axis=1),
            'stats_hp': merged_df['hp'].where(merged_df['hp'].notna(), None).astype('Int64'),
            'stats_attack': merged_df['attack'].where(merged_df['attack'].notna(), None).astype('Int64'),
            'stats_defense': merged_df['defense'].where(merged_df['defense'].notna(), None).astype('Int64'),
            'stats_special_attack': merged_df['special_attack'].where(merged_df['special_attack'].notna(), None).astype('Int64'),
            'stats_special_defense': merged_df['special_defense'].where(merged_df['special_defense'].notna(), None).astype('Int64'),
            'stats_speed': merged_df['speed'].where(merged_df['speed'].notna(), None).astype('Int64'),
            'description_scarlet': merged_df['scarlet'].astype(str).where(merged_df['scarlet'].notna(), None),
            'description_violet': merged_df['violet'].astype(str).where(merged_df['violet'].notna(), None)
        })

        logger.info(f"{len(result_df)} records load complete")
        return result_df

    def safe_process(self, value: Any, field_type: str) -> str:
        if pd.isna(value):
            return None
        
        if field_type == 'list':
            if isinstance(value, list):
                return ' '.join(value)
            if isinstance(value, str):
                try:
                    value = ast.literal_eval(value)
                except:
                    value = [x.strip() for x in value.split(',')]
                return ' '.join(value)
        
        return str(value)

    def create_combined_text(self, df: pd.Series) -> str:
        text_fields = []
        
        for col in df.index:
            if col.startswith('stats_'):
                continue
                
            value = df[col]
            text_fields.append(f"{value}")
        
        print('text_fields:', text_fields)
        return " ".join(text_fields)


    def generate_vector(self, text: str) -> List[float]:
        return self.model.encode(text, show_progress_bar=False).tolist()

    def process_dataframe(self, df: pd.DataFrame) -> List[Dict]:
        logger.info("データ処理開始...")
        df = df.copy()
        
        logger.info("テキスト結合中...")
        df['combined_text'] = df.apply(self.create_combined_text, axis=1)
        
        logger.info("ベクトル生成中...")
        tqdm.pandas(desc="データ処理", bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}')
        df['combined_text_vector'] = df['combined_text'].progress_apply(self.generate_vector)
        
        logger.info("データ処理完了")
        return df.to_dict('records')
    
    def create_index(self, index_name: str = "") -> None:
        index_settings = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "global_no": {"type": "keyword"},
                    "name_japanese": {"type": "text"},
                    "name_english": {"type": "text"},
                    "name_chinese": {"type": "text"}, 
                    "form": {"type": "keyword"},
                    "types": {"type": "keyword"},
                    "abilities": {"type": "keyword"},
                    "stats_hp": {"type": "integer"},
                    "stats_attack": {"type": "integer"},
                    "stats_defense": {"type": "integer"},
                    "stats_special_attack": {"type": "integer"},
                    "stats_special_defense": {"type": "integer"},
                    "stats_speed": {"type": "integer"},
                    "description_scarlet": {"type": "text"},
                    "description_violet": {"type": "text"},
                    "combined_text_vector": {
                        "type": "dense_vector",
                        "dims": 768,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            }
        }

        self.es.indices.delete(index=index_name, ignore_unavailable=True)

        self.es.indices.create(index=index_name, body=index_settings)
        logger.info(f"インデックス {index_name} の作成が完了しました")

    def bulk_index_documents(self, documents: List[Dict], 
                           index_name: str = "test2", 
                           batch_size: int = 100) -> None:

        logger.info(f"インデックス {index_name} へのドキュメント一括登録開始")
        
        for i in tqdm(range(0, len(documents), batch_size), desc="インデックス進捗"):
            batch = documents[i:i + batch_size]
            bulk_data = []
            
            for doc in batch:
                bulk_data.append({"index": {"_index": index_name}})
                bulk_data.append(doc)
            
            try:
                response = self.es.bulk(body=bulk_data)
                if response.get('errors'):
                    logger.error(f"バッチ {i//batch_size + 1} のインデックスでエラーが発生")
            except Exception as e:
                logger.error(f"バッチ {i//batch_size + 1} で例外が発生: {str(e)}")
                
        logger.info("ドキュメントのインデックスが完了しました")

def main():
    DB_PATH = "pokedex.db"
    INDEX_NAME = "pk"
    ES_HOST = "http://elasticsearch:9200"
    MODEL_PATH = "paraphrase-multilingual-mpnet-base-v2"
    
    try:
        ingest = PokemonIngest(model_path=MODEL_PATH, es_host=ES_HOST)

        df = ingest.prepare_data(DB_PATH)
 
        ingest.create_index(index_name=INDEX_NAME)
        
        processed_data = ingest.process_dataframe(df)
        
        ingest.bulk_index_documents(processed_data, index_name=INDEX_NAME)
        
        logger.info("全ての処理が完了しました")
        
    except Exception as e:
        logger.error(f"処理中にエラーが発生しました: {str(e)}")
        raise

if __name__ == "__main__":
    main()
