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
        tab1, tab2, tab3 = st.tabs(["📚 要約・Q&Aセッション", "📊 最終レポート", "📄 文書ビューアー"])

        with tab1:
            self._render_qa_session_tab(session_data)

        with tab2:
            self._render_final_report_tab(session_data)

        with tab3:
            self._render_document_viewer_tab(session_data)
    
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

            # インタラクティブ質問セクション
            self._render_interactive_question_section(session_data)
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
                st.markdown(f"**❓ Q{i} (メイン質問):**")
                st.write(f"{question}")

                st.markdown(f"**💡 A{i}:**")
                st.write(f"{answer}")
                
                # フォローアップ質問を関連性を明確にして表示
                followup_question = qa_pair.get('followup_question', '')
                followup_answer = qa_pair.get('followup_answer', '')

                if followup_question:
                    st.markdown("""
                    <div style="
                        border-left: 3px solid #1f77b4;
                        padding-left: 15px;
                        margin-left: 20px;
                        margin-top: 15px;
                        background: linear-gradient(90deg, #f8f9ff 0%, #ffffff 100%);
                        border-radius: 0 8px 8px 0;
                        padding-top: 10px;
                        padding-bottom: 10px;
                    ">
                    """, unsafe_allow_html=True)

                    st.markdown(f"**🔄 Q{i+1}-1 (フォローアップ):**")
                    st.markdown(f"→ {followup_question}")

                    st.markdown(f"**💡 A{i+1}-1:**")
                    st.markdown(f"→ {followup_answer}")

                    st.markdown("</div>", unsafe_allow_html=True)
                
                # キャプション情報（タイムスタンプと専門性スコア）
                caption_parts = []
                if timestamp:
                    caption_parts.append(f"生成時刻: {timestamp}")
                
                complexity_score = qa_pair.get('complexity_score', 'N/A')
                if complexity_score != 'N/A':
                    caption_parts.append(f"専門性: {complexity_score}")
                
                if caption_parts:
                    st.caption(" | ".join(caption_parts))

    def _render_interactive_question_section(self, session_data: Dict[str, Any]):
        """インタラクティブ質問セクションを描画"""
        st.divider()
        st.subheader("💭 追加で質問する")

        # 質問入力
        with st.form("interactive_question_form", clear_on_submit=True):
            user_question = st.text_area(
                "文書やQ&Aセッションについて質問してください：",
                placeholder="例: 先ほどの説明で分からなかった部分について詳しく教えてください",
                height=100
            )

            col1, col2 = st.columns([1, 4])
            with col1:
                submit_button = st.form_submit_button("質問する", use_container_width=True)

            if submit_button and user_question.strip():
                # セッション状態に質問を保存
                if 'interactive_questions' not in st.session_state:
                    st.session_state.interactive_questions = []

                # 教師エージェントに質問を送信
                self._process_interactive_question(user_question, session_data)

        # 過去の質問・回答履歴を表示
        if 'interactive_questions' in st.session_state and st.session_state.interactive_questions:
            st.subheader("🗣️ 質問履歴")
            for i, qa in enumerate(reversed(st.session_state.interactive_questions), 1):
                with st.expander(f"追加質問 {len(st.session_state.interactive_questions) - i + 1}: {qa['question'][:50]}...", expanded=i == 1):
                    st.markdown(f"**質問：** {qa['question']}")
                    st.markdown(f"**回答：** {qa['answer']}")
                    if qa.get('timestamp'):
                        st.caption(f"質問時刻: {qa['timestamp']}")

    def _process_interactive_question(self, question: str, session_data: Dict[str, Any]):
        """インタラクティブ質問を処理"""
        from agents.teacher_agent import TeacherAgent
        from services.kernel_service import KernelService, AgentOrchestrator
        from services.session_manager import SessionManager
        import asyncio
        from datetime import datetime

        try:
            with st.spinner("💭 回答を生成中..."):
                # カーネルサービスを初期化
                kernel_service = KernelService()

                # エージェントオーケストレーターを初期化
                orchestrator = AgentOrchestrator(kernel_service)

                # 教師エージェントを初期化
                teacher_agent = TeacherAgent(kernel_service)

                # 文書内容を設定
                document_data = SessionManager.get_document_data()
                document_content = document_data.get('text_content', '')
                teacher_agent.set_document_content(document_content)

                # Q&A履歴を設定
                qa_pairs = session_data.get('qa_pairs', [])
                teacher_agent.set_qa_history(qa_pairs)

                # 質問に対する回答を生成
                prompt = teacher_agent.answer_interactive_question(question)

                # セマンティックカーネルで回答生成
                async def generate_answer():
                    # 教師エージェントのKernelエージェントを取得
                    teacher_kernel_agent = teacher_agent.get_agent()
                    result = await orchestrator.single_agent_invoke(
                        teacher_kernel_agent,
                        prompt
                    )
                    return result

                answer = asyncio.run(generate_answer())

                # 履歴に追加
                qa_entry = {
                    'question': question,
                    'answer': answer,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                # セッション状態に保存
                if 'interactive_questions' not in st.session_state:
                    st.session_state.interactive_questions = []
                st.session_state.interactive_questions.append(qa_entry)

                # 教師エージェントの履歴にも追加
                teacher_agent.add_qa_to_history(question, answer)

                st.success("✅ 回答完了！下の履歴をご確認ください。")
                st.rerun()

        except Exception as e:
            st.error(f"❌ 回答生成エラー: {str(e)}")

    def get_streaming_display(self) -> Optional[StreamingDisplay]:
        """ストリーミング表示オブジェクトを取得"""
        return self.streaming_display
    
    def update_streaming_content(self, agent_name: str, content: str, message_type: str = "normal"):
        """ストリーミング内容を更新"""
        if self.streaming_display:
            self.streaming_display.display_agent_message(agent_name, content, message_type)

    def _render_document_viewer_tab(self, session_data: Dict[str, Any]):
        """文書ビューアータブの内容"""
        from services.session_manager import SessionManager
        import base64

        # 文書データを取得
        document_data = SessionManager.get_document_data()

        if not document_data:
            st.info("📄 文書がアップロードされていません。左のサイドバーからPDFをアップロードするか、テキストを入力してください。")
            return

        # 文書データから必要な情報を取得
        if document_data:
            input_type = document_data.get('input_type', 'unknown')
            text_content = document_data.get('text_content', '')

            # PDFビューアー表示（PDFの場合）
            if input_type == 'pdf' and document_data.get('raw_content'):
                st.markdown("**📄 PDFビューアー**")

                try:
                    # PDFの生データをBase64エンコード
                    pdf_data = document_data.get('raw_content')
                    if isinstance(pdf_data, bytes):
                        b64_pdf = base64.b64encode(pdf_data).decode()
                    else:
                        # 既にBase64エンコードされている場合
                        b64_pdf = pdf_data

                    # PDFビューアーのHTML
                    pdf_display = f"""
                    <div style="width: 100%; height: 600px; border: 1px solid #ddd; border-radius: 5px;">
                        <iframe
                            src="data:application/pdf;base64,{b64_pdf}"
                            width="100%"
                            height="100%"
                            type="application/pdf"
                            style="border: none;">
                            <p>PDFを表示できません。ブラウザがPDF表示をサポートしていない可能性があります。</p>
                        </iframe>
                    </div>
                    """

                    st.markdown(pdf_display, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"PDFの表示でエラーが発生しました: {str(e)}")
                    # エラー時はテキスト表示にフォールバック
                    st.markdown("**📖 抽出されたテキスト**")
                    if text_content:
                        st.text_area(
                            "抽出されたテキスト:",
                            value=text_content,
                            height=400,
                            disabled=True,
                            key="pdf_text_fallback"
                        )
                    else:
                        st.warning("⚠️ 文書内容が取得できませんでした。")

            # テキスト表示（テキスト入力の場合のみ）
            elif input_type == 'text':
                st.markdown("**📖 文書内容（テキスト表示）**")

                # 検索機能
                search_term = st.text_input(
                    "🔍 文書内検索",
                    placeholder="キーワードを入力して文書内を検索...",
                    key="document_search"
                )

                # テキスト入力の場合：検索機能付きシンプル表示
                if text_content:
                    if search_term:
                        # 検索結果の表示
                        if search_term.lower() in text_content.lower():
                            match_count = text_content.lower().count(search_term.lower())
                            st.success(f"🔍 「{search_term}」が{match_count}箇所で見つかりました")

                            # 検索ワードをハイライト
                            import re
                            highlighted_content = re.sub(
                                f'({re.escape(search_term)})',
                                r'<mark style="background-color: #ffeb3b;">\1</mark>',
                                text_content,
                                flags=re.IGNORECASE
                            )
                            st.markdown(highlighted_content, unsafe_allow_html=True)
                        else:
                            st.warning(f"「{search_term}」は文書内に見つかりませんでした")
                            st.text_area(
                                "入力されたテキスト:",
                                value=text_content,
                                height=400,
                                disabled=True,
                                key="text_content_display_no_match"
                            )
                    else:
                        # 検索なしの場合は通常表示
                        st.text_area(
                            "入力されたテキスト:",
                            value=text_content,
                            height=400,
                            disabled=True,
                            key="text_content_display"
                        )
                else:
                    st.warning("⚠️ 文書内容が取得できませんでした。")
        else:
            st.warning("⚠️ 文書データが見つかりませんでした。")

class UploadTab:
    """アップロード・設定タブを管理するクラス"""
    
    def __init__(self):
        self.components = UIComponents()
    
    def render_upload_section(self, sidebar_settings: Dict[str, Any]) -> Dict[str, Any]:
        """アップロード・設定セクションを描画"""
        result = {
            'uploaded_file': None,
            'text_content': None,
            'input_type': None,
            'qa_turns': 10,
            'start_processing': False
        }

        # 入力オプション（PDF or テキスト）
        input_result = self.components.render_input_options()
        result.update(input_result)

        # 何らかの入力がある場合
        if input_result['input_type']:
            # サイドバー設定を結果に統合
            result.update(sidebar_settings)

            # 文書情報を表示（処理後に情報があれば）
            doc_data = st.session_state.get('document_data', {})
            if doc_data:
                self.components.render_document_info(doc_data)

            st.divider()

            # 設定確定と実行ボタン
            from services.session_manager import SessionManager
            is_locked = SessionManager.is_settings_locked()

            if not is_locked:
                # 設定がロックされていない場合：設定確定ボタンを表示
                col1, col2 = st.columns([1, 1])
                with col1:
                    confirm_button = st.button("⚙️ 設定を確定", type="secondary", use_container_width=True)
                    if confirm_button:
                        SessionManager.lock_settings()
                        st.success("✅ 設定を確定しました。実行開始ボタンが表示されます。")
                        st.rerun()

                with col2:
                    if st.button("🔄 リセット", use_container_width=True):
                        # セッションリセットのフラグを設定
                        st.session_state['reset_requested'] = True
                        st.rerun()

                result['start_processing'] = False
                st.info("👆 まず設定を確定してから実行してください")

            else:
                # 設定がロックされている場合：実行開始ボタンを表示
                st.info("🔒 設定が確定されました。実行開始できます。")

                # 実行開始・リセットボタンのグラデーションスタイルを追加
                st.markdown("""
                <style>
                /* 実行開始ボタン（primary）のスタイル */
                div[data-testid="stButton"] > button[kind="primary"] {
                    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 50%, #ff4757 100%) !important;
                    border: 1px solid #ff4757 !important;
                    border-radius: 12px !important;
                    color: white !important;
                    font-weight: 600 !important;
                    backdrop-filter: blur(10px) !important;
                    -webkit-backdrop-filter: blur(10px) !important;
                    box-shadow:
                        0 4px 15px rgba(255, 75, 87, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                }

                div[data-testid="stButton"] > button[kind="primary"]:hover {
                    background: linear-gradient(135deg, #ff7675 0%, #fd79a8 50%, #e84393 100%) !important;
                    transform: translateY(-2px) !important;
                    box-shadow:
                        0 6px 20px rgba(255, 75, 87, 0.4),
                        inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
                }

                /* リセットボタン（secondary）のスタイル */
                div[data-testid="stButton"] > button[kind="secondary"] {
                    background: linear-gradient(135deg, rgba(173, 216, 230, 0.4) 0%, rgba(135, 206, 235, 0.5) 50%, rgba(176, 224, 230, 0.4) 100%) !important;
                    border: 1px solid rgba(173, 216, 230, 0.6) !important;
                    border-radius: 12px !important;
                    color: #2c5aa0 !important;
                    font-weight: 500 !important;
                    backdrop-filter: blur(10px) !important;
                    -webkit-backdrop-filter: blur(10px) !important;
                    box-shadow:
                        0 2px 8px rgba(173, 216, 230, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                }

                div[data-testid="stButton"] > button[kind="secondary"]:hover {
                    background: linear-gradient(135deg, rgba(173, 216, 230, 0.6) 0%, rgba(135, 206, 235, 0.7) 50%, rgba(176, 224, 230, 0.6) 100%) !important;
                    transform: translateY(-2px) !important;
                    box-shadow:
                        0 4px 16px rgba(173, 216, 230, 0.4),
                        inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
                }
                </style>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns([1, 1])
                with col1:
                    start_button = st.button("🚀 実行開始", type="primary", use_container_width=True)

                    # ボタンがクリックされたらセッション状態に保存
                    if start_button:
                        st.session_state['start_button_clicked'] = True

                    # セッション状態の値を返す（瞬間的なボタン値ではなく）
                    result['start_processing'] = start_button or st.session_state.get('start_button_clicked', False)

                with col2:
                    if st.button("🔄 リセット", type="secondary", use_container_width=True):
                        # セッションリセットのフラグを設定
                        st.session_state['reset_requested'] = True
                        # スタートボタンの状態もリセット
                        if 'start_button_clicked' in st.session_state:
                            del st.session_state['start_button_clicked']
                        if 'processing_start_time' in st.session_state:
                            del st.session_state['processing_start_time']
                        st.rerun()

                # 処理完了チェック（シンプル）
                from services.session_manager import SessionManager
                current_step = SessionManager.get_step()

                if current_step == "completed" and SessionManager.get_final_report():
                    st.success("✅ 処理が完了しました！下のタブで結果をご確認ください")
        else:
            # 入力がない場合の詳細説明
            st.info("📄 PDFファイルまたはテキストを入力して、AIエージェントによる文書理解セッションを開始してください")

            # アプリの特徴
            st.markdown("### ✨ このアプリの特徴")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🤖 3つのAIエージェント**")
                st.markdown("- 🎓 **学生エージェント**: 文書について質問を生成")
                st.markdown("- 👨‍🏫 **教師エージェント**: 詳細で分かりやすい回答を提供")
                st.markdown("- 📋 **要約エージェント**: 文書要約と最終レポート作成")

            with col2:
                st.markdown("**📊  主要機能**")
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
                PDFファイルをドラッグ&ドロップ, またはテキスト入力

                **ステップ3: 実行開始**
                🚀ボタンでQ&Aセッション開始
                """)

            with steps_col2:
                st.markdown("**📋 対応ファイル**")
                st.markdown("- **形式**: PDFファイル（.pdf）, テキスト入力")
                st.markdown("- **サイズ**: 最大50MB")
                st.markdown("- **内容**: 論文、レポート、マニュアル等の文書")

            with steps_col3:
                st.markdown("**⚙️ 設定項目**")
                st.markdown("- **Q&A数**: 1-20回（推奨: 10回）")
                st.markdown("- **フォローアップ質問**: 有効/無効")
                st.markdown("- **重要単語**: 優先的に質問生成する単語指定")

            st.divider()

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