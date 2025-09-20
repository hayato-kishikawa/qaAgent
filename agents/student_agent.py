from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from services.kernel_service import KernelService
from semantic_kernel.contents import ChatHistory, ChatMessageContent
from semantic_kernel.contents.chat_message_content import AuthorRole

class StudentAgent(BaseAgent):
    """生徒エージェント - 質問を生成する役割"""
    
    def __init__(self, kernel_service: KernelService, prompt_version: str = "simple"):
        self.questions_asked = 0
        self.current_section = 0
        self.document_sections = []
        self.qa_history = []  # 従来の履歴（後方互換性のため保持）
        self.asked_topics = set()  # 質問済みトピックを追跡
        self.chat_history = ChatHistory()  # Semantic Kernel ChatHistory
        super().__init__("student", kernel_service, prompt_version)
    
    def get_description(self) -> str:
        """エージェントの説明を返す"""
        return "好奇心旺盛で知識欲の強い学生。文書の内容について理解を深めるための質問を生成します。"

    def set_question_level(self, level: str):
        """質問レベルを動的に設定"""
        if level in ["simple", "latest"]:
            self.prompt_version = level
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

        # 質問のトピックを抽出して追跡
        topic_keywords = self._extract_topic_keywords(question)
        self.asked_topics.update(topic_keywords)

        if question_type == "main":
            self.questions_asked += 1

    def _extract_topic_keywords(self, question: str) -> set:
        """質問からトピックキーワードを抽出"""
        # 簡単なキーワード抽出（実際の実装ではより高度な手法を使用）
        import re

        # 日本語の単語を抽出（ひらがな、カタカナ、漢字）
        keywords = re.findall(r'[ぁ-ん]+|[ァ-ヴ]+|[一-龯]+', question)

        # 短すぎる単語や一般的すぎる単語を除外
        stopwords = {'は', 'が', 'を', 'に', 'で', 'と', 'の', 'か', 'から', 'まで', 'より', 'こと', 'もの', 'それ', 'これ', 'あの', 'その', 'この', 'です', 'ます', 'ある', 'いる', 'する', 'した', 'なる', 'なっ', 'という', 'として', 'について', 'による', 'によって'}

        filtered_keywords = {kw for kw in keywords if len(kw) >= 2 and kw not in stopwords}
        return filtered_keywords

    def get_qa_history(self, question_type: str = None) -> list:
        """Q&A履歴を取得"""
        if question_type:
            return [qa for qa in self.qa_history if qa['question_type'] == question_type]
        return self.qa_history.copy()

    def has_similar_question(self, current_question: str) -> bool:
        """類似の質問が既に存在するかチェック"""
        current_topics = self._extract_topic_keywords(current_question)

        for qa in self.qa_history:
            if qa['question_type'] == 'main':  # メイン質問のみチェック
                past_topics = self._extract_topic_keywords(qa['question'])
                # 共通トピックが多い場合は類似と判定
                if len(current_topics & past_topics) >= 2:
                    return True
        return False
    
    def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        メッセージを処理して質問を生成

        Args:
            message: 入力メッセージ
            context: コンテキスト情報

        Returns:
            生成された質問プロンプト（非同期版はgenerate_question_with_chat_historyを使用）
        """
        # 後方互換性のため、従来のプロンプト生成を維持
        if context:
            document_content = context.get("document_content", "")
            current_section_content = context.get("current_section_content", "")
            target_keyword = context.get("target_keyword")
        else:
            document_content = ""
            current_section_content = self.get_current_section()
            target_keyword = None

        # シンプルなプロンプトを返す（実際のLLM呼び出しは呼び出し側で行う）
        return self._build_simple_question_prompt(
            document_content,
            current_section_content,
            target_keyword
        )

    async def generate_question_with_chat_history(self, document_content: str, section_content: str, target_keyword: str = None) -> str:
        """
        ChatHistoryを使用して質問を生成

        Args:
            document_content: 文書全体の内容
            section_content: 現在のセクション内容
            target_keyword: 対象キーワード（オプション）

        Returns:
            生成された質問
        """
        from services.kernel_service import AgentOrchestrator

        # 文書内容をシステムメッセージとして追加
        document_context = f"""
【文書全体】
{document_content[:800]}...

