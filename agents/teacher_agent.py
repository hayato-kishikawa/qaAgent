from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from services.kernel_service import KernelService

class TeacherAgent(BaseAgent):
    """先生エージェント - 質問に回答する役割"""
    
    def __init__(self, kernel_service: KernelService, prompt_version: str = "latest"):
        self.answers_provided = 0
        self.document_content = ""
        super().__init__("teacher", kernel_service, prompt_version)
    
    def get_description(self) -> str:
        """エージェントの説明を返す"""
        return "あらゆる分野に精通した専門家で教育者。文書の内容に基づいて詳細でわかりやすい回答を提供します。"
    
    def set_document_content(self, content: str):
        """参照する文書内容を設定"""
        self.document_content = content
    
    def process_message(self, question: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        質問に対する回答を生成
        
        Args:
            question: 質問内容
            context: コンテキスト情報
            
        Returns:
            回答プロンプト
        """
        # コンテキストから情報を取得
        if context:
            document_content = context.get("document_content", self.document_content)
            section_content = context.get("current_section_content", "")
            previous_qa = context.get("previous_qa", [])
        else:
            document_content = self.document_content
            section_content = ""
            previous_qa = []
        
        # 回答生成のためのプロンプトを構築
        answer_prompt = self._build_answer_prompt(
            question,
            document_content,
            section_content,
            previous_qa
        )
        
        self.answers_provided += 1
        return answer_prompt
    
    def _build_answer_prompt(self, question: str, document_content: str, section_content: str, previous_qa: list) -> str:
        """回答生成用のプロンプトを構築"""
        prompt_parts = []
        
        # 質問
        prompt_parts.append(f"【質問】\\n{question}")
        
        # 文書全体の情報
        if document_content:
            prompt_parts.append(f"【参考文書】\\n{document_content}")
        
        # 現在のセクション情報
        if section_content:
            prompt_parts.append(f"【関連セクション】\\n{section_content}")
        
        # 過去のQ&A履歴（参考程度）
        if previous_qa:
            prompt_parts.append("【これまでの議論の流れ（参考）】")
            for i, qa in enumerate(previous_qa[-2:], 1):  # 直近2つのQ&A
                prompt_parts.append(f"Q{i}: {qa.get('question', '')}")
                prompt_parts.append(f"A{i}: {qa.get('answer', '')[:150]}...")
        
        # 回答指示
        prompt_parts.append("\\n【指示】")
        prompt_parts.append("上記の質問に対して、参考文書の内容に基づいた正確で詳細な回答を提供してください。")
        prompt_parts.append("以下の点に注意してください：")
        prompt_parts.append("1. 文書に記載されている内容を正確に引用・参照する")
        prompt_parts.append("2. 専門用語は適切に説明し、具体例を交える")
        prompt_parts.append("3. 文書に明記されていない内容については、その旨を明確にする")
        prompt_parts.append("4. わかりやすく丁寧な説明を心がける")
        prompt_parts.append("\\n回答のみを出力してください。")
        
        return "\\n\\n".join(prompt_parts)
    
    def provide_detailed_explanation(self, topic: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        特定のトピックについて詳細な説明を提供
        
        Args:
            topic: 説明するトピック
            context: コンテキスト情報
            
        Returns:
            詳細説明のプロンプト
        """
        prompt_parts = [
            f"【説明対象】\\n{topic}",
            "",
            f"【参考文書】\\n{self.document_content}" if self.document_content else "",
            "",
            "【指示】",
            "上記のトピックについて、参考文書の内容を基に詳細で理解しやすい説明を提供してください。",
            "基礎的な概念から応用まで、段階的に説明してください。",
            "",
            "説明のみを出力してください。"
        ]
        
        return "\\n".join([part for part in prompt_parts if part])
    
    def answer_followup(self, original_question: str, original_answer: str, followup_question: str) -> str:
        """
        フォローアップ質問に回答
        
        Args:
            original_question: 元の質問
            original_answer: 元の回答
            followup_question: フォローアップ質問
            
        Returns:
            フォローアップ回答のプロンプト
        """
        prompt_parts = [
            f"【元の質問】\\n{original_question}",
            "",
            f"【元の回答】\\n{original_answer}",
            "",
            f"【フォローアップ質問】\\n{followup_question}",
            "",
            f"【参考文書】\\n{self.document_content}" if self.document_content else "",
            "",
            "【指示】",
            "上記のフォローアップ質問に対して、元の質問と回答を踏まえつつ、",
            "さらに詳細で具体的な回答を提供してください。",
            "実用的な観点や具体例を含めて説明してください。",
            "",
            "回答のみを出力してください。"
        ]
        
        return "\\n".join([part for part in prompt_parts if part])
    
    def evaluate_answer_complexity(self, answer: str) -> float:
        """
        回答の専門度を評価
        
        Args:
            answer: 評価する回答
            
        Returns:
            専門度スコア（0.0-1.0）
        """
        # 専門用語や複雑な概念の指標
        complex_indicators = [
            # 一般的な専門用語指標
            "アルゴリズム", "フレームワーク", "アーキテクチャ", "プロトコル",
            "インターフェース", "実装", "メソッド", "クラス", "オブジェクト",
            # 学術的表現
            "理論", "仮説", "分析", "評価", "検証", "実証", "考察",
            # 専門分野特有の表現
            "システム", "プロセス", "メカニズム", "構造", "機能",
            # 抽象的概念
            "概念", "原理", "法則", "規則", "基準", "指標"
        ]
        
        # 長い文章や複雑な構文の指標
        sentence_complexity = [
            "すなわち", "つまり", "したがって", "その結果", "一方で", 
            "しかしながら", "加えて", "さらに", "具体的には"
        ]
        
        # カウント
        complex_terms = sum(1 for term in complex_indicators if term in answer)
        complex_sentences = sum(1 for phrase in sentence_complexity if phrase in answer)
        
        # 文字数による判定
        length_score = min(len(answer) / 500.0, 1.0)  # 500文字で最大
        
        # 総合スコア
        total_score = (
            (complex_terms / 10.0) * 0.4 +  # 専門用語の重み
            (complex_sentences / 5.0) * 0.3 +  # 複雑な文章の重み
            length_score * 0.3  # 長さの重み
        )
        
        return min(total_score, 1.0)
    
    def get_status(self) -> Dict[str, Any]:
        """現在の状態を取得"""
        return {
            "answers_provided": self.answers_provided,
            "has_document": bool(self.document_content),
            "document_length": len(self.document_content) if self.document_content else 0
        }