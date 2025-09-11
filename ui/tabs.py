import streamlit as st
from typing import Dict, Any, Optional, List
from ui.components import UIComponents, StreamingDisplay

class TabManager:
    """タブ切り替えロジックを管理するクラス"""
    
    def __init__(self):
        self.components = UIComponents()
        self.streaming_display = None
    
    def render_main_tabs(self, session_data: Dict[str, Any]):
        """メインタブを描画"""
        tab1, tab2 = st.tabs(["📚 要約・Q&Aセッション", "📊 最終レポート"])
        
        with tab1:
            self._render_qa_session_tab(session_data)
        
        with tab2:
            self._render_final_report_tab(session_data)
    
    def _render_qa_session_tab(self, session_data: Dict[str, Any]):
        """要約・Q&Aセッションタブの内容"""
        # 要約セクション
        summary = session_data.get('summary', '')
        if summary:
            self.components.render_summary_section(summary)
        
        # Q&Aセッション表示エリア
        qa_pairs = session_data.get('qa_pairs', [])
        
        if qa_pairs:
            st.subheader("💬 Q&Aセッション結果")
            self._render_qa_pairs(qa_pairs)
        else:
            # Q&Aが開始されていない場合の表示
            processing = session_data.get('processing', False)
            if processing:
                st.info("🔄 Q&Aセッションを実行中です...")
                # ストリーミング表示エリアを作成
                if not self.streaming_display:
                    self.streaming_display = StreamingDisplay()
                    self.streaming_display.create_streaming_area()
            else:
                st.info("📝 PDFファイルをアップロードしてQ&Aセッションを開始してください。")
    
    def _render_final_report_tab(self, session_data: Dict[str, Any]):
        """最終レポートタブの内容"""
        final_report = session_data.get('final_report', '')
        
        if final_report:
            self.components.render_final_report(final_report)
            
            # 統計情報があれば表示
            stats = session_data.get('statistics', {})
            if stats:
                st.divider()
                self.components.render_statistics(stats)
        else:
            qa_completed = session_data.get('qa_completed', False)
            if qa_completed:
                st.info("🔄 最終レポートを生成中です...")
            else:
                st.info("📋 Q&Aセッション完了後に最終レポートが生成されます。")
    
    def _render_qa_pairs(self, qa_pairs: List[Dict[str, Any]]):
        """Q&Aペアのリストを表示"""
        for i, qa_pair in enumerate(qa_pairs, 1):
            question = qa_pair.get('question', '質問なし')
            answer = qa_pair.get('answer', '回答なし')
            timestamp = qa_pair.get('timestamp', '')
            
            with st.expander(f"Q{i}: {question[:50]}...", expanded=False):
                st.markdown(f"**質問：** {question}")
                st.markdown(f"**回答：** {answer}")
                
                if timestamp:
                    st.caption(f"生成時刻: {timestamp}")
    
    def get_streaming_display(self) -> Optional[StreamingDisplay]:
        """ストリーミング表示オブジェクトを取得"""
        return self.streaming_display
    
    def update_streaming_content(self, agent_name: str, content: str, message_type: str = "normal"):
        """ストリーミング内容を更新"""
        if self.streaming_display:
            self.streaming_display.display_agent_message(agent_name, content, message_type)

class UploadTab:
    """アップロード・設定タブを管理するクラス"""
    
    def __init__(self):
        self.components = UIComponents()
    
    def render_upload_section(self) -> Dict[str, Any]:
        """アップロード・設定セクションを描画"""
        result = {
            'uploaded_file': None,
            'qa_turns': 10,
            'start_processing': False
        }
        
        # ファイルアップローダー
        uploaded_file = self.components.render_file_uploader()
        result['uploaded_file'] = uploaded_file
        
        if uploaded_file:
            st.success(f"✅ ファイルがアップロードされました: {uploaded_file.name}")
            
            # Q&A設定
            qa_settings = self.components.render_qa_settings()
            result['qa_turns'] = qa_settings['qa_turns']
            result['student_model'] = qa_settings['student_model']
            result['teacher_model'] = qa_settings['teacher_model']
            result['summarizer_model'] = qa_settings['summarizer_model']
            result['enable_followup'] = qa_settings['enable_followup']
            result['followup_threshold'] = qa_settings['followup_threshold']
            result['max_followups'] = qa_settings['max_followups']
            
            # 実行ボタン
            col1, col2 = st.columns([1, 3])
            with col1:
                start_button = st.button("🚀 実行開始", type="primary", use_container_width=True)
                result['start_processing'] = start_button
            
            with col2:
                if st.button("🔄 リセット", use_container_width=True):
                    # セッションリセットのフラグを設定
                    st.session_state['reset_requested'] = True
                    st.rerun()
        
        return result

class ProcessingTab:
    """処理中の状態を管理するクラス"""
    
    def __init__(self):
        self.components = UIComponents()
    
    def render_processing_status(self, current_step: str, progress_text: str = ""):
        """処理状況を表示"""
        st.subheader("🔄 処理中...")
        
        # プログレスバー
        progress_steps = {
            "pdf_processing": 0.2,
            "summary_generation": 0.4,
            "qa_session": 0.8,
            "final_report": 1.0
        }
        
        current_progress = progress_steps.get(current_step, 0.1)
        progress_bar = st.progress(current_progress)
        
        # ステップ表示
        step_descriptions = {
            "pdf_processing": "📄 PDFファイルを処理中...",
            "summary_generation": "📋 文書要約を生成中...",
            "qa_session": "💬 Q&Aセッションを実行中...",
            "final_report": "📊 最終レポートを作成中..."
        }
        
        current_step_text = step_descriptions.get(current_step, "処理中...")
        st.info(current_step_text)
        
        if progress_text:
            st.caption(progress_text)
        
        # 緊急リセット機能を追加
        st.divider()
        st.markdown("**🚨 処理が止まった場合**")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 処理をリセット", help="処理状態をリセットして最初からやり直します"):
                from services.session_manager import SessionManager
                SessionManager.reset_session()
                st.rerun()
        
        with col2:
            if st.button("⏹️ 処理を強制停止", help="現在の処理を強制停止します"):
                from services.session_manager import SessionManager
                SessionManager.stop_processing()
                SessionManager.set_step("upload")
                st.rerun()

class ErrorTab:
    """エラー表示を管理するクラス"""
    
    def __init__(self):
        self.components = UIComponents()
    
    def render_error_state(self, error_message: str):
        """エラー状態を表示"""
        self.components.render_error_message(error_message)
        
        st.markdown("### 🔧 対処方法")
        st.markdown("""
        - ファイルサイズが50MBを超えていないか確認してください
        - PDFファイルが破損していないか確認してください
        - OpenAI APIキーが正しく設定されているか確認してください
        - しばらく時間をおいて再度お試しください
        """)
        
        if st.button("🔄 リトライ"):
            # エラーをクリアしてリトライ
            st.session_state['error_message'] = None
            st.rerun()