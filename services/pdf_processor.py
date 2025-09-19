import PyPDF2
import pdf2image
import io
import base64
from typing import List, Dict, Tuple, Optional
from PIL import Image
from config.settings import Settings

class PDFProcessor:
    """PDF文書の処理を行うクラス"""
    
    def __init__(self):
        self.settings = Settings()
        # tiktokenが利用できない場合の代替処理
        self.encoding = None
        try:
            import tiktoken
            self.encoding = tiktoken.encoding_for_model(self.settings.GPT_MODEL)
        except ImportError:
            pass
    
    def validate_pdf(self, pdf_file) -> bool:
        """
        PDFファイルの検証
        
        Args:
            pdf_file: アップロードされたPDFファイル
            
        Returns:
            検証結果
        """
        # ファイルサイズチェック
        if hasattr(pdf_file, 'size'):
            if pdf_file.size > self.settings.get_file_size_limit_bytes():
                raise ValueError(f"ファイルサイズが{self.settings.MAX_FILE_SIZE_MB}MBを超えています")
        
        # ファイル形式チェック
        if hasattr(pdf_file, 'type'):
            if pdf_file.type != 'application/pdf':
                raise ValueError("PDFファイルのみ対応しています")
        
        return True
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """
        PDFからテキストを抽出
        
        Args:
            pdf_file: PDFファイル
            
        Returns:
            抽出されたテキスト
        """
        try:
            # PDF読み込み
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text_content = ""
            
            # 各ページからテキストを抽出
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    text_content += f"\\n--- ページ {page_num + 1} ---\\n"
                    text_content += page_text + "\\n"
            
            return text_content
        
        except Exception as e:
            raise Exception(f"PDFテキスト抽出エラー: {str(e)}")
    
    def extract_images_from_pdf(self, pdf_file) -> List[Image.Image]:
        """
        PDFから画像を抽出（Vision機能用）
        
        Args:
            pdf_file: PDFファイル
            
        Returns:
            抽出された画像のリスト
        """
        try:
            # PDFを画像に変換
            import platform
            
            # Windowsの場合、popplerパスを手動で設定を試行
            if platform.system() == "Windows":
                try:
                    images = pdf2image.convert_from_bytes(pdf_file.read())
                except Exception as e:
                    # Windowsでpopplerパスエラーの場合のフォールバック
                    import shutil
                    poppler_path = None
                    
                    # 一般的なpopplerのインストール場所を確認
                    possible_paths = [
                        r"C:\poppler\Release-25.07.0-0\Library\bin",  # 手動インストール時の実際のパス
                        r"C:\Program Files\poppler-24.02.0\Library\bin",  # Chocolatey版
                        r"C:\Program Files\poppler\Library\bin",
                        r"C:\Program Files (x86)\poppler\Library\bin", 
                        r"C:\poppler\Library\bin",
                        r"C:\tools\poppler\Library\bin"
                    ]
                    
                    for path in possible_paths:
                        if os.path.exists(path):
                            poppler_path = path
                            break
                    
                    if poppler_path:
                        images = pdf2image.convert_from_bytes(pdf_file.read(), poppler_path=poppler_path)
                    else:
                        raise Exception(f"PDF画像抽出エラー: Popplerが見つかりません。READMEを参照してPopplerをインストールしてください。原因: {str(e)}")
            else:
                images = pdf2image.convert_from_bytes(pdf_file.read())
                
            return images
        
        except Exception as e:
            if "poppler" in str(e).lower() or "pdftoppm" in str(e).lower():
                # Streamlit Community Cloudなど、popplerが利用できない環境では画像処理をスキップ
                import streamlit as st
                st.warning("⚠️ PDF画像処理機能が利用できません。テキスト抽出のみ実行します。")
                return []  # 空の画像リストを返す
            else:
                raise Exception(f"PDF画像抽出エラー: {str(e)}")
    
    def images_to_base64(self, images: List[Image.Image]) -> List[str]:
        """
        画像をbase64エンコード
        
        Args:
            images: PIL画像のリスト
            
        Returns:
            base64エンコードされた画像のリスト
        """
        base64_images = []
        
        for image in images:
            # 画像をバイトに変換
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            img_bytes = buffer.getvalue()
            
            # base64エンコード
            base64_string = base64.b64encode(img_bytes).decode('utf-8')
            base64_images.append(base64_string)
        
        return base64_images
    
    def count_tokens(self, text: str) -> int:
        """
        テキストのトークン数をカウント
        
        Args:
            text: テキスト
            
        Returns:
            トークン数
        """
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # 簡易的な概算（4文字≈1トークン）
            return max(1, len(text) // 4)
    
    def split_text_by_token_limit(self, text: str, max_tokens: Optional[int] = None) -> List[str]:
        """
        トークン数制限に基づいてテキストを分割
        
        Args:
            text: 分割するテキスト
            max_tokens: 最大トークン数（Noneの場合は設定から取得）
            
        Returns:
            分割されたテキストのリスト
        """
        if max_tokens is None:
            max_tokens = self.settings.MAX_TOKENS
        
        # トークン数をチェック
        total_tokens = self.count_tokens(text)
        
        if total_tokens <= max_tokens:
            return [text]
        
        # テキストを段落単位で分割
        paragraphs = text.split('\\n\\n')
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for paragraph in paragraphs:
            paragraph_tokens = self.count_tokens(paragraph)
            
            # 現在のチャンクに追加できるかチェック
            if current_tokens + paragraph_tokens <= max_tokens:
                if current_chunk:
                    current_chunk += "\\n\\n" + paragraph
                else:
                    current_chunk = paragraph
                current_tokens += paragraph_tokens
            else:
                # 現在のチャンクを保存
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 新しいチャンクを開始
                if paragraph_tokens <= max_tokens:
                    current_chunk = paragraph
                    current_tokens = paragraph_tokens
                else:
                    # 段落自体が長すぎる場合は文単位で分割
                    sentences = paragraph.split('。')
                    for sentence in sentences:
                        sentence_tokens = self.count_tokens(sentence)
                        if current_tokens + sentence_tokens <= max_tokens:
                            current_chunk += sentence + "。"
                            current_tokens += sentence_tokens
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = sentence + "。"
                            current_tokens = sentence_tokens
        
        # 最後のチャンクを追加
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def process_pdf(self, pdf_file) -> Dict[str, any]:
        """
        PDFファイルの完全処理

        Args:
            pdf_file: PDFファイル

        Returns:
            処理結果の辞書
        """
        # 検証
        self.validate_pdf(pdf_file)

        # 生のPDFデータを保存（PDFビューアー用）
        pdf_file.seek(0)
        raw_content = pdf_file.read()

        # ファイルポインタを先頭に戻す
        pdf_file.seek(0)

        # テキスト抽出
        text_content = self.extract_text_from_pdf(pdf_file)

        # 画像抽出（ファイルを先頭に戻す）
        pdf_file.seek(0)
        try:
            images = self.extract_images_from_pdf(pdf_file)
            base64_images = self.images_to_base64(images) if images else []
        except Exception:
            # 画像処理でエラーが発生してもテキスト処理は継続
            images = []
            base64_images = []

        # トークン数チェック
        total_tokens = self.count_tokens(text_content)

        # トークン制限チェックと分割
        text_chunks = []
        if total_tokens > self.settings.MAX_TOKENS:
            text_chunks = self.split_text_by_token_limit(text_content)
        else:
            text_chunks = [text_content]

        return {
            "text_content": text_content,
            "text_chunks": text_chunks,
            "images": base64_images,
            "total_tokens": total_tokens,
            "page_count": len(images),
            "is_split": len(text_chunks) > 1,
            "raw_content": raw_content,  # PDFビューアー用の生データ
            "input_type": "pdf",  # 入力タイプを明示
            "filename": getattr(pdf_file, 'name', 'document.pdf')  # ファイル名を取得
        }