# ポケモンRAGシステム

ベクトル検索と大規模言語モデルに基づくポケモン情報の検索システムです。このシステムはベクトルデータベースとセマンティック検索技術を活用して、自然言語クエリに基づいて関連するポケモン情報を返します。

## 使用するAIモデル

### 1. Sentence Transformer
- モデル: `paraphrase-multilingual-mpnet-base-v2`
- 目的: 多言語テキスト埋め込みの生成
- 特徴:
  - 複数言語対応（中国語、日本語、英語）
  - セマンティック類似性タスクに最適化
  - 768次元のベクトル出力

### 2. 大規模言語モデル（Groq経由）
- モデル: `llama-3.2-90b-vision-preview`
- 目的: 自然言語理解と生成
- 特徴:
  - 高度なコンテキスト理解
  - 多言語レスポンス生成
  - ストーリー生成機能

## APIキーに関する重要な注意事項

⚠️ **Groq APIの設定が必要**

このシステムは高度な言語処理にGroqのLLM APIを使用します。システムを使用する前にGroq APIキーを設定する必要があります：

1. `flask-app`ディレクトリに`.env`ファイルを作成
2. Groq APIキーを追加：
```
KEY_groq=your_groq_api_key_here
```

## システムアーキテクチャ

システムは以下の主要コンポーネントで構成されています：

- **フロントエンド**: Reactベースのユーザーインターフェース
  - 検索インターフェース
  - ポケモン詳細表示
  - 類似度スコアの可視化

- **バックエンド**: Flaskベースのバックエンドサービス
  - SentenceTransformerによるクエリ処理
  - ベクトル検索サービス
  - Groq API経由のLlama 3.2 90B統合

- **Elasticsearch**: ベクトルデータベース
  - ポケモン情報の保存
  - ベクトル類似度検索

## 主要機能

1. **セマンティック検索**
   - SentenceTransformerによる自然言語クエリ対応
   - 類似度ベースのポケモン検索
   - 多言語対応（中国語、日本語、英語）

2. **高度な言語処理（Llama 3.2経由）**
   - コンテキストを考慮したレスポンス生成
   - ポケモンの背景ストーリー作成
   - 関連性分析

3. **RAG（検索拡張生成）**
   - 検索結果に基づくコンテキスト生成
   - 関連性分析とスコアリング
   - ポケモンの背景ストーリー自動生成

## クイックスタート

### 前提条件

- Docker & Docker Compose
- Python 3.8以上
- 有効なGroq APIキー

### インストール手順

1. リポジトリのクローン
```bash
git clone <repository-url>
cd pokemon_rag
```

2. Groq APIキーの設定
```bash
# flask-app/.envに記述
KEY_groq=your_groq_api_key_here
```

3. サービスのビルド
```bash
docker-compose build
```

4. サービスの起動
```bash
docker-compose up -d
```

5. 初期データの生成
```bash
docker exec -it [container_name/id] bash
make injest
```

システムは以下のポートで起動します：
- フロントエンド: http://localhost:3000
- バックエンド: http://localhost:8080
- Elasticsearch: http://localhost:9200