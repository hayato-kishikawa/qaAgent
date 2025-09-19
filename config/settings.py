import os
from dotenv import load_dotenv
from pathlib import Path

# .envファイルから環境変数を読み込み
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def get_openai_api_key():
    """OpenAI APIキーを取得（StreamlitとEnvの両方をチェック）"""
    try:
        import streamlit as st
        # Streamlit secretsから取得を試行
        api_key = st.secrets.get("OPENAI_API_KEY")
        if api_key and api_key != "your-openai-api-key-here":
            return api_key
    except:
        pass
    # 環境変数から取得
    return os.getenv("OPENAI_API_KEY")

class Settings:
    """アプリケーション設定クラス"""

    # API設定
    OPENAI_API_KEY = get_openai_api_key()
    
    # GPTモデル設定
    GPT_MODEL = "gpt-4o"
    
    # トークン制限
    MAX_TOKENS = 250000
    
    # ファイル設定
    MAX_FILE_SIZE_MB = 50
    ALLOWED_FILE_TYPES = ["pdf"]
    
    # Q&A設定
    MIN_QA_TURNS = 5
    MAX_QA_TURNS = 20
    MAX_FOLLOWUP_QUESTIONS = 3
    
    # Streamlit設定
    PAGE_TITLE = "StudyMate AI - 文書学習アシスタント"
    PAGE_ICON = "🎓"
    LAYOUT = "wide"
    
    # プロンプト設定
    PROMPT_VERSION = "latest"
    
    @classmethod
    def validate_api_key(cls):
        """OpenAI APIキーの検証"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY環境変数が設定されていません")
        return True
    
    @classmethod
    def get_file_size_limit_bytes(cls):
        """ファイルサイズ制限をバイトで取得"""
        return cls.MAX_FILE_SIZE_MB * 1024 * 1024