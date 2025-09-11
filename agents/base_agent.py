from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from semantic_kernel.agents import ChatCompletionAgent

from services.kernel_service import KernelService
from prompts.prompt_loader import PromptLoader

class BaseAgent(ABC):
    """エージェントの基底クラス"""
    
    def __init__(self, agent_type: str, kernel_service: KernelService, prompt_version: str = "latest"):
        self.agent_type = agent_type
        self.kernel_service = kernel_service
        self.prompt_version = prompt_version
        self.prompt_loader = PromptLoader()
        self.agent = None
        
        self._initialize_agent()
    
    def _initialize_agent(self):
        """エージェントを初期化"""
        # プロンプトを読み込み
        system_prompt = self.prompt_loader.get_system_prompt(self.agent_type, self.prompt_version)
        
        # エージェントを作成
        self.agent = self.kernel_service.create_agent(
            name=self.agent_type,
            description=self.get_description(),
            instructions=system_prompt
        )
    
    @abstractmethod
    def get_description(self) -> str:
        """エージェントの説明を返す"""
        pass
    
    def get_agent(self) -> ChatCompletionAgent:
        """Semantic Kernelエージェントインスタンスを取得"""
        return self.agent
    
    def update_prompt_version(self, version: str):
        """プロンプトバージョンを更新"""
        self.prompt_version = version
        self._initialize_agent()
    
    @abstractmethod
    def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """メッセージを処理"""
        pass