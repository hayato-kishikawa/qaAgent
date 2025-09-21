from typing import Dict, Any
from agents.base_agent import BaseAgent
from services.kernel_service import KernelService
from semantic_kernel.contents import ChatHistory, ChatMessageContent
from semantic_kernel.contents.chat_message_content import AuthorRole

class StudentAgent(BaseAgent):
    """生徒エージェント - 質問を生成する役割"""
    
    def __init__(self, kernel_service: KernelService, prompt_version: str = "beginner"):
        self.questions_asked = 0
        self.current_section = 0
        self.document_sections = []
        self.qa_history = []  # 従来の履歴（後方互換性のため保持）
        self.asked_topics = set()  # 質問済みトピックを追跡
        self.chat_history = ChatHistory()  # Semantic Kernel ChatHistory
        self.question_level = prompt_version  # app.pyで参照される属性を設定
        super().__init__("student", kernel_service, prompt_version)
    
    def get_description(self) -> str:
        """エージェントの説明を返す"""
        return "好奇心旺盛で知識欲の強い学生。文書の内容について理解を深めるための質問を生成します。"

    def set_question_level(self, level: str):
        """質問レベルを動的に設定"""
        if level in ["beginner", "simple", "standard"]:
            self.prompt_version = level
            self.question_level = level  # app.pyで参照される属性も設定
            # エージェントを再初期化してプロンプトを再読み込み
            self._initialize_agent()
    
    def set_document_sections(self, sections: list):
        """文書のセクション分割を設定"""
        self.document_sections = sections
        self.current_section = 0
        self.questions_asked = 0
        self.qa_history = []  # 履歴をリセット
        self.asked_topics = set()  # トピックもリセット
        self.chat_history = ChatHistory()  # ChatHistoryもリセット
    
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

    def add_qa_to_history(self, question: str, answer: str, question_type: str = "main"):
        """Q&A履歴に追加"""
        qa_entry = {
            "question": question,
            "answer": answer,
            "question_type": question_type,  # "main" or "followup"
            "section_index": self.current_section,
            "timestamp": self.questions_asked + 1
        }
        self.qa_history.append(qa_entry)

        # Semantic Kernel ChatHistoryにも追加
        self.chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=question
            )
        )
        self.chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content=answer
            )
        )


        if question_type == "main":
            self.questions_asked += 1

    def process_message(self, message: str, context: Dict[str, Any] = None) -> str:
        """メッセージを処理（最小限の実装）"""
        return message


    def get_qa_history(self, question_type: str = None) -> list:
        """Q&A履歴を取得"""
        if question_type:
            return [qa for qa in self.qa_history if qa['question_type'] == question_type]
        return self.qa_history.copy()
    
    
    def get_status(self) -> Dict[str, Any]:
        """現在の状態を取得"""
        return {
            "questions_asked": self.questions_asked,
            "current_section": self.current_section,
            "total_sections": len(self.document_sections),
            "has_more_sections": self.has_more_sections(),
            "progress_percentage": (self.current_section / len(self.document_sections) * 100) if self.document_sections else 0
        }