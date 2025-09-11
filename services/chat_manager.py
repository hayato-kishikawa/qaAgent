from typing import List, Dict, Optional
from semantic_kernel.contents import ChatMessageContent, ChatHistory
from datetime import datetime
import json

class ChatManager:
    """チャット履歴とセッション管理を行うクラス"""
    
    def __init__(self):
        self.chat_history = ChatHistory()
        self.session_data = {
            "start_time": None,
            "end_time": None,
            "document_info": {},
            "qa_pairs": [],
            "summary": "",
            "final_report": ""
        }
    
    def start_session(self, document_info: Dict):
        """セッションを開始"""
        self.session_data["start_time"] = datetime.now()
        self.session_data["document_info"] = document_info
        self.chat_history = ChatHistory()
        self.session_data["qa_pairs"] = []
    
    def end_session(self):
        """セッションを終了"""
        self.session_data["end_time"] = datetime.now()
    
    def add_message(self, role: str, content: str, agent_name: Optional[str] = None):
        """メッセージを追加"""
        if role == "user":
            self.chat_history.add_user_message(content)
        elif role == "assistant":
            self.chat_history.add_assistant_message(content)
        else:
            # システムメッセージとして追加
            self.chat_history.add_system_message(content)
    
    def add_qa_pair(self, question: str, answer: str, section: int = 0):
        """Q&Aペアを追加"""
        qa_pair = {
            "timestamp": datetime.now().isoformat(),
            "section": section,
            "question": question,
            "answer": answer
        }
        self.session_data["qa_pairs"].append(qa_pair)
    
    def set_summary(self, summary: str):
        """文書要約を設定"""
        self.session_data["summary"] = summary
    
    def set_final_report(self, report: str):
        """最終レポートを設定"""
        self.session_data["final_report"] = report
    
    def get_chat_history(self) -> ChatHistory:
        """チャット履歴を取得"""
        return self.chat_history
    
    def get_session_data(self) -> Dict:
        """セッションデータを取得"""
        return self.session_data
    
    def get_qa_pairs(self) -> List[Dict]:
        """Q&Aペアのリストを取得"""
        return self.session_data["qa_pairs"]
    
    def get_session_duration(self) -> Optional[float]:
        """セッション時間を取得（秒）"""
        if self.session_data["start_time"] and self.session_data["end_time"]:
            duration = self.session_data["end_time"] - self.session_data["start_time"]
            return duration.total_seconds()
        return None
    
    def export_session_json(self) -> str:
        """セッションデータをJSON形式でエクスポート"""
        export_data = self.session_data.copy()
        
        # datetimeオブジェクトを文字列に変換
        if export_data["start_time"]:
            export_data["start_time"] = export_data["start_time"].isoformat()
        if export_data["end_time"]:
            export_data["end_time"] = export_data["end_time"].isoformat()
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)
    
    def format_qa_for_display(self) -> str:
        """表示用にQ&Aをフォーマット"""
        if not self.session_data["qa_pairs"]:
            return "まだQ&Aペアがありません。"
        
        formatted_text = []
        for i, qa in enumerate(self.session_data["qa_pairs"], 1):
            formatted_text.append(f"**Q{i}:** {qa['question']}")
            formatted_text.append(f"**A{i}:** {qa['answer']}")
            formatted_text.append("---")
        
        return "\\n\\n".join(formatted_text)
    
    def get_statistics(self) -> Dict:
        """セッション統計を取得"""
        qa_count = len(self.session_data["qa_pairs"])
        duration = self.get_session_duration()
        
        stats = {
            "qa_count": qa_count,
            "duration_seconds": duration,
            "document_pages": self.session_data["document_info"].get("page_count", 0),
            "document_tokens": self.session_data["document_info"].get("total_tokens", 0),
            "has_summary": bool(self.session_data["summary"]),
            "has_final_report": bool(self.session_data["final_report"])
        }
        
        if duration:
            stats["avg_qa_time"] = duration / qa_count if qa_count > 0 else 0
        
        return stats

class StreamingCallback:
    """ストリーミング表示用のコールバッククラス"""
    
    def __init__(self, chat_manager: ChatManager, display_callback=None):
        self.chat_manager = chat_manager
        self.display_callback = display_callback
        self.current_qa = {"question": "", "answer": ""}
    
    def __call__(self, message: ChatMessageContent) -> None:
        """エージェントの応答を処理"""
        agent_name = message.name
        content = message.content
        
        # チャット履歴に追加
        self.chat_manager.add_message("assistant", content, agent_name)
        
        # 質問と回答を解析
        if agent_name == "student":
            # 生徒の質問
            self.current_qa["question"] = content
            if self.display_callback:
                self.display_callback("question", content, agent_name)
                
        elif agent_name == "teacher":
            # 先生の回答
            self.current_qa["answer"] = content
            
            # Q&Aペアとして保存
            if self.current_qa["question"]:
                self.chat_manager.add_qa_pair(
                    self.current_qa["question"],
                    self.current_qa["answer"]
                )
                # リセット
                self.current_qa = {"question": "", "answer": ""}
            
            if self.display_callback:
                self.display_callback("answer", content, agent_name)
                
        elif agent_name == "summarizer":
            # 要約エージェント
            if "要約" in content or "まとめ" in content:
                self.chat_manager.set_summary(content)
            else:
                self.chat_manager.set_final_report(content)
                
            if self.display_callback:
                self.display_callback("summary", content, agent_name)
        
        else:
            # その他のエージェント
            if self.display_callback:
                self.display_callback("other", content, agent_name)