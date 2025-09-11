from typing import Dict, Any, Optional
from utils.helpers import FileUtils

class InputValidator:
    """入力検証を行うクラス"""
    
    @staticmethod
    def validate_file_upload(file_obj) -> Dict[str, Any]:
        """ファイルアップロードの検証"""
        result = {
            "is_valid": True,
            "error_message": "",
            "warnings": []
        }
        
        if not file_obj:
            result["is_valid"] = False
            result["error_message"] = "ファイルが選択されていません"
            return result
        
        # PDFファイルの検証
        if hasattr(file_obj, 'type'):
            if not file_obj.type == 'application/pdf':
                result["is_valid"] = False
                result["error_message"] = "PDFファイルのみ対応しています"
                return result
        
        # ファイルサイズの検証
        if hasattr(file_obj, 'size'):
            max_size = 50 * 1024 * 1024  # 50MB
            
            if file_obj.size > max_size:
                result["is_valid"] = False
                result["error_message"] = f"ファイルサイズが上限（50MB）を超えています: {FileUtils.format_file_size(file_obj.size)}"
                return result
            
            # 警告レベル（30MB以上）
            warning_size = 30 * 1024 * 1024
            if file_obj.size > warning_size:
                result["warnings"].append("ファイルサイズが大きいため、処理に時間がかかる可能性があります")
        
        return result
    
    @staticmethod
    def validate_qa_settings(qa_turns: int) -> Dict[str, Any]:
        """Q&A設定の検証"""
        result = {
            "is_valid": True,
            "error_message": "",
            "warnings": []
        }
        
        # 型チェック
        if not isinstance(qa_turns, int):
            result["is_valid"] = False
            result["error_message"] = "Q&Aターン数は整数で指定してください"
            return result
        
        # 範囲チェック
        min_turns, max_turns = 5, 20
        if qa_turns < min_turns or qa_turns > max_turns:
            result["is_valid"] = False
            result["error_message"] = f"Q&Aターン数は{min_turns}-{max_turns}の範囲で設定してください"
            return result
        
        # 警告レベル
        if qa_turns > 15:
            result["warnings"].append("Q&Aターン数が多いため、処理時間が長くなる可能性があります")
        
        return result
    
    @staticmethod
    def validate_api_key(api_key: Optional[str]) -> Dict[str, Any]:
        """APIキーの検証"""
        result = {
            "is_valid": True,
            "error_message": ""
        }
        
        if not api_key:
            result["is_valid"] = False
            result["error_message"] = "OpenAI APIキーが設定されていません"
            return result
        
        # 基本的な形式チェック
        if not api_key.startswith('sk-'):
            result["is_valid"] = False
            result["error_message"] = "無効なAPIキー形式です"
            return result
        
        # 長さチェック（概算）
        if len(api_key) < 20:
            result["is_valid"] = False
            result["error_message"] = "APIキーが短すぎます"
            return result
        
        return result