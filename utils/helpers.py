import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re
import math

class TextUtils:
    """テキスト処理のユーティリティ"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """テキストをクリーニング"""
        # 余分な空白を削除
        text = re.sub(r'\s+', ' ', text)
        # 改行を正規化
        text = re.sub(r'\n\s*\n', '\n\n', text)
        # 先頭・末尾の空白を削除
        text = text.strip()
        return text
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """テキストを指定された長さで切り詰める"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def extract_key_phrases(text: str, max_phrases: int = 5) -> List[str]:
        """テキストからキーフレーズを抽出（簡易版）"""
        # 簡易的な実装：長い単語を抽出
        words = re.findall(r'\b\w{4,}\b', text)
        # 頻度でソート
        from collections import Counter
        word_freq = Counter(words)
        return [word for word, _ in word_freq.most_common(max_phrases)]
    
    @staticmethod
    def format_markdown_table(data: List[Dict[str, Any]], columns: List[str]) -> str:
        """データをMarkdownテーブル形式に変換"""
        if not data or not columns:
            return ""
        
        # ヘッダー
        header = "|" + "|".join(columns) + "|"
        separator = "|" + "|".join(["---"] * len(columns)) + "|"
        
        # データ行
        rows = []
        for row in data:
            row_data = [str(row.get(col, "")) for col in columns]
            rows.append("|" + "|".join(row_data) + "|")
        
        return "\n".join([header, separator] + rows)

class FileUtils:
    """ファイル操作のユーティリティ"""
    
    @staticmethod
    def ensure_directory(directory_path: str):
        """ディレクトリが存在しない場合は作成"""
        os.makedirs(directory_path, exist_ok=True)
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """ファイルサイズを取得（バイト）"""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """ファイルサイズを人間が読みやすい形式に変換"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

class ValidationUtils:
    """検証関連のユーティリティ"""
    
    @staticmethod
    def validate_pdf_file(file_obj) -> Dict[str, Any]:
        """PDFファイルの検証"""
        result = {
            "is_valid": True,
            "error_message": "",
            "file_info": {}
        }
        
        try:
            # ファイルタイプチェック
            if hasattr(file_obj, 'type'):
                if file_obj.type != 'application/pdf':
                    result["is_valid"] = False
                    result["error_message"] = "PDFファイルのみ対応しています"
                    return result
            
            # ファイルサイズチェック（50MB制限）
            if hasattr(file_obj, 'size'):
                max_size = 50 * 1024 * 1024  # 50MB
                if file_obj.size > max_size:
                    result["is_valid"] = False
                    result["error_message"] = f"ファイルサイズが50MBを超えています ({FileUtils.format_file_size(file_obj.size)})"
                    return result
                
                result["file_info"]["size"] = file_obj.size
        
        except Exception as e:
            result["is_valid"] = False
            result["error_message"] = f"ファイル検証中にエラーが発生しました: {str(e)}"
        
        return result

def clamp(n: int, min_v: int, max_v: int) -> int:
    return max(min_v, min(n, max_v))

def estimate_tokens(text: str, model: Optional[str] = None) -> int:
    """トークン数を概算"""
    try:
        import tiktoken
        enc_names = ["o200k_base", "cl100k_base", "p50k_base", "gpt2"]
        for name in enc_names:
            try:
                enc = tiktoken.get_encoding(name)
                return len(enc.encode(text or ""))
            except Exception:
                continue
        return max(1, len(text) // 4)
    except Exception:
        return max(1, len(text) // 4)

def bytes_to_mb(size_bytes: int) -> float:
    return size_bytes / 1_000_000.0
