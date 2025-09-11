from typing import Dict, Any, Optional, List
from agents.base_agent import BaseAgent
from services.kernel_service import KernelService
from datetime import datetime

class SummarizerAgent(BaseAgent):
    """要約・整形エージェント - 文書要約と最終レポート生成の役割"""
    
    def __init__(self, kernel_service: KernelService, prompt_version: str = "latest"):
        self.summaries_created = 0
        self.reports_created = 0
        super().__init__("summarizer", kernel_service, prompt_version)
    
    def get_description(self) -> str:
        """エージェントの説明を返す"""
        return "文書の要約と情報整理の専門家。文書要約の生成とQ&A内容の整理・最終レポート作成を行います。"
    
    def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        メッセージを処理（基本的には使用しない）
        
        Args:
            message: 入力メッセージ
            context: コンテキスト情報
            
        Returns:
            処理結果
        """
        return "要約エージェントは特定のタスク用メソッドを使用してください"
    
    def create_document_summary(self, document_content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        文書全体の要約を作成
        
        Args:
            document_content: 文書内容
            context: コンテキスト情報
            
        Returns:
            要約生成用のプロンプト
        """
        prompt_parts = [
            f"【文書内容】\\n{document_content}",
            "",
            "【指示】",
            "上記の文書全体を読んで、以下の要件に従って簡潔で包括的な要約を作成してください：",
            "",
            "1. 文書の主要なテーマや目的を明確にする",
            "2. 重要なポイントを3-5個に絞って整理する", 
            "3. 各ポイントは1-2文で簡潔にまとめる",
            "4. 専門用語は適切に説明を加える",
            "5. 読者が文書全体の概要を素早く理解できるようにする",
            "",
            "要約は以下の形式で出力してください：",
            "## 📋 文書要約",
            "**主要テーマ：** [文書の中心的なテーマ]",
            "",
            "**重要ポイント：**",
            "1. [ポイント1]",
            "2. [ポイント2]", 
            "3. [ポイント3]",
            "...",
            "",
            "要約のみを出力してください。"
        ]
        
        self.summaries_created += 1
        return "\\n".join(prompt_parts)
    
    def create_final_report(self, document_content: str, qa_pairs: List[Dict[str, Any]], summary: str = "") -> str:
        """
        最終マークダウンレポートを作成
        
        Args:
            document_content: 元の文書内容
            qa_pairs: Q&Aペアのリスト
            summary: 事前に作成された要約
            
        Returns:
            最終レポート生成用のプロンプト
        """
        # Q&Aペアを文字列形式に整形
        qa_text = self._format_qa_pairs_for_prompt(qa_pairs)
        
        prompt_parts = [
            f"【元文書】\\n{document_content[:2000]}..." if len(document_content) > 2000 else f"【元文書】\\n{document_content}",
            "",
            f"【文書要約】\\n{summary}" if summary else "",
            "",
            f"【Q&A セッション内容】\\n{qa_text}",
            "",
            "【指示】",
            "上記の情報を基に、以下の構造を持つ包括的なMarkdown形式の最終レポートを作成してください：",
            "",
            "## 構造要件：",
            "1. **タイトルと概要セクション**",
            "   - 文書のタイトルと基本情報",
            "   - 文書の要約（既存の要約を改良・活用）",
            "",
            "2. **Q&A セッション結果**",
            "   - 各Q&Aペアを見やすく整理",
            "   - 質問と回答を適切に構造化",
            "   - 重要な洞察やポイントをハイライト",
            "",
            "3. **主要な学習ポイント**",
            "   - Q&Aから得られた重要な知識をまとめ",
            "   - 実用的な示唆や応用可能な点を抽出",
            "",
            "4. **結論・まとめ**",
            "   - 文書とQ&Aセッションから得られた全体的な理解",
            "   - 今後の学習や応用への示唆",
            "",
            "## フォーマット要件：",
            "- 適切なMarkdown記法を使用",
            "- 見出し、リスト、強調などで構造化",
            "- 読みやすく整理された形式",
            "- 必要に応じて表や引用ブロックを活用",
            "",
            "最終レポート（Markdown形式）のみを出力してください。"
        ]
        
        self.reports_created += 1
        return "\\n".join([part for part in prompt_parts if part])
    
    def _format_qa_pairs_for_prompt(self, qa_pairs: List[Dict[str, Any]]) -> str:
        """Q&AペアをプロンプトでUIに適した形式に整形"""
        if not qa_pairs:
            return "Q&Aペアがありません。"
        
        formatted_pairs = []
        for i, qa in enumerate(qa_pairs, 1):
            question = qa.get('question', '質問なし')
            answer = qa.get('answer', '回答なし')
            
            formatted_pairs.append(f"Q{i}: {question}")
            formatted_pairs.append(f"A{i}: {answer}")
            formatted_pairs.append("---")
        
        return "\\n\\n".join(formatted_pairs)
    
    def create_section_summary(self, section_content: str, qa_pairs: List[Dict[str, Any]]) -> str:
        """
        セクション毎の要約を作成
        
        Args:
            section_content: セクション内容
            qa_pairs: そのセクションのQ&Aペア
            
        Returns:
            セクション要約生成用のプロンプト
        """
        qa_text = self._format_qa_pairs_for_prompt(qa_pairs)
        
        prompt_parts = [
            f"【セクション内容】\\n{section_content}",
            "",
            f"【このセクションのQ&A】\\n{qa_text}",
            "",
            "【指示】",
            "上記のセクション内容とQ&Aを基に、このセクションの要点をまとめてください：",
            "",
            "1. セクションの主要な内容を2-3文で要約",
            "2. Q&Aから明らかになった重要なポイントを整理",
            "3. このセクションで学べる主要な知識や概念をハイライト",
            "",
            "要約のみを出力してください。"
        ]
        
        return "\\n".join(prompt_parts)
    
    def improve_qa_formatting(self, qa_pairs: List[Dict[str, Any]]) -> str:
        """
        Q&Aペアの整形・改善
        
        Args:
            qa_pairs: 整形するQ&Aペア
            
        Returns:
            整形後のQ&A
        """
        qa_text = self._format_qa_pairs_for_prompt(qa_pairs)
        
        prompt_parts = [
            f"【現在のQ&A内容】\\n{qa_text}",
            "",
            "【指示】",
            "上記のQ&A内容を以下の要件に従って整形・改善してください：",
            "",
            "1. 質問文を簡潔で明確にする",
            "2. 回答の構造を整理し、読みやすくする", 
            "3. 重要なポイントを適切に強調する",
            "4. 必要に応じて関連性の高いQ&A同士をグループ化する",
            "5. Markdown記法を使用して見やすく整形する",
            "",
            "整形後のQ&A（Markdown形式）のみを出力してください。"
        ]
        
        return "\\n".join(prompt_parts)
    
    def create_executive_summary(self, full_report: str) -> str:
        """
        エグゼクティブサマリーを作成
        
        Args:
            full_report: 完全なレポート内容
            
        Returns:
            エグゼクティブサマリー生成用のプロンプト
        """
        prompt_parts = [
            f"【完全レポート】\\n{full_report}",
            "",
            "【指示】",
            "上記のレポート全体を基に、エグゼクティブサマリーを作成してください：",
            "",
            "1. 最も重要なポイントを3-5個に絞る",
            "2. 各ポイントを1-2文で簡潔にまとめる",
            "3. ビジネスや実用面での示唆があれば含める",
            "4. 2-3分で読める長さに収める",
            "",
            "エグゼクティブサマリーのみを出力してください。"
        ]
        
        return "\\n".join(prompt_parts)
    
    def get_status(self) -> Dict[str, Any]:
        """現在の状態を取得"""
        return {
            "summaries_created": self.summaries_created,
            "reports_created": self.reports_created,
            "timestamp": datetime.now().isoformat()
        }