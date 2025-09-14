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
        quick_mode = session_data.get('quick_mode', False)

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
                if quick_mode:
                    # Quickモードの場合、即座にレポートを生成
                    summary = session_data.get('summary', '')
                    qa_pairs = session_data.get('qa_pairs', [])
                    document_info = session_data.get('document_data', {})

                    if summary and qa_pairs:
                        quick_report = self.components.generate_quick_report(summary, qa_pairs, document_info)
                        # セッションにレポートを保存
                        st.session_state['final_report'] = quick_report
                        st.session_state['qa_completed'] = True

                        # レポートを表示
                        self.components.render_final_report(quick_report)

                        # 統計情報を生成・表示
                        quick_stats = {
                            'qa_count': len(qa_pairs),
                            'document_pages': document_info.get('page_count', 0),
                            'document_tokens': document_info.get('total_tokens', 0),
                            'duration_seconds': 0  # Quickモードは即座に完了
                        }
                        st.divider()
                        self.components.render_statistics(quick_stats)
                    else:
                        st.info("💨 Quickモード: レポート生成準備中...")
                else:
                    st.info("🔄 最終レポートを生成中です...")
            else:
                if quick_mode:
                    st.info("📋 Q&Aセッション完了後に簡易レポートが即座に生成されます。")
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
                
                # 回答表示
                st.markdown(f"**回答：** {answer}")
                
                # フォローアップ質問をインデントして表示
                followup_question = qa_pair.get('followup_question', '')
                followup_answer = qa_pair.get('followup_answer', '')
                
                if followup_question:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**🔄 Q{i}-追加質問:**", unsafe_allow_html=True)
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{followup_question}", unsafe_allow_html=True)
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**💡 Q{i}-追加回答:**", unsafe_allow_html=True)
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{followup_answer}", unsafe_allow_html=True)
                
                # キャプション情報（タイムスタンプと専門性スコア）
                caption_parts = []
                if timestamp:
                    caption_parts.append(f"生成時刻: {timestamp}")
                
                complexity_score = qa_pair.get('complexity_score', 'N/A')
                if complexity_score != 'N/A':
                    caption_parts.append(f"専門性: {complexity_score}")
                
                if caption_parts:
                    st.caption(" | ".join(caption_parts))
    
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
    
    def render_upload_section(self, sidebar_settings: Dict[str, Any]) -> Dict[str, Any]:
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

            # サイドバー設定を結果に統合
            result.update(sidebar_settings)

            # 文書情報を表示（PDF処理後に情報があれば）
            doc_data = st.session_state.get('document_data', {})
            if doc_data:
                self.components.render_document_info(doc_data)

            st.divider()

            # 実行ボタン
            col1, col2 = st.columns([1, 1])
            with col1:
                start_button = st.button("🚀 実行開始", type="primary", use_container_width=True)
                result['start_processing'] = start_button

                # 即時フィードバック（rerunしない）
                if start_button:
                    st.success("🔄 処理を開始しています...")

            with col2:
                if st.button("🔄 リセット", use_container_width=True):
                    # セッションリセットのフラグを設定
                    st.session_state['reset_requested'] = True
                    st.rerun()
        else:
            # ファイルがアップロードされていない場合の詳細説明
            st.info("📄 PDFファイルをアップロードして、AIエージェントによる文書理解セッションを開始してください")

            # アプリの特徴
            st.markdown("### ✨ このアプリの特徴")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🤖 3つのAIエージェント**")
                st.markdown("- 🎓 **学生エージェント**: 文書について質問を生成")
                st.markdown("- 👨‍🏫 **教師エージェント**: 詳細で分かりやすい回答を提供")
                st.markdown("- 📋 **要約エージェント**: 文書要約と最終レポート作成")

            with col2:
                st.markdown("**📊 学習効果**")
                st.markdown("- 💡 **理解促進**: Q&A形式で段階的に理解")
                st.markdown("- 🔄 **フォローアップ**: 難しい回答には追加説明")
                st.markdown("- 📝 **レポート**: 学習内容をMarkdown形式で整理")

            st.divider()

            # 使用方法
            st.markdown("### 🚀 使用方法")

            steps_col1, steps_col2, steps_col3 = st.columns(3)

            with steps_col1:
                st.markdown("""
                **ステップ1: 設定確認**
                左サイドバーで設定を確認・調整

                **ステップ2: ファイル選択**
                PDFファイルをドラッグ&ドロップ

                **ステップ3: 実行開始**
                🚀ボタンでQ&Aセッション開始
                """)

            with steps_col2:
                st.markdown("**📋 対応ファイル**")
                st.markdown("- **形式**: PDFファイルのみ")
                st.markdown("- **サイズ**: 最大50MB")
                st.markdown("- **内容**: 論文、レポート、マニュアル等の文書")
                st.markdown("- **言語**: 日本語・英語対応")

            with steps_col3:
                st.markdown("**⚙️ 主な設定項目**")
                st.markdown("- **Q&A数**: 1-20回（推奨: 10回）")
                st.markdown("- **モデル**: GPT-5系から選択可能")
                st.markdown("- **重要単語**: 優先的に質問生成する単語指定")

            st.divider()

            # 利用シーン
            st.markdown("### 💼 こんな場面で活用")
            scenario_col1, scenario_col2, scenario_col3 = st.columns(3)

            with scenario_col1:
                st.markdown("""
                **📚 学習・研究**
                - 論文の理解
                - 専門書の要点整理
                - 研究資料の分析
                """)

            with scenario_col2:
                st.markdown("""
                **💼 業務効率化**
                - 報告書の要約
                - マニュアルの理解
                - 技術資料の習得
                """)

            with scenario_col3:
                st.markdown("""
                **🎯 試験対策**
                - 教材の重要ポイント抽出
                - 問題集作成の参考
                - 復習用資料の作成
                """)

            # 注意事項
            st.markdown("### ⚠️ ご利用上の注意")
            st.markdown("""
            - 処理時間は文書の長さとQ&A数に比例します（目安: 10Q&Aで3-5分）
            - 専門的な内容ほど、より詳細な説明が生成されます
            - 生成されるQ&Aは学習効果を重視した構成になっています
            """)

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