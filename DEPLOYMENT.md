# Streamlit Community Cloud デプロイメント手順

## 🚀 デプロイメント手順

### 1. GitHubリポジトリの準備

このリポジトリをGitHubにプッシュします：

```bash
git add .
git commit -m "Add Streamlit Community Cloud deployment configuration"
git push origin feature/prompt-editor
```

### 2. Streamlit Community Cloudでのアプリ作成

1. [Streamlit Community Cloud](https://share.streamlit.io/)にアクセス
2. GitHubアカウントでサインイン
3. "New app"をクリック
4. Repository: `hayato-kishikawa/qaAgent`
5. Branch: `feature/prompt-editor` （または`main`）
6. Main file path: `app.py`
7. App URL: 任意の名前を設定

### 3. シークレット設定

Streamlit Community Cloudのアプリダッシュボードで「⚙️ Settings」→「🔐 Secrets」を選択し、以下を設定：

```toml
# OpenAI API Key (必須)
OPENAI_API_KEY = "sk-your-actual-openai-api-key"

# アプリケーションパスワード (任意)
APP_PASSWORD = "your-secure-password"
```

### 4. デプロイメント確認

- アプリが自動的にデプロイされます
- 初回デプロイには数分かかる場合があります
- ログで依存関係のインストール状況を確認できます

## 🔐 セキュリティ設定

### パスワード認証

- デフォルトパスワード: `qaAgent2024`
- カスタムパスワード: `APP_PASSWORD`でSecrets設定
- パスワードは必ずセキュアなものに変更してください

### 環境変数

以下の環境変数が設定可能です：

- `OPENAI_API_KEY`: OpenAI APIキー（必須）
- `APP_PASSWORD`: アプリアクセスパスワード（任意）

## 📋 必要なファイル

デプロイメントに必要なファイルは以下の通りです：

```
qaAgent/
├── app.py                     # メインアプリケーション
├── auth.py                    # 認証モジュール
├── requirements.txt           # 依存関係
├── .streamlit/
│   └── secrets.toml          # ローカル開発用（gitignoreされる）
├── config/
├── services/
├── agents/
├── ui/
├── prompts/
└── utils/
```

## ⚠️ 注意事項

### 制限事項

1. **リソース制限**: Community Cloudには計算リソースの制限があります
2. **タイムアウト**: 長時間の処理はタイムアウトする場合があります
3. **ファイルアップロード**: 大きなPDFファイルは処理に時間がかかります

### 推奨事項

1. **API使用量の監視**: OpenAI APIの使用量を定期的に確認
2. **パスワードの定期変更**: セキュリティのため定期的にパスワードを変更
3. **ログの確認**: エラーやパフォーマンス問題がないか定期的に確認

## 🔧 トラブルシューティング

### よくある問題

1. **依存関係エラー**
   - `requirements.txt`の内容を確認
   - Streamlitのログでエラー詳細を確認

2. **API接続エラー**
   - `OPENAI_API_KEY`が正しく設定されているか確認
   - APIキーの有効性と残高を確認

3. **認証エラー**
   - `APP_PASSWORD`が正しく設定されているか確認
   - ブラウザのキャッシュをクリア

### パフォーマンス最適化

1. **処理時間短縮**
   - Q&A回数を適切に設定
   - 大きなPDFファイルは事前に分割

2. **メモリ使用量削減**
   - 不要なセッション状態をクリア
   - 定期的にアプリを再起動

## 📞 サポート

問題が発生した場合：

1. Streamlit Community Cloudのログを確認
2. GitHubのIssuesで報告
3. READMEのトラブルシューティングセクションを参照

## 🔄 更新手順

アプリケーションを更新する場合：

1. ローカルで変更をコミット
2. GitHubにプッシュ
3. Streamlit Community Cloudが自動的に再デプロイ
4. デプロイメントログで成功を確認