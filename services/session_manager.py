import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime

class SessionManager:
    """Streamlitセッション状態の管理を行うクラス"""
    
    @staticmethod
    def initialize_session():
        """セッション状態を初期化"""
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
            st.session_state.document_uploaded = False
            st.session_state.processing = False
            st.session_state.qa_completed = False
            st.session_state.current_step = "upload"  # upload, processing, qa, completed
            
            # 文書関連
            st.session_state.document_data = {}
            st.session_state.qa_turns = 10
            
            # Q&A関連
            st.session_state.qa_pairs = []
            st.session_state.summary = ""
            st.session_state.final_report = ""
            
            # UI関連
            st.session_state.selected_tab = 0
            st.session_state.show_progress = False
            st.session_state.progress_text = ""
    
    @staticmethod
    def set_document_data(data: Dict[str, Any]):
        """文書データを保存"""
        st.session_state.document_data = data
        st.session_state.document_uploaded = True
    
    @staticmethod
    def get_document_data() -> Dict[str, Any]:
        """文書データを取得"""
        return st.session_state.get('document_data', {})
    
    @staticmethod
    def set_qa_turns(turns: int):
        """Q&Aターン数を設定"""
        st.session_state.qa_turns = turns
    
    @staticmethod
    def set_processing_settings(settings: Dict[str, Any]):
        """処理設定を保存"""
        st.session_state.processing_settings = settings
    
    @staticmethod
    def get_processing_settings() -> Dict[str, Any]:
        """処理設定を取得"""
        return st.session_state.get('processing_settings', {
            'qa_turns': 10,
            'student_model': 'gpt-5-mini',
            'teacher_model': 'gpt-5',
            'summarizer_model': 'gpt-5-nano',
            'enable_followup': True,
            'followup_threshold': 0.6,
            'max_followups': 3
        })
    
    @staticmethod
    def get_qa_turns() -> int:
        """Q&Aターン数を取得"""
        return st.session_state.get('qa_turns', 10)
    
    @staticmethod
    def start_processing():
        """処理開始"""
        st.session_state.processing = True
        st.session_state.current_step = "processing"
        st.session_state.show_progress = True
    
    @staticmethod
    def stop_processing():
        """処理終了"""
        st.session_state.processing = False
        st.session_state.show_progress = False
    
    @staticmethod
    def set_step(step: str):
        """現在のステップを設定"""
        st.session_state.current_step = step
    
    @staticmethod
    def get_step() -> str:
        """現在のステップを取得"""
        return st.session_state.get('current_step', 'upload')
    
    @staticmethod
    def is_processing() -> bool:
        """処理中かどうか"""
        return st.session_state.get('processing', False)
    
    @staticmethod
    def set_summary(summary: str):
        """要約を保存"""
        st.session_state.summary = summary
    
    @staticmethod
    def get_summary() -> str:
        """要約を取得"""
        return st.session_state.get('summary', '')
    
    @staticmethod
    def add_qa_pair(question: str, answer: str):
        """Q&Aペアを追加"""
        if 'qa_pairs' not in st.session_state:
            st.session_state.qa_pairs = []
        
        qa_pair = {
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'answer': answer
        }
        st.session_state.qa_pairs.append(qa_pair)
    
    @staticmethod
    def get_qa_pairs() -> list:
        """Q&Aペアを取得"""
        return st.session_state.get('qa_pairs', [])
    
    @staticmethod
    def set_final_report(report: str):
        """最終レポートを保存"""
        st.session_state.final_report = report
        st.session_state.qa_completed = True
        st.session_state.current_step = "completed"
    
    @staticmethod
    def get_final_report() -> str:
        """最終レポートを取得"""
        return st.session_state.get('final_report', '')
    
    @staticmethod
    def is_qa_completed() -> bool:
        """Q&Aが完了しているか"""
        return st.session_state.get('qa_completed', False)
    
    @staticmethod
    def set_progress(text: str, show: bool = True):
        """プログレス状態を設定"""
        st.session_state.progress_text = text
        st.session_state.show_progress = show
    
    @staticmethod
    def get_progress() -> tuple:
        """プログレス状態を取得"""
        return (
            st.session_state.get('show_progress', False),
            st.session_state.get('progress_text', '')
        )
    
    @staticmethod
    def reset_session():
        """セッションをリセット"""
        # 重要なキーのみ残してリセット
        keys_to_keep = ['initialized']
        keys_to_remove = [key for key in st.session_state.keys() if key not in keys_to_keep]
        
        for key in keys_to_remove:
            del st.session_state[key]
        
        # 再初期化
        SessionManager.initialize_session()
    
    @staticmethod
    def set_selected_tab(tab_index: int):
        """選択されたタブを設定"""
        st.session_state.selected_tab = tab_index
    
    @staticmethod
    def get_selected_tab() -> int:
        """選択されたタブを取得"""
        return st.session_state.get('selected_tab', 0)
    
    @staticmethod
    def get_session_info() -> Dict[str, Any]:
        """セッション情報を取得"""
        return {
            'document_uploaded': st.session_state.get('document_uploaded', False),
            'processing': st.session_state.get('processing', False),
            'qa_completed': st.session_state.get('qa_completed', False),
            'current_step': st.session_state.get('current_step', 'upload'),
            'qa_pairs_count': len(st.session_state.get('qa_pairs', [])),
            'has_summary': bool(st.session_state.get('summary', '')),
            'has_final_report': bool(st.session_state.get('final_report', ''))
        }