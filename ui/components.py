import streamlit as st
from typing import Dict, Any, Optional, List
import time

class UIComponents:
    """再利用可能なUIコンポーネント"""
    
    @staticmethod
    def render_header():
        """アプリケーションヘッダーを描画"""
        st.title("🤖 AI文書要約・Q&Aアプリ")
        st.markdown("""
        このアプリは、PDFドキュメントをアップロードして、3つのAIエージェントによる要約とQ&Aセッションを通じて理解を深めることができます。
        """)
        st.divider()
    
    @staticmethod
    def render_file_uploader() -> Optional[Any]:
        """ファイルアップローダーを描画"""
        st.subheader("📄 PDFファイルをアップロード")
        
        uploaded_file = st.file_uploader(
            "PDFファイルを選択してください（最大50MB）",
            type=['pdf'],
            help="論文や専門文書のPDFファイルをアップロードしてください"
        )
        
        return uploaded_file
    
    @staticmethod
    def render_qa_settings() -> int:
        """Q&A設定を描画"""
        st.subheader("⚙️ Q&A設定")
        
        qa_turns = st.slider(
            "Q&Aターン数",
            min_value=5,
            max_value=20,
            value=10,
            help="生成するQ&Aペアの数を設定してください"
        )
        
        return qa_turns
    
    @staticmethod
    def render_document_info(doc_data: Dict[str, Any]):
        """文書情報を表示"""
        if not doc_data:
            return
            
        st.subheader("📋 文書情報")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("ページ数", doc_data.get('page_count', 0))
        
        with col2:
            st.metric("トークン数", f"{doc_data.get('total_tokens', 0):,}")
        
        with col3:
            split_status = "分割済み" if doc_data.get('is_split', False) else "未分割"
            st.metric("処理状況", split_status)
        
        # トークン数による警告
        if doc_data.get('total_tokens', 0) > 200000:
            st.warning("⚠️ トークン数が多いため、処理に時間がかかる可能性があります")
    
    @staticmethod
    def render_progress_indicator(show: bool, text: str):
        """プログレスインジケーターを表示"""
        if show:
            with st.spinner(text):
                time.sleep(0.1)  # UI更新のため短時間待機
    
    @staticmethod
    def render_summary_section(summary: str):
        """要約セクションを描画"""
        if summary:
            st.subheader("📋 文書要約")
            st.markdown(summary)
            st.divider()
    
    @staticmethod
    def render_qa_streaming_area():
        """Q&Aストリーミング表示エリアを作成"""
        st.subheader("💬 Q&Aセッション")
        
        # プレースホルダーを作成
        qa_container = st.container()
        
        return qa_container
    
    @staticmethod
    def render_qa_pair(container, question: str, answer: str, pair_number: int):
        """Q&Aペアを表示"""
        with container:
            with st.expander(f"Q{pair_number}: {question[:50]}...", expanded=True):
                st.markdown(f"**質問：** {question}")
                st.markdown(f"**回答：** {answer}")
    
    @staticmethod
    def render_final_report(report: str):
        """最終レポートを表示"""
        if report:
            st.subheader("📊 最終レポート")
            st.markdown(report)
            
            # コピーボタン
            if st.button("📋 レポートをコピー", key="copy_report"):
                # JavaScriptを使用してクリップボードにコピー
                st.components.v1.html(f"""
                    <script>
                        navigator.clipboard.writeText(`{report.replace('`', '\\`')}`);
                        alert('レポートがクリップボードにコピーされました！');
                    </script>
                """, height=0)
    
    @staticmethod
    def render_statistics(stats: Dict[str, Any]):
        """統計情報を表示"""
        st.subheader("📊 セッション統計")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Q&A数", stats.get('qa_count', 0))
        
        with col2:
            duration = stats.get('duration_seconds', 0)
            duration_str = f"{duration:.1f}秒" if duration else "N/A"
            st.metric("処理時間", duration_str)
        
        with col3:
            st.metric("文書ページ数", stats.get('document_pages', 0))
        
        with col4:
            tokens = stats.get('document_tokens', 0)
            token_str = f"{tokens:,}" if tokens else "N/A"
            st.metric("トークン数", token_str)
    
    @staticmethod
    def render_error_message(error: str):
        """エラーメッセージを表示"""
        st.error(f"❌ エラーが発生しました: {error}")
    
    @staticmethod
    def render_success_message(message: str):
        """成功メッセージを表示"""
        st.success(f"✅ {message}")
    
    @staticmethod
    def render_warning_message(message: str):
        """警告メッセージを表示"""
        st.warning(f"⚠️ {message}")
    
    @staticmethod
    def render_info_message(message: str):
        """情報メッセージを表示"""
        st.info(f"ℹ️ {message}")

class StreamingDisplay:
    """ストリーミング表示用のクラス"""
    
    def __init__(self):
        self.containers = {}
        self.current_qa = {"question": "", "answer": ""}
        self.qa_count = 0
    
    def create_streaming_area(self):
        """ストリーミング表示エリアを作成"""
        self.main_container = st.container()
        self.progress_placeholder = st.empty()
        
        return self.main_container
    
    def update_progress(self, text: str):
        """プログレス表示を更新"""
        with self.progress_placeholder:
            st.info(text)
    
    def display_agent_message(self, agent_name: str, content: str, message_type: str = "normal"):
        """エージェントのメッセージを表示"""
        with self.main_container:
            if agent_name == "student":
                self._display_question(content)
            elif agent_name == "teacher":
                self._display_answer(content)
            elif agent_name == "summarizer":
                self._display_summary(content)
    
    def _display_question(self, question: str):
        """質問を表示"""
        self.qa_count += 1
        self.current_qa["question"] = question
        
        with st.expander(f"❓ Q{self.qa_count}: {question[:50]}...", expanded=True):
            st.markdown(f"**質問：** {question}")
            # 回答用のプレースホルダーを作成
            answer_placeholder = st.empty()
            self.current_qa["answer_placeholder"] = answer_placeholder
    
    def _display_answer(self, answer: str):
        """回答を表示"""
        if "answer_placeholder" in self.current_qa:
            with self.current_qa["answer_placeholder"]:
                st.markdown(f"**回答：** {answer}")
        
        # Q&Aペア完了
        self.current_qa = {"question": "", "answer": ""}
    
    def _display_summary(self, summary: str):
        """要約を表示"""
        with self.main_container:
            st.markdown("### 📋 要約")
            st.markdown(summary)
            st.divider()