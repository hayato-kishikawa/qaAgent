from typing import List, Dict, Any, Optional
import os
from openai import OpenAI
import streamlit as st

class OpenAIService:
    """OpenAI APIとの連携を管理するサービス"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
    
    @st.cache_data(ttl=300)  # 5分間キャッシュ
    def get_available_models(_self) -> List[Dict[str, Any]]:
        """利用可能なOpenAIモデルの一覧を取得"""
        if not _self.client:
            return []
        
        try:
            models = _self.client.models.list()
            
            # GPTモデルのみをフィルタリング
            gpt_models = []
            for model in models:
                model_id = model.id
                # GPTモデル、o1モデル、GPT-4oモデルなどをフィルタリング
                if any(prefix in model_id.lower() for prefix in ['gpt-', 'o1', 'chatgpt']):
                    gpt_models.append({
                        'id': model_id,
                        'name': _self._format_model_name(model_id),
                        'category': _self._get_model_category(model_id)
                    })
            
            # カテゴリ別にソート
            gpt_models.sort(key=lambda x: (x['category'], x['name']))
            return gpt_models
            
        except Exception as e:
            st.error(f"モデル一覧の取得に失敗しました: {str(e)}")
            return []
    
    def _format_model_name(self, model_id: str) -> str:
        """モデルIDを表示用の名前に変換"""
        # 表示用の名前変換
        name_mapping = {
            'gpt-4o': 'GPT-4o (最新)',
            'gpt-4o-mini': 'GPT-4o Mini (高速・低コスト)',
            'gpt-4-turbo': 'GPT-4 Turbo',
            'gpt-4': 'GPT-4',
            'gpt-3.5-turbo': 'GPT-3.5 Turbo',
            'o1-preview': 'o1-preview (推論特化)',
            'o1-mini': 'o1-mini (推論・高速)',
        }
        
        return name_mapping.get(model_id, model_id)
    
    def _get_model_category(self, model_id: str) -> str:
        """モデルのカテゴリを取得"""
        if 'o1' in model_id:
            return '1_reasoning'  # 推論特化モデル
        elif 'gpt-4o' in model_id:
            return '2_latest'     # 最新モデル
        elif 'gpt-4' in model_id:
            return '3_advanced'   # 高性能モデル
        elif 'gpt-3.5' in model_id:
            return '4_standard'   # 標準モデル
        else:
            return '5_other'      # その他
    
    def get_default_model(self) -> str:
        """デフォルトモデルを取得"""
        models = self.get_available_models()
        
        # 利用可能なモデルから優先順位で選択
        preferred_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo']
        
        for preferred in preferred_models:
            for model in models:
                if model['id'] == preferred:
                    return preferred
        
        # 利用可能なモデルがある場合は最初のものを返す
        if models:
            return models[0]['id']
        
        # フォールバック
        return 'gpt-4o-mini'
    
    def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """APIキーの有効性を検証"""
        result = {
            "is_valid": False,
            "error_message": "",
            "models_count": 0
        }
        
        try:
            test_client = OpenAI(api_key=api_key)
            models = test_client.models.list()
            
            # GPTモデルの数をカウント
            gpt_count = sum(1 for model in models if 'gpt' in model.id.lower())
            
            if gpt_count > 0:
                result["is_valid"] = True
                result["models_count"] = gpt_count
            else:
                result["error_message"] = "GPTモデルへのアクセス権限がありません"
            
        except Exception as e:
            result["error_message"] = f"APIキーの検証に失敗: {str(e)}"
        
        return result