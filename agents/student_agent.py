from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from services.kernel_service import KernelService

class StudentAgent(BaseAgent):
    """生徒エージェント - 質問を生成する役割"""
    
    def __init__(self, kernel_service: KernelService, prompt_version: str = "latest"):
        self.questions_asked = 0
        self.current_section = 0
        self.document_sections = []
        super().__init__("student", kernel_service, prompt_version)
    
    def get_description(self) -> str:
        """エージェントの説明を返す"""
        return "好奇心旺盛で知識欲の強い学生。文書の内容について理解を深めるための質問を生成します。"
    
    def set_document_sections(self, sections: list):
        """文書のセクション分割を設定"""
        self.document_sections = sections
        self.current_section = 0
        self.questions_asked = 0
    
    def get_current_section(self) -> str:
        """現在のセクションを取得"""
        if self.current_section < len(self.document_sections):
            return self.document_sections[self.current_section]
        return ""
    
    def move_to_next_section(self):
        """次のセクションに移動"""
        self.current_section += 1
        
    def has_more_sections(self) -> bool:
        """まだ質問すべきセクションがあるか"""
        return self.current_section < len(self.document_sections)
    
    def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        メッセージを処理して質問を生成
        
        Args:
            message: 入力メッセージ
            context: コンテキスト情報
            
        Returns:
            生成された質問
        """
        # コンテキストから情報を取得
        if context:
            document_content = context.get("document_content", "")
            current_section_content = context.get("current_section_content", "")
            previous_qa = context.get("previous_qa", [])
        else:
            document_content = ""
            current_section_content = self.get_current_section()
            previous_qa = []
        
        # 質問生成のためのプロンプトを構築
        target_keyword = context.get("target_keyword") if context else None
        question_prompt = self._build_question_prompt(
            document_content, 
            current_section_content, 
            previous_qa,
            target_keyword
        )
        
        return question_prompt
    
    def _build_question_prompt(self, document_content: str, section_content: str, previous_qa: list, target_keyword: str = None) -> str:
        """質問生成用のプロンプトを構築"""
        prompt_parts = []
        
        # 文書全体の情報
        if document_content:
            prompt_parts.append(f"【文書全体】\\n{document_content[:1000]}...")
        
        # 現在のセクション
        if section_content:
            prompt_parts.append(f"【現在注目すべきセクション（セクション{self.current_section + 1}）】\\n{section_content}")
        
        # 過去のQ&A履歴
        if previous_qa:
            prompt_parts.append("【これまでの質問と回答の履歴】")
            for i, qa in enumerate(previous_qa[-3:], 1):  # 直近3つのQ&Aのみ表示
                prompt_parts.append(f"Q{i}: {qa.get('question', '')}")
                prompt_parts.append(f"A{i}: {qa.get('answer', '')[:200]}...")
        
        # 質問指示
        prompt_parts.append("\\n【指示】")
        
        if target_keyword:
            # 単語指定がある場合の特別な指示
            prompt_parts.append(f"重要単語「{target_keyword}」に関する質問を生成してください。")
            prompt_parts.append(f"この単語が文書内でどのような文脈で使われ、どのような意味や重要性を持つかについて、")
            prompt_parts.append("理解を深めるための具体的な質問を1つだけ生成してください。")
            prompt_parts.append("過去の質問と重複しないよう注意してください。")
        else:
            # 通常の質問生成指示
            prompt_parts.append(f"上記の「現在注目すべきセクション（セクション{self.current_section + 1}）」の内容について、")
            prompt_parts.append("理解を深めるための質問を1つだけ生成してください。")
            prompt_parts.append("過去の質問と重複しないよう注意し、そのセクションの重要なポイントに焦点を当ててください。")
        
        prompt_parts.append("\\n質問のみを出力してください。")
        
        return "\\n\\n".join(prompt_parts)
    
    def generate_followup_question(self, previous_answer: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        フォローアップ質問を生成
        
        Args:
            previous_answer: 前回の回答
            context: コンテキスト情報
            
        Returns:
            フォローアップ質問
        """
        prompt_parts = [
            "【前回の回答】",
            previous_answer,
            "",
            "【指示】",
            "上記の回答について、さらに理解を深めるためのフォローアップ質問を1つ生成してください。",
            "専門的な内容をより具体的に、または実用的な観点から質問してください。",
            "",
            "質問のみを出力してください。"
        ]
        
        return "\\n".join(prompt_parts)
    
    def should_ask_followup(self, answer: str, complexity_threshold: float = 0.7) -> bool:
        """
        フォローアップ質問をすべきか判定
        
        Args:
            answer: 回答内容
            complexity_threshold: 専門度の閾値
            
        Returns:
            フォローアップが必要かどうか
        """
        # 簡易的な専門度判定（実際の実装では、より高度な判定が必要）
        complex_indicators = [
            "専門用語", "技術的", "理論", "アルゴリズム", "メカニズム", 
            "プロセス", "システム", "フレームワーク", "アーキテクチャ"
        ]
        
        complexity_score = sum(1 for indicator in complex_indicators if indicator in answer)
        normalized_score = min(complexity_score / 5.0, 1.0)  # 5個以上で最大値
        
        return normalized_score >= complexity_threshold
    
    def get_status(self) -> Dict[str, Any]:
        """現在の状態を取得"""
        return {
            "questions_asked": self.questions_asked,
            "current_section": self.current_section,
            "total_sections": len(self.document_sections),
            "has_more_sections": self.has_more_sections(),
            "progress_percentage": (self.current_section / len(self.document_sections) * 100) if self.document_sections else 0
        }