【現在注目するセクション】
{section_content}
"""

        if target_keyword:
            document_context += f"\n\n特に「{target_keyword}」について質問してください。"

        context_message = ChatMessageContent(
            role=AuthorRole.SYSTEM,
            content=document_context
        )

        # 新しいChatHistoryを作成
        working_history = ChatHistory()

        # システムメッセージを追加
        working_history.add_message(context_message)

        # 過去の会話履歴を追加
        for message in self.chat_history.messages:
            working_history.add_message(message)

        # エージェントオーケストレーターを使用して質問を生成
        # エージェントは既に latest.ini のシステムプロンプトで初期化されている
        orchestrator = AgentOrchestrator(self.kernel_service)
        response = await orchestrator.single_agent_invoke(
            agent=self.agent,
            message="上記の文書について、あなたの役割に従って1つ質問を生成してください。",
            chat_history=working_history
        )

        return response.strip()

    def get_chat_history(self) -> ChatHistory:
        """現在のChatHistoryを取得"""
        return self.chat_history

    def get_chat_history_summary(self) -> Dict[str, Any]:
        """ChatHistoryの要約情報を取得"""
        messages = self.chat_history.messages
        user_messages = [msg for msg in messages if msg.role == AuthorRole.USER]
        assistant_messages = [msg for msg in messages if msg.role == AuthorRole.ASSISTANT]

        return {
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "last_interaction": {
                "user": user_messages[-1].content if user_messages else None,
                "assistant": assistant_messages[-1].content if assistant_messages else None
            }
        }

    def clear_chat_history(self):
        """ChatHistoryをクリア"""
        self.chat_history = ChatHistory()


    def _build_simple_question_prompt(self, document_content: str, section_content: str, target_keyword: str = None) -> str:
        """シンプルな質問プロンプトを構築"""
        prompt_parts = []

        # 文書内容
        if document_content:
            prompt_parts.append(f"【文書全体】\n{document_content[:800]}...")

        # 現在のセクション
        if section_content:
            prompt_parts.append(f"【現在注目するセクション】\n{section_content}")

        # 質問指示
        if target_keyword:
            prompt_parts.append(f"\n「{target_keyword}」について1つ質問してください。")
        else:
            prompt_parts.append("\n現在のセクションについて1つ質問してください。")

        return "\n\n".join(prompt_parts)

    def _build_question_prompt(self, document_content: str, section_content: str, previous_qa: list, target_keyword: str = None) -> str:
        """質問生成用のプロンプトを構築（改良版：履歴を考慮し重複回避）"""
        prompt_parts = []

        # 文書全体の情報
        if document_content:
            prompt_parts.append(f"【文書全体】\\n{document_content[:1000]}...")

        # 現在のセクション
        if section_content:
            prompt_parts.append(f"【現在注目すべきセクション（セクション{self.current_section + 1}）】\\n{section_content}")

        # 過去のメイン質問履歴（重複回避のため）
        main_questions = self.get_qa_history("main")
        if main_questions:
            prompt_parts.append("【これまでに質問した内容（重複を避けてください）】")
            for i, qa in enumerate(main_questions, 1):  # 全てのメイン質問を参照
                prompt_parts.append(f"過去の質問{i}: {qa['question']}")
                prompt_parts.append(f"回答要約: {qa['answer'][:150]}...")

        # 質問済みトピック
        if self.asked_topics:
            prompt_parts.append(f"【既に扱ったトピック】")
            prompt_parts.append(f"これらの話題は避けてください: {', '.join(list(self.asked_topics)[:10])}")

        # 質問指示
        prompt_parts.append("\\n【指示】")
        prompt_parts.append("あなたは文書を読んで勉強している学習者です。")
        prompt_parts.append("現在のセクションについて、1つだけ質問を生成してください。")

        if target_keyword:
            # 単語指定がある場合
            prompt_parts.append(f"\\n「{target_keyword}」について質問してください。")
        else:
            # 通常の質問生成指示
            prompt_parts.append("\\n現在のセクションで分からないことを1つ選んで質問してください。")

        prompt_parts.append("\\n【重要な制約】")
        prompt_parts.append("- 必ず1つの質問のみを出力してください")
        prompt_parts.append("- 複数の質問を並べて書かないでください")
        prompt_parts.append("- 「〜とは何ですか？」のような1文で完結する質問にしてください")
        prompt_parts.append("- 過去に質問した内容と重複しないようにしてください")
        prompt_parts.append("- 自然な日本語で、分かりやすく質問してください")

        prompt_parts.append("\\n【出力形式】")
        prompt_parts.append("質問文のみを1行で出力してください。説明や前置きは不要です。")

        prompt_parts.append("\\n例: 「これはどのような仕組みで動いているのですか？」")

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