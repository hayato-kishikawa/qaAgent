from typing import Dict, Any, Optional
import re


class TextProcessor:
    """テキスト処理サービス"""

    @staticmethod
    def process_text(text_content: str) -> Dict[str, Any]:
        """テキストを処理してPDF処理と同様の形式に変換"""
        try:
            # テキストの基本情報を取得
            text_info = TextProcessor._analyze_text(text_content)

            # PDF処理と同様の形式で返す
            result = {
                'text_content': text_content,
                'page_count': 1,  # テキスト貼り付けは常に1ページ扱い
                'total_tokens': text_info['estimated_tokens'],
                'char_count': text_info['char_count'],
                'word_count': text_info['word_count'],
                'is_split': False,  # テキストは分割しない
                'source_type': 'text',
                'input_type': 'text',  # ビューアータブで適切に表示するため
                'filename': 'テキスト入力'  # ファイル名を設定
            }

            return result

        except Exception as e:
            raise Exception(f"テキスト処理エラー: {str(e)}")

    @staticmethod
    def _analyze_text(text: str) -> Dict[str, Any]:
        """テキストを分析して基本情報を取得"""
        # 基本的な文字数・単語数カウント
        char_count = len(text)

        # 単語数（日本語対応）
        # 英語の単語 + 日本語の文字（ひらがな、カタカナ、漢字）
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text))

        # 概算単語数（日本語は文字数の1/2を単語として計算）
        word_count = english_words + (japanese_chars // 2)

        # トークン数の概算（単語数 × 1.3）
        estimated_tokens = int(word_count * 1.3)

        return {
            'char_count': char_count,
            'word_count': word_count,
            'estimated_tokens': estimated_tokens,
            'language': TextProcessor._detect_language(text)
        }

    @staticmethod
    def _detect_language(text: str) -> str:
        """簡単な言語判定"""
        japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))

        if japanese_chars > english_chars:
            return 'japanese'
        elif english_chars > 0:
            return 'english'
        else:
            return 'unknown'

    @staticmethod
    def validate_text(text: str) -> Dict[str, Any]:
        """テキストの妥当性を検証"""
        if not text or not text.strip():
            return {
                'is_valid': False,
                'error_message': 'テキストが入力されていません。'
            }

        # 最小文字数チェック
        if len(text.strip()) < 100:
            return {
                'is_valid': False,
                'error_message': 'テキストが短すぎます。100文字以上入力してください。'
            }

        # 最大文字数チェック（250,000トークン相当）
        max_chars = 500000  # 概算
        if len(text) > max_chars:
            return {
                'is_valid': False,
                'error_message': f'テキストが長すぎます。{max_chars:,}文字以下にしてください。'
            }

        return {
            'is_valid': True,
            'message': 'テキストの検証が完了しました。'
        }