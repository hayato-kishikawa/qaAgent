import asyncio
from typing import List, Dict, Optional
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.agents import ChatCompletionAgent, GroupChatOrchestration, RoundRobinGroupChatManager
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.contents import ChatMessageContent, ChatHistory

from config.settings import Settings

class KernelService:
    """Semantic Kernelとの統合を管理するサービス"""
    
    def __init__(self):
        self.settings = Settings()
        self.kernel = None
        self.chat_service = None
        self.execution_settings = None
        
        self._initialize_kernel()
    
    def _initialize_kernel(self):
        """Semantic Kernelを初期化"""
        # API キーの検証
        self.settings.validate_api_key()
        
        # Kernelの作成
        self.kernel = Kernel()
        
        # ChatGPTサービスの設定
        self.chat_service = OpenAIChatCompletion(
            service_id="openai-chat",
            ai_model_id=self.settings.GPT_MODEL,
            api_key=self.settings.OPENAI_API_KEY
        )
        
        # Kernelにサービスを追加
        self.kernel.add_service(self.chat_service)
        
        # 実行設定
        self.execution_settings = OpenAIChatPromptExecutionSettings(
            temperature=0.7,
            max_tokens=2000
        )
    
    def create_agent(self, name: str, description: str, instructions: str) -> ChatCompletionAgent:
        """
        エージェントを作成
        
        Args:
            name: エージェント名
            description: エージェントの説明
            instructions: システムプロンプト
            
        Returns:
            作成されたエージェント
        """
        return ChatCompletionAgent(
            name=name,
            description=description,
            instructions=instructions,
            kernel=self.kernel,
        )
    
    def get_kernel(self) -> Kernel:
        """Kernelインスタンスを取得"""
        return self.kernel
    
    def get_execution_settings(self) -> OpenAIChatPromptExecutionSettings:
        """実行設定を取得"""
        return self.execution_settings

class QASessionManager:
    """Q&Aセッションの管理を行うクラス"""
    
    def __init__(self, kernel_service: KernelService):
        self.kernel_service = kernel_service
        self.qa_pairs = []
        self.current_section = 0
        self.max_followups = 3
        self.current_followups = 0
    
    def reset_session(self):
        """セッションをリセット"""
        self.qa_pairs = []
        self.current_section = 0
        self.current_followups = 0
    
    def add_qa_pair(self, question: str, answer: str):
        """Q&Aペアを追加"""
        self.qa_pairs.append({
            "section": self.current_section,
            "question": question,
            "answer": answer,
            "followup_count": self.current_followups
        })
    
    def can_add_followup(self) -> bool:
        """フォローアップ質問を追加できるかチェック"""
        return self.current_followups < self.max_followups
    
    def increment_followup(self):
        """フォローアップカウンターを増加"""
        self.current_followups += 1
    
    def next_section(self):
        """次のセクションに進む"""
        self.current_section += 1
        self.current_followups = 0
    
    def get_qa_summary(self) -> Dict:
        """Q&Aの要約を取得"""
        return {
            "total_pairs": len(self.qa_pairs),
            "sections_covered": self.current_section + 1,
            "qa_pairs": self.qa_pairs
        }

class AgentOrchestrator:
    """エージェント間のやり取りを調整するクラス"""
    
    def __init__(self, kernel_service: KernelService):
        self.kernel_service = kernel_service
        self.runtime = None
    
    async def start_runtime(self):
        """ランタイムを開始"""
        if not self.runtime:
            self.runtime = InProcessRuntime()
            self.runtime.start()
    
    async def stop_runtime(self):
        """ランタイムを停止"""
        if self.runtime:
            await self.runtime.stop_when_idle()
            self.runtime = None
    
    async def run_qa_session(
        self, 
        agents: List[ChatCompletionAgent], 
        task: str,
        max_rounds: int,
        callback=None
    ) -> str:
        """
        Q&Aセッションを実行
        
        Args:
            agents: 参加エージェントのリスト
            task: 実行タスク
            max_rounds: 最大ラウンド数
            callback: メッセージコールバック関数
            
        Returns:
            セッション結果
        """
        await self.start_runtime()
        
        try:
            # グループチャットオーケストレーション
            orchestration = GroupChatOrchestration(
                members=agents,
                manager=RoundRobinGroupChatManager(max_rounds=max_rounds),
                agent_response_callback=callback,
            )
            
            # セッションを実行
            orchestration_result = await orchestration.invoke(
                task=task,
                runtime=self.runtime,
            )
            
            result = await orchestration_result.get()
            return result
            
        finally:
            await self.stop_runtime()
    
    async def single_agent_invoke(
        self, 
        agent: ChatCompletionAgent,
        message: str,
        chat_history: Optional[ChatHistory] = None
    ) -> str:
        """
        単一エージェントでメッセージを処理
        
        Args:
            agent: エージェント
            message: メッセージ
            chat_history: チャット履歴
            
        Returns:
            エージェントの応答
        """
        await self.start_runtime()
        
        try:
            if chat_history is None:
                chat_history = ChatHistory()
            
            # メッセージを追加
            chat_history.add_user_message(message)
            
            # エージェントを実行
            response_generator = agent.invoke(chat_history)
            
            # async generatorから結果を取得
            response_messages = []
            async for response_message in response_generator:
                response_messages.append(response_message)
            
            # 最後のメッセージから内容を取得
            if response_messages:
                last_message = response_messages[-1]
                if hasattr(last_message, 'content'):
                    response_content = str(last_message.content)
                else:
                    response_content = str(last_message)
            else:
                response_content = ""
            
            return response_content if response_content else "応答を取得できませんでした"
                
        finally:
            await self.stop_runtime()