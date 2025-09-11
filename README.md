# AIエージェント文書要約・Q&Aアプリ

このアプリは、PDFドキュメントをアップロードして、3つのAIエージェント（生徒、先生、要約）による要約とQ&Aセッションを通じて理解を深めるStreamlitアプリケーションです。

## 機能

- **PDFアップロード**: 最大50MBのPDFファイルに対応
- **自動要約**: 文書全体を簡潔に要約
- **Q&Aセッション**: AIエージェントによる対話形式の学習
- **最終レポート**: Markdown形式での包括的なレポート生成
- **リアルタイム表示**: ストリーミング形式での進行状況表示

## 技術仕様

- **フレームワーク**: Streamlit 1.39.0
- **AI Framework**: Semantic Kernel 1.36.0
- **LLM**: GPT-4o (OpenAI API)
- **言語**: Python
- **トークン制限**: 250,000トークン以内

## セットアップ

### 1. 環境構築

```bash
# 仮想環境の作成（既に作成済みの場合はスキップ）
python -m venv venv

# 仮想環境の有効化
source venv/bin/activate  # Linux/Mac
# または
venv\\Scripts\\activate    # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example`をコピーして`.env`ファイルを作成し、OpenAI APIキーを設定してください。

```bash
cp .env.example .env
```

`.env`ファイル内でAPIキーを設定：
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. アプリの起動

```bash
# 仮想環境の有効化
source .venv/bin/activate  # Linux/Mac

# アプリの起動
streamlit run app.py
```

ブラウザで `http://localhost:8502` にアクセスしてアプリを使用できます。

### 4. 追加の依存関係（macOSの場合）

PDF画像抽出機能を使用するには、popplerが必要です：

```bash
brew install poppler
```

## プロジェクト構造

```
qaAgent/
├── app.py                      # メインのStreamlitアプリ
├── requirements.txt            # 依存関係
├── .env.example               # 環境変数のテンプレート
├── config/
│   ├── __init__.py
│   └── settings.py            # API設定、アプリ設定等
├── prompts/                   # プロンプトのバージョン管理
│   ├── student/
│   │   ├── v1_0_0.ini
│   │   └── latest.ini         # 現在使用中バージョンへのシンボリックリンク
│   ├── teacher/
│   │   ├── v1_0_0.ini
│   │   └── latest.ini
│   ├── summarizer/
│   │   ├── v1_0_0.ini
│   │   └── latest.ini
│   └── prompt_loader.py       # .iniファイル読み込みユーティリティ
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # 基底エージェントクラス
│   ├── student_agent.py       # 生徒役エージェント
│   ├── teacher_agent.py       # 先生役エージェント
│   └── summarizer_agent.py    # 要約・整形役エージェント
├── services/
│   ├── __init__.py
│   ├── pdf_processor.py       # PDF読み込み・前処理
│   ├── kernel_service.py      # SK初期化、LLM連携、オーケストレーション
│   ├── chat_manager.py        # チャット履歴管理
│   └── session_manager.py     # セッション状態管理
├── ui/
│   ├── __init__.py
│   ├── components.py          # 再利用可能なUIコンポーネント
│   ├── tabs.py               # タブ切り替えロジック
│   └── styles.py              # カスタムCSS
└── utils/
    ├── __init__.py
    ├── helpers.py             # ユーティリティ関数
    └── validators.py          # 入力検証
```

## 使用方法

1. **PDFファイルのアップロード**: メイン画面でPDFファイルを選択
2. **Q&A設定**: 生成するQ&Aペアの数を設定（5-20回）
3. **実行開始**: 「実行開始」ボタンをクリック
4. **要約・Q&Aセッションの確認**: 生成された要約とQ&Aを確認
5. **最終レポートの確認**: Markdown形式のレポートを確認・コピー

## AIエージェントについて

### 生徒エージェント
- 好奇心旺盛で知識欲の強い学生役
- 文書の内容について理解を深めるための質問を生成
- セクション順に質問し、必要に応じてフォローアップ質問も実行

### 先生エージェント  
- あらゆる分野に精通した専門家で教育者
- 文書の内容に基づいて詳細でわかりやすい回答を提供
- 専門用語の説明や具体例を交えた丁寧な説明

### 要約・整形エージェント
- 文書の要約と情報整理の専門家
- 文書全体の短い要約を生成
- Q&A内容を整理して最終的なMarkdownレポートを作成

## 制限事項

- PDFファイルのみ対応（最大50MB）
- トークン制限：250,000トークン以内
- Q&A回数：5-20回の範囲
- OpenAI APIキーが必要

## トラブルシューティング

### よくある問題

1. **APIキーエラー**: `.env`ファイルにOpenAI APIキーが正しく設定されているか確認
2. **ファイルサイズエラー**: PDFファイルが50MB以下であることを確認
3. **PDF画像抽出エラー**: macOSの場合は`brew install poppler`でpopplerをインストール
4. **トークン超過**: 文書が長すぎる場合は自動分割されますが、それでも処理できない場合はより短い文書を使用
5. **処理が遅い**: 大きなファイルや多いQ&A数の場合は処理時間が長くなります

### エラー対処法

- アプリケーションエラーが発生した場合は、ページをリフレッシュしてリトライ
- 依存関係のインストールエラーの場合は、Python環境を確認
- 処理中にエラーが発生した場合は、「リセット」ボタンでセッションをリセット

## 開発者向け情報

### 依存関係

主要な依存関係は`requirements.txt`に記載されています：
- streamlit: WebUIフレームワーク
- semantic-kernel: AIエージェント統合
- openai: OpenAI API連携
- PyPDF2: PDF処理
- pdf2image: PDF画像抽出（popplerが必要）
- pillow: 画像処理
- markdown: Markdown処理

**注意**: tiktokenは必須ではありませんが、より正確なトークン数カウントのためにインストールを推奨します。

### カスタマイズ

- プロンプトの修正: `prompts/`ディレクトリ内の`.ini`ファイルを編集
- UI の修正: `ui/`ディレクトリ内のファイルを編集
- エージェントロジックの修正: `agents/`ディレクトリ内のファイルを編集

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。