from typing import Optional, Dict, Any
from .base_agent import BaseAgent

class InitialSummarizerAgent(BaseAgent):
    """
    初期要約専用エージェント
    文書の全体像を素早く把握するための要約を生成
    """
    
    def __init__(self, kernel_service):
        super().__init__("initial_summarizer", kernel_service)
        self.document_content = ""
    
    def set_document_content(self, content: str):
        """文書内容を設定"""
        self.document_content = content
    
    def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        初期要約のためのメッセージを処理
        
        Args:
            message: 入力メッセージ（使用しない）
            context: コンテキスト情報
            
        Returns:
            初期要約生成のプロンプト
        """
        document_content = context.get("document_content", self.document_content) if context else self.document_content
        
        if not document_content:
            return "文書が提供されていません。"
        
        return self._build_initial_summary_prompt(document_content)
    
    def _build_initial_summary_prompt(self, document_content: str) -> str:
        """初期要約用のプロンプトを構築"""
        prompt_parts = [
            "【文書内容】",
            f"{document_content[:5000]}...",  # 最初の5000文字を使用
            "",
            "【指示】",
            "この文書の内容について、読者が全体像を素早く把握できるような要約を作成してください。",
            "",
            "要約のポイント：",
            "1. 3-5段落程度の簡潔な要約",
            "2. 文書の主要なテーマと論点を明確に",
            "3. 重要なキーワードや概念を含める",
            "4. 読みやすく分かりやすい文章で",
            "5. 専門用語は最小限に抑える",
            "",
            "要約のみを出力してください。"
        ]
        
        return "\\n".join(prompt_parts)
    
    def create_document_summary(self, document_content: str) -> str:
        """
        文書要約を作成（外部インターフェース）
        
        Args:
            document_content: 文書内容
            
        Returns:
            要約生成プロンプト
        """
        return self._build_initial_summary_prompt(document_content)
    
    def get_description(self) -> str:
        """エージェントの説明を返す"""
        return "文書の全体像を素早く把握するための初期要約を生成するエージェント"