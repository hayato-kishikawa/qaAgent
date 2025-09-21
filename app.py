import streamlit as st
import asyncio
from typing import Dict, Any, Optional
import traceback

# 認証のインポート
from auth import check_password, logout

# 設定とサービスのインポート
from config.settings import Settings
from services.pdf_processor import PDFProcessor
from services.text_processor import TextProcessor
from services.kernel_service import KernelService, AgentOrchestrator
from services.chat_manager import ChatManager, StreamingCallback
from services.session_manager import SessionManager

# エージェントのインポート
from agents.student_agent import StudentAgent
from agents.teacher_agent import TeacherAgent
from agents.initial_summarizer_agent import InitialSummarizerAgent
from agents.summarizer_agent import SummarizerAgent

# UIコンポーネントのインポート
from ui.components import UIComponents, StreamingDisplay
from ui.tabs import TabManager, UploadTab, ProcessingTab
from ui.styles import StyleManager

# ユーティリティのインポート
from utils.helpers import TextUtils, ValidationUtils

class QAApp:
    """メインアプリケーションクラス"""
    
    def __init__(self):
        self.settings = Settings()
        self.components = UIComponents()
        self.tab_manager = TabManager()
        self.upload_tab = UploadTab()
        self.processing_tab = ProcessingTab()
        
        # 初期化エラーフラグ
        self.initialization_error = None
        
        # サービスの初期化
        try:
            self.kernel_service = KernelService()
            self.pdf_processor = PDFProcessor()
            self.text_processor = TextProcessor()
            self.chat_manager = ChatManager()
            self.orchestrator = AgentOrchestrator(self.kernel_service)

            # エージェントの事前初期化（最初のアクセス時のみ）
            self._agents_initialized = False
            self.student_agent = None
            self.teacher_agent = None
            self.initial_summarizer_agent = None
            self.summarizer_agent = None

        except Exception as e:
            self.initialization_error = f"サービスの初期化に失敗しました: {str(e)}"
            return
        
    def _initialize_agents_lazy(self, question_level: str = "simple"):
        """エージェントの遅延初期化"""
        if self._agents_initialized and self.student_agent is not None:
            return

        try:
            # 学生エージェントは質問レベルを動的に設定するため、指定レベルで初期化
            self.student_agent = StudentAgent(self.kernel_service, question_level)
            self.teacher_agent = TeacherAgent(self.kernel_service)
            self.initial_summarizer_agent = InitialSummarizerAgent(self.kernel_service)
            self.summarizer_agent = SummarizerAgent(self.kernel_service)

            # 初期化成功を確認
            required_agents = [self.student_agent, self.teacher_agent, self.initial_summarizer_agent, self.summarizer_agent]
            if all(agent is not None for agent in required_agents):
                self._agents_initialized = True
                st.success("✅ 全エージェントの初期化完了")
            else:
                failed_agents = []
                if not self.student_agent: failed_agents.append("学生エージェント")
                if not self.teacher_agent: failed_agents.append("教師エージェント")
                if not self.initial_summarizer_agent: failed_agents.append("初期要約エージェント")
                if not self.summarizer_agent: failed_agents.append("要約エージェント")
                raise Exception(f"以下のエージェントの初期化に失敗: {', '.join(failed_agents)}")

        except Exception as e:
            st.error(f"エージェントの初期化に失敗しました: {str(e)}")
            self._agents_initialized = False
            # フォールバック: 従来の方法で再試行
            self._fallback_agent_initialization(question_level)

    def _fallback_agent_initialization(self, question_level: str = "simple"):
        """フォールバック用のエージェント初期化"""
        try:
            st.warning("エージェントをフォールバックモードで初期化中...")

            # 従来の直接初期化を試行
            from agents.student_agent import StudentAgent
            from agents.teacher_agent import TeacherAgent
            from agents.initial_summarizer_agent import InitialSummarizerAgent
            from agents.summarizer_agent import SummarizerAgent

            self.student_agent = StudentAgent(self.kernel_service, question_level)
            self.teacher_agent = TeacherAgent(self.kernel_service)
            self.initial_summarizer_agent = InitialSummarizerAgent(self.kernel_service)
            self.summarizer_agent = SummarizerAgent(self.kernel_service)

            required_agents = [self.student_agent, self.teacher_agent, self.initial_summarizer_agent, self.summarizer_agent]
            if all(agent is not None for agent in required_agents):
                self._agents_initialized = True
                st.success("✅ フォールバックモードでエージェント初期化完了")
            else:
                failed_agents = []
                if not self.student_agent: failed_agents.append("学生エージェント")
                if not self.teacher_agent: failed_agents.append("教師エージェント")
                if not self.initial_summarizer_agent: failed_agents.append("初期要約エージェント")
                if not self.summarizer_agent: failed_agents.append("要約エージェント")
                st.error(f"フォールバックモードでも初期化に失敗: {', '.join(failed_agents)}")

        except Exception as e:
            st.error(f"フォールバックエージェント初期化エラー: {str(e)}")
            self._agents_initialized = False

    def run(self):
        """アプリケーションを実行"""
        # ページ設定
        st.set_page_config(
            page_title=self.settings.PAGE_TITLE,
            page_icon=self.settings.PAGE_ICON,
            layout=self.settings.LAYOUT
        )
        
        # 認証チェック
        if not check_password():
            return
        
        # サイドバーで設定を描画（ログアウトボタン含む）
        sidebar_settings = self.components.render_sidebar_settings()
        self._cached_sidebar_settings = sidebar_settings
        
        # 初期化エラーチェック
        if self.initialization_error:
            st.error(self.initialization_error)
            st.stop()
        
        # スタイルを適用
        StyleManager.apply_custom_styles()
        
        # セッション管理の初期化
        SessionManager.initialize_session()
        
        # ヘッダーを描画
        self.components.render_header()
        
        # メイン処理
        self._render_main_content()
    
    def _render_main_content(self):
        """メインコンテンツを描画"""
        # 右上にプロンプトプレビューボタンを配置
        col1, col2 = st.columns([8, 2])
        with col2:
            # カスタムスタイルで薄いグレーのボタンを作成
            st.markdown("""
            <style>
            .stButton > button[kind="secondary"] {
                background-color: #f8f9fa !important;
                color: #6c757d !important;
                border: 1px solid #dee2e6 !important;
            }
            .stButton > button[kind="secondary"]:hover {
                background-color: #e9ecef !important;
                color: #495057 !important;
                border: 1px solid #ced4da !important;
            }
            </style>
            """, unsafe_allow_html=True)

            if st.button(" プロンプトプレビュー", use_container_width=True, type="secondary"):
                self._show_prompt_preview_dialog()

        # メインコンテンツ（Q&Aセッションのみ）
        # セッション状態を取得
        current_step = SessionManager.get_step()

        try:
            if current_step == "upload":
                self._render_upload_step()
            elif current_step == "processing":
                self._render_processing_step()
            elif current_step == "qa" or current_step == "completed":
                self._render_results_step()

            # 処理中の進捗表示のみ（完了後はタブで確認）
            pass

        except Exception as e:
            st.error(f"アプリケーションエラー: {str(e)}")
            st.code(traceback.format_exc())
    
    @st.dialog(" プロンプトプレビュー")
    def _show_prompt_preview_dialog(self):
        """プロンプトプレビューをダイアログで表示"""
        try:
            from prompts.prompt_loader import PromptLoader
            prompt_loader = PromptLoader()

            # エージェント選択
            agent_options = [
                ("🎓 学生エージェント", "student"),
                ("👨‍🏫 教師エージェント", "teacher"),
                ("📋 要約エージェント", "summarizer"),
                ("📝 初期要約エージェント", "initial_summarizer")
            ]

            col1, col2 = st.columns(2)

            with col1:
                # エージェント選択UI
                selected_agent_name = st.selectbox(
                    "エージェントを選択",
                    options=[name for name, _ in agent_options],
                    index=0
                )

            with col2:
                # レベル選択UI（学生エージェントの場合のみ）
                selected_agent_type = next(agent_type for name, agent_type in agent_options
                                         if name == selected_agent_name)

                if selected_agent_type == "student":
                    level_options = ["Standard", "Simple", "Beginner"]
                    selected_level = st.selectbox(
                        "質問レベルを選択",
                        options=level_options,
                        index=0
                    )
                else:
                    selected_level = "Standard"
                    st.selectbox(
                        "質問レベル",
                        options=["Standard"],
                        index=0,
                        disabled=True
                    )

            # システムプロンプト表示
            with st.expander(f"🤖 {selected_agent_name} - システムプロンプト", expanded=True):
                try:
                    system_prompt = prompt_loader.get_system_prompt(selected_agent_type, selected_level)
                    st.code(system_prompt, language="markdown")
                    st.caption(f"文字数: {len(system_prompt):,}文字")
                except Exception as e:
                    st.error(f"システムプロンプト読み込みエラー: {str(e)}")

            # ユーザープロンプト表示（学生エージェントの場合のみ）
            if selected_agent_type == "student":
                with st.expander(f"👤 {selected_agent_name} - ユーザープロンプト", expanded=False):
                    try:
                        # サンプルコンテキストでユーザープロンプトを表示
                        sample_context = {
                            "previous_questions": "1. サンプル質問1\n2. サンプル質問2"
                        }
                        user_prompt = prompt_loader.get_user_prompt(selected_agent_type, selected_level, sample_context)
                        if user_prompt:
                            st.code(user_prompt, language="markdown")
                            st.caption(f"文字数: {len(user_prompt):,}文字")
                            st.info("💡 {previous_questions}は動的に過去の質問で置換されます")
                        else:
                            st.info("このエージェントにはユーザープロンプトがありません")
                    except Exception as e:
                        st.error(f"ユーザープロンプト読み込みエラー: {str(e)}")

            # フォローアッププロンプト表示
            with st.expander(f"🔄 フォローアッププロンプト", expanded=False):
                try:
                    prompt_config = prompt_loader.load_prompt(selected_agent_type, selected_level)
                    followup_section = prompt_config.get('followup_question_prompt', {})

                    if followup_section:
                        # フォローアップセクションを構造化して表示
                        followup_parts = []
                        for key, value in followup_section.items():
                            if key.startswith('prompt'):
                                followup_parts.append(value)
                            else:
                                followup_parts.append(value)

                        followup_text = "\n".join(followup_parts)
                        # サンプルコンテキストを適用
                        sample_followup = followup_text.replace("{current_answer}", "サンプル回答内容")
                        st.code(sample_followup, language="markdown")
                        st.caption(f"文字数: {len(sample_followup):,}文字")
                        st.info("💡 {current_answer}は動的に先生の回答で置換されます")
                    else:
                        st.info("このエージェントにはフォローアッププロンプトがありません")
                except Exception as e:
                    st.error(f"フォローアッププロンプト読み込みエラー: {str(e)}")

            # 閉じるボタン
            if st.button("閉じる", use_container_width=True):
                st.rerun()

        except Exception as e:
            st.error(f"プロンプトプレビューエラー: {str(e)}")


    def _generate_system_prompt(self, agent_type: str, level: str = "Standard") -> str:
        """エージェントの実際のシステムプロンプトを生成"""
        from prompts.prompt_loader import PromptLoader
        prompt_loader = PromptLoader()

        try:
            return prompt_loader.get_system_prompt(agent_type, level)
        except Exception as e:
            return f"プロンプト生成エラー: {str(e)}"

    
    def _render_upload_step(self):
        """アップロード・設定ステップを描画"""
        # サイドバー設定を取得（既に描画済み）
        sidebar_settings = getattr(self, '_cached_sidebar_settings', {})
        upload_result = self.upload_tab.render_upload_section(sidebar_settings)

        if upload_result['start_processing'] and (upload_result['uploaded_file'] or upload_result['text_content']):
            # 入力タイプに応じた検証
            if upload_result['input_type'] == 'pdf' and upload_result['uploaded_file']:
                # PDFファイル検証
                validation_result = ValidationUtils.validate_pdf_file(upload_result['uploaded_file'])
                if not validation_result['is_valid']:
                    st.error(validation_result['error_message'])
                    return
            elif upload_result['input_type'] == 'text' and upload_result['text_content']:
                # テキスト検証
                validation_result = self.text_processor.validate_text(upload_result['text_content'])
                if not validation_result['is_valid']:
                    st.error(validation_result['error_message'])
                    return
            else:
                st.error("入力内容が不正です。PDFファイルまたはテキストを入力してください。")
                return

            # 処理設定を収集
            processing_settings = {
                'qa_turns': upload_result['qa_turns'],
                'student_model': upload_result.get('student_model', 'gpt-5-mini'),
                'teacher_model': upload_result.get('teacher_model', 'gpt-5'),
                'summarizer_model': upload_result.get('summarizer_model', 'gpt-5-nano'),
                'enable_followup': upload_result['enable_followup'],
                'followup_threshold': upload_result['followup_threshold'],
                'max_followups': upload_result['max_followups'],
                'target_keywords': upload_result.get('target_keywords', []),
                'student_level': 'Standard',
                'teacher_level': 'Standard',
                'summarizer_level': 'Standard',
                'initial_summarizer_level': 'Standard',
                'quick_mode': upload_result.get('quick_mode', False),
                'input_type': upload_result['input_type']
            }

            # 処理を開始
            if upload_result['input_type'] == 'pdf':
                self._start_processing(upload_result['uploaded_file'], processing_settings)
            else:  # text
                self._start_text_processing(upload_result['text_content'], processing_settings)
    
    def _render_processing_step(self):
        """処理中ステップを描画"""
        show_progress, progress_text = SessionManager.get_progress()
        current_step = SessionManager.get_step()
        
        if show_progress:
            self.processing_tab.render_processing_status(current_step, progress_text)
    
    def _render_results_step(self):
        """結果表示ステップを描画"""
        session_data = {
            'summary': SessionManager.get_summary(),
            'qa_pairs': SessionManager.get_qa_pairs(),
            'final_report': SessionManager.get_final_report(),
            'processing': SessionManager.is_processing(),
            'qa_completed': SessionManager.is_qa_completed()
        }
        
        self.tab_manager.render_main_tabs(session_data)
    
    def _start_processing(self, uploaded_file, processing_settings: Dict[str, Any]):
        """PDFの処理を開始"""
        SessionManager.start_processing()
        SessionManager.set_qa_turns(processing_settings['qa_turns'])

        # 処理設定をセッションに保存
        SessionManager.set_processing_settings(processing_settings)
        
        # エージェント別モデル設定を表示
        model_info = (
            f"🎓 学生: {processing_settings['student_model']} | "
            f"👨‍🏫 教師: {processing_settings['teacher_model']} | "
            f"📋 要約: {processing_settings['summarizer_model']}"
        )
        st.info(f"🤖 {model_info}")

        # エージェント初期化とモデル設定
        try:
            question_level = processing_settings.get('question_level', 'simple')
            self._initialize_agents_lazy(question_level)

            if self._agents_initialized:
                self._configure_agent_models(processing_settings)
            else:
                st.warning("エージェントの初期化に失敗しました。デフォルト設定で続行します。")
        except Exception as e:
            st.warning(f"モデル設定警告: {str(e)}")

        # 全体進捗表示を作成
        overall_progress = st.progress(0)
        overall_status = st.empty()
        step_info = st.empty()

        try:
            # ステップ1: PDFを処理 (0-15%)
            overall_status.text("📄 PDFファイルを処理中...")
            step_info.text("ステップ 1/4: 文書解析")
            overall_progress.progress(5)

            with st.spinner("📄 PDFファイルを処理中..."):
                pdf_data = self.pdf_processor.process_pdf(uploaded_file)
                SessionManager.set_document_data(pdf_data)

            overall_progress.progress(15)
            st.success("✅ PDF処理完了")

            # 文書情報を表示
            self.components.render_document_info(pdf_data)

            # ステップ2: 初期要約を生成 (15-35%)
            overall_status.text("📋 文書要約を生成中...")
            step_info.text("ステップ 2/4: 要約生成")
            overall_progress.progress(20)

            with st.spinner("📋 文書要約を生成中..."):
                initial_summary = asyncio.run(self._generate_initial_summary(pdf_data['text_content']))
                SessionManager.set_summary(initial_summary)

            overall_progress.progress(35)
            st.success("✅ 要約生成完了")
            self.components.render_summary_section(initial_summary)

            # ステップ3: Q&Aセッション実行 (35-85%)
            overall_status.text("💬 Q&Aセッションを実行中...")
            step_info.text("ステップ 3/4: Q&A生成")
            overall_progress.progress(40)

            qa_pairs = asyncio.run(self._run_parallel_qa_only_with_progress(pdf_data, processing_settings, overall_progress, overall_status, step_info, 40, 85))

            overall_progress.progress(85)
            st.success("✅ Q&Aセッション完了")
            
            # ステップ4: 最終レポート生成 (85-100%)
            quick_mode = processing_settings.get('quick_mode', False)
            overall_status.text("📊 最終レポートを作成中...")
            step_info.text("ステップ 4/4: レポート生成")
            overall_progress.progress(90)

            if quick_mode:
                # Quickモードの場合は簡易レポートを生成
                with st.spinner("💨 簡易レポートを作成中..."):
                    document_info = SessionManager.get_document_data()
                    quick_report = UIComponents.generate_quick_report(initial_summary, qa_pairs, document_info)
                    SessionManager.set_final_report(quick_report)
                st.success("✅ 処理完了！Quickモードで簡易レポートを生成しました")
            else:
                # 通常モードの場合はAI生成レポート
                with st.spinner("📊 最終レポートを作成中..."):
                    final_report = asyncio.run(self._generate_final_report(pdf_data['text_content'], qa_pairs, initial_summary))
                    SessionManager.set_final_report(final_report)
                st.success("✅ 処理完了！下のタブで結果をご確認ください")

            # 完了
            overall_progress.progress(100)
            overall_status.text("🎉 全ての処理が完了しました！")
            step_info.text("✅ 完了: 要約 + Q&A + レポート")

            # Quickモード情報をセッションに保存
            st.session_state['quick_mode'] = quick_mode
            SessionManager.stop_processing()
            SessionManager.unlock_settings()  # 設定ロックを解除
            SessionManager.set_step("completed")

            # 完了後にタブを表示
            st.divider()
            self._render_results_step()

        except Exception as e:
            st.error(f"処理エラー: {str(e)}")
            SessionManager.stop_processing()
            SessionManager.unlock_settings()  # エラー時も設定ロックを解除

        finally:
            # 進捗表示をクリア
            if 'overall_progress' in locals():
                overall_progress.empty()
            if 'overall_status' in locals():
                overall_status.empty()
            if 'step_info' in locals():
                step_info.empty()

    def _start_text_processing(self, text_content: str, processing_settings: Dict[str, Any]):
        """テキストの処理を開始"""
        SessionManager.start_processing()
        SessionManager.set_qa_turns(processing_settings['qa_turns'])

        # 処理設定をセッションに保存
        SessionManager.set_processing_settings(processing_settings)

        # エージェント別モデル設定を表示
        model_info = (
            f"🎓 学生: {processing_settings['student_model']} | "
            f"👨‍🏫 教師: {processing_settings['teacher_model']} | "
            f"📋 要約: {processing_settings['summarizer_model']}"
        )
        st.info(f"🤖 {model_info}")

        # エージェント初期化とモデル設定
        try:
            question_level = processing_settings.get('question_level', 'simple')
            self._initialize_agents_lazy(question_level)

            if self._agents_initialized:
                self._configure_agent_models(processing_settings)
            else:
                st.warning("エージェントの初期化に失敗しました。デフォルト設定で続行します。")
        except Exception as e:
            st.warning(f"モデル設定警告: {str(e)}")

        # 全体進捗表示を作成
        overall_progress = st.progress(0)
        overall_status = st.empty()
        step_info = st.empty()

        try:
            # ステップ1: テキストを処理 (0-15%)
            overall_status.text("📝 テキストを処理中...")
            step_info.text("ステップ 1/4: テキスト解析")
            overall_progress.progress(5)

            with st.spinner("📝 テキストを処理中..."):
                text_data = self.text_processor.process_text(text_content)
                SessionManager.set_document_data(text_data)

            overall_progress.progress(15)
            st.success("✅ テキスト処理完了")

            # 文書情報を表示
            self.components.render_document_info(text_data)

            # ステップ2: 初期要約を生成 (15-35%)
            overall_status.text("📋 文書要約を生成中...")
            step_info.text("ステップ 2/4: 要約生成")
            overall_progress.progress(20)

            with st.spinner("📋 文書要約を生成中..."):
                initial_summary = asyncio.run(self._generate_initial_summary(text_data['text_content']))
                SessionManager.set_summary(initial_summary)

            overall_progress.progress(35)
            st.success("✅ 要約生成完了")
            self.components.render_summary_section(initial_summary)

            # ステップ3: Q&Aセッション実行 (35-85%)
            overall_status.text("💬 Q&Aセッションを実行中...")
            step_info.text("ステップ 3/4: Q&A生成")
            overall_progress.progress(40)

            qa_pairs = asyncio.run(self._run_parallel_qa_only_with_progress(text_data, processing_settings, overall_progress, overall_status, step_info, 40, 85))

            overall_progress.progress(85)
            st.success("✅ Q&Aセッション完了")

            # ステップ4: 最終レポート生成 (85-100%)
            quick_mode = processing_settings.get('quick_mode', False)
            overall_status.text("📊 最終レポートを作成中...")
            step_info.text("ステップ 4/4: レポート生成")
            overall_progress.progress(90)

            if quick_mode:
                # Quickモードの場合は簡易レポートを生成
                with st.spinner("💨 簡易レポートを作成中..."):
                    document_info = SessionManager.get_document_data()
                    quick_report = UIComponents.generate_quick_report(initial_summary, qa_pairs, document_info)
                    SessionManager.set_final_report(quick_report)
                st.success("✅ 処理完了！Quickモードで簡易レポートを生成しました")
            else:
                # 通常モードの場合はAI生成レポート
                with st.spinner("📊 最終レポートを作成中..."):
                    final_report = asyncio.run(self._generate_final_report(text_data['text_content'], qa_pairs, initial_summary))
                    SessionManager.set_final_report(final_report)
                st.success("✅ 処理完了！下のタブで結果をご確認ください")

            # 完了
            overall_progress.progress(100)
            overall_status.text("🎉 全ての処理が完了しました！")
            step_info.text("✅ 完了: 要約 + Q&A + レポート")

            # Quickモード情報をセッションに保存
            st.session_state['quick_mode'] = quick_mode
            SessionManager.stop_processing()
            SessionManager.unlock_settings()  # 設定ロックを解除
            SessionManager.set_step("completed")

            # 完了後にタブを表示
            st.divider()
            self._render_results_step()

        except Exception as e:
            st.error(f"処理エラー: {str(e)}")
            SessionManager.stop_processing()
            SessionManager.unlock_settings()  # エラー時も設定ロックを解除

        finally:
            # 進捗表示をクリア
            if 'overall_progress' in locals():
                overall_progress.empty()
            if 'overall_status' in locals():
                overall_status.empty()
            if 'step_info' in locals():
                step_info.empty()
    
    async def _run_qa_session(self, pdf_data: Dict[str, Any], qa_turns: int):
        """Q&Aセッションを実行"""
        try:
            # チャットマネージャーを初期化
            self.chat_manager.start_session(pdf_data)
            
            # 1. 要約を生成
            SessionManager.set_progress("文書要約を生成中...", True)
            summary = await self._generate_summary(pdf_data['text_content'])
            SessionManager.set_summary(summary)
            
            # 2. 文書をセクションに分割
            sections = self._split_document(pdf_data['text_content'], qa_turns)
            self.student_agent.set_document_sections(sections)
            self.teacher_agent.set_document_content(pdf_data['text_content'])
            
            # 3. Q&Aセッションを実行
            SessionManager.set_step("qa")
            SessionManager.set_progress("Q&Aセッションを実行中...", True)
            
            qa_pairs = await self._execute_qa_loop(sections, qa_turns)
            
            # 4. 最終レポートを生成
            SessionManager.set_progress("最終レポートを作成中...", True)
            final_report = await self._generate_final_report(pdf_data['text_content'], qa_pairs, summary)
            SessionManager.set_final_report(final_report)
            
            # 完了
            SessionManager.stop_processing()
            SessionManager.unlock_settings()  # 設定ロックを解除
            SessionManager.set_step("completed")

        except Exception as e:
            st.error(f"Q&Aセッション実行エラー: {str(e)}")
            SessionManager.stop_processing()
            SessionManager.unlock_settings()  # エラー時も設定ロックを解除
    
    async def _generate_summary(self, document_content: str) -> str:
        """文書要約を生成"""
        try:
            prompt = self.summarizer_agent.create_document_summary(document_content)
            summary = await self.orchestrator.single_agent_invoke(
                self.summarizer_agent.get_agent(),
                prompt
            )
            return summary
        except Exception as e:
            return f"要約生成エラー: {str(e)}"
    
    def _split_document(self, content: str, qa_turns: int) -> list:
        """文書をセクションに分割（最適化版）"""
        # 改行による段落分割（効率的な文字列処理）
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        # 段落がない場合は改行で分割
        if not paragraphs:
            paragraphs = [p.strip() for p in content.split('\n') if p.strip()]

        # それでも空の場合は文書全体を使用
        if not paragraphs:
            return [content.strip()] * min(qa_turns, 3)  # 最大3セクションに制限

        # 効率的なセクション作成
        if len(paragraphs) >= qa_turns:
            # 段落数が十分な場合は均等分散
            step = len(paragraphs) // qa_turns
            sections = []
            for i in range(qa_turns):
                start_idx = i * step
                end_idx = min((i + 1) * step, len(paragraphs))
                section_paragraphs = paragraphs[start_idx:end_idx]
                sections.append('\n\n'.join(section_paragraphs))
            return sections
        else:
            # 段落数が少ない場合の最適化
            sections = paragraphs.copy()
            # 不足分は重要な段落を再利用
            while len(sections) < qa_turns:
                # 最も長い段落を優先的に再利用
                longest_para = max(paragraphs, key=len)
                sections.append(longest_para)
            return sections[:qa_turns]
    
    async def _execute_qa_loop(self, sections: list, qa_turns: int) -> list:
        """Q&Aループを実行"""
        qa_pairs = []
        
        for i, section in enumerate(sections):
            try:
                # 質問生成
                question_prompt = self.student_agent.process_message("", {
                    "current_section_content": section,
                    "document_content": self.teacher_agent.document_content,
                    "previous_qa": qa_pairs
                })
                
                question = await self.orchestrator.single_agent_invoke(
                    self.student_agent.get_agent(),
                    question_prompt
                )
                
                # 回答生成
                answer_prompt = self.teacher_agent.process_message(question, {
                    "current_section_content": section,
                    "document_content": self.teacher_agent.document_content,
                    "previous_qa": qa_pairs
                })
                
                answer = await self.orchestrator.single_agent_invoke(
                    self.teacher_agent.get_agent(),
                    answer_prompt
                )
                
                # Q&Aペアを保存
                qa_pair = {
                    "question": question,
                    "answer": answer,
                    "section": i
                }
                qa_pairs.append(qa_pair)
                SessionManager.add_qa_pair(question, answer)
                
                # 進捗を更新
                progress = f"Q&Aセッション進行中... ({i+1}/{len(sections)})"
                SessionManager.set_progress(progress, True)
                
            except Exception as e:
                st.error(f"Q&A生成エラー (セクション{i+1}): {str(e)}")
        
        return qa_pairs
    
    async def _generate_final_report(self, document_content: str, qa_pairs: list, summary: str) -> str:
        """最終レポートを生成"""
        try:
            prompt = self.summarizer_agent.create_final_report(document_content, qa_pairs, summary)
            final_report = await self.orchestrator.single_agent_invoke(
                self.summarizer_agent.get_agent(),
                prompt
            )
            return final_report
        except Exception as e:
            return f"最終レポート生成エラー: {str(e)}"
    
    async def _evaluate_answer_complexity(self, answer: str) -> float:
        """OpenAI APIを使って回答の専門度を評価（0.0-1.0のスコア）"""
        try:
            evaluation_prompt = f"""
以下の文章の専門度・複雑さを0.0から1.0の数値で評価してください。

評価基準：
- 0.0-0.3: 一般の人でも理解しやすい、簡単な説明
- 0.4-0.6: 多少の専門知識が必要だが理解できる
- 0.7-1.0: 高度な専門知識や長い説明で理解が困難

評価対象の文章：
{answer}

数値のみ回答してください（例：0.7）
"""
            
            # 軽量モデルを使用して評価（コスト削減）
            complexity_response = await self.orchestrator.single_agent_invoke(
                self.summarizer_agent.get_agent(),  # 要約エージェントを流用
                evaluation_prompt
            )
            
            # 数値を抽出
            try:
                score = float(complexity_response.strip())
                return max(0.0, min(1.0, score))
            except ValueError:
                # パースできない場合はデフォルト値
                return 0.5
                
        except Exception as e:
            # エラー時はデフォルト値を返す
            return 0.5
    
    
    
    async def _run_parallel_summary_and_qa(self, pdf_data: Dict[str, Any], processing_settings: Dict[str, Any]) -> tuple:
        """要約とQ&Aセッションを並列実行し、要約は完了次第すぐに表示"""
        try:
            # エージェントの遅延初期化
            question_level = processing_settings.get('question_level', 'simple')
            self._initialize_agents_lazy(question_level)

            # 初期化確認してからモデル設定
            if self._agents_initialized:
                self._configure_agent_models(processing_settings)
            else:
                st.error("エージェントの初期化に失敗しました。処理を中止します。")
                return "", []

            # 即時フィードバック（100ms以内）
            st.success("🚀 処理開始 - 文書を解析しています...")
            
            # 詳細な進捗表示
            st.info("⚡ 要約とQ&Aセッションを並列実行中...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            step_text = st.empty()
            
            # プロセス透明性 - 実行予定を明示
            with st.expander("📋 実行プロセス", expanded=False):
                st.markdown("""
                **実行予定:**
                1. 📄 PDF文書をセクション分割
                2. 📋 要約生成（並列実行）
                3. 💬 Q&A生成（並列実行）
                4. 📊 最終レポート作成
                
                **推定時間:** 2-5分（文書の長さにより変動）
                """)
            
            # スケルトンローディングを表示
            skeleton_container = st.empty()
            with skeleton_container:
                self.components.render_skeleton_summary()
                self.components.render_skeleton_qa()
            
            # 要約表示用のプレースホルダーを作成
            summary_container = st.empty()
            
            # タスク作成と進捗更新
            status_text.text("🔄 ステップ1/4: 文書分析と並列タスク準備中...")
            step_text.text("📄 PDFセクション分割完了")
            progress_bar.progress(10)
            
            # 要約タスクを作成
            summary_task = self._generate_summary_async(pdf_data['text_content'])
            
            # Q&Aタスクを作成
            qa_task = self._run_parallel_qa_session(pdf_data, processing_settings)
            
            # 並列実行開始
            status_text.text("🔄 ステップ2-3/4: 要約とQ&Aを並列処理中...")
            step_text.text("⚡ 2つのAIエージェントが同時作業中...")
            progress_bar.progress(30)
            
            # asyncio.as_completedを使用して、完了したタスクから順次処理
            pending = {summary_task, qa_task}
            summary = None
            qa_pairs = []
            
            for task in asyncio.as_completed(pending):
                result = await task
                
                if task == summary_task:
                    # 要約が完了した場合、すぐに表示
                    summary = result
                    if summary:
                        # スケルトンを消去して実際の内容を表示
                        skeleton_container.empty()
                        with summary_container:
                            st.success("✅ ステップ2/4: 要約生成完了")
                            self.components.render_summary_section(summary)
                        SessionManager.set_summary(summary)
                        progress_bar.progress(60)
                        status_text.text("📋 要約表示完了！Q&Aセッション継続中...")
                        step_text.text("📝 文書要約が利用可能になりました")
                
                elif task == qa_task:
                    # Q&Aが完了した場合
                    qa_pairs = result
                    progress_bar.progress(90)
                    status_text.text("💬 ステップ3/4: Q&Aセッション完了！")
                    step_text.text(f"✅ {len(qa_pairs)}個のQ&Aペアを生成しました")
            
            # Q&A結果を表示
            if qa_pairs:
                st.success(f"✅ Q&Aセッション完了 ({len(qa_pairs)}ペア生成)")
                st.subheader("💬 生成されたQ&A")
                
                # Q&Aペアを一つずつ表示
                for i, qa_pair in enumerate(qa_pairs, 1):
                    # フォローアップがある場合はタイトルに含める
                    expander_title = f"Q{i}: {qa_pair['question'][:50]}..."
                    if qa_pair.get('followup_question'):
                        expander_title = f"Q{i}: {qa_pair['question'][:30]}... (+フォローアップ)"

                    with st.expander(expander_title, expanded=True):
                        st.markdown(f"**❓ Q{i} (メイン質問):**")
                        st.write(qa_pair['question'])

                        st.markdown(f"**💡 A{i}:**")
                        st.write(qa_pair['answer'])

                        # フォローアップ質問を表示
                        if qa_pair.get('followup_question'):
                            st.markdown("---")
                            st.markdown(f"**❓ Q{i}-1 (フォローアップ):**")
                            st.write(qa_pair['followup_question'])

                            st.markdown(f"**💡 A{i}-1:**")
                            st.write(qa_pair['followup_answer'])
            
            # 最終ステップ
            progress_bar.progress(100)
            status_text.text("🎉 ステップ4/4: 全ての処理が完了しました！")
            step_text.text("📊 最終レポート準備完了 - タブで確認できます")
            
            # 完了サマリー
            st.balloons()  # 完了のお祝いアニメーション
            st.success(f"✅ 処理完了！要約 + {len(qa_pairs) if qa_pairs else 0}個のQ&A + 最終レポートが準備できました")
            
            return summary, qa_pairs
            
        except asyncio.TimeoutError:
            st.error("⏱️ タイムアウトエラー: 処理に時間がかかりすぎました")
            st.markdown("""
            **対処方法:**
            - 文書が大きすぎる可能性があります（50MB以下を推奨）
            - Q&Aターン数を減らしてみてください
            - しばらく時間をおいて再度お試しください
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 再試行", type="primary"):
                    st.rerun()
            with col2:
                if st.button("⚙️ 設定を変更"):
                    st.session_state.current_step = "upload"
                    st.rerun()
            
            return "", []
            
        except Exception as e:
            st.error(f"❌ 処理エラーが発生しました: {str(e)}")
            st.markdown("""
            **一般的な解決方法:**
            - OpenAI APIキーが正しく設定されているか確認
            - インターネット接続を確認
            - ファイルが破損していないか確認
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 再試行", type="primary", key="retry_general"):
                    st.rerun()
            with col2:
                if st.button("⚙️ 設定を変更", key="reset_general"):
                    st.session_state.current_step = "upload"
                    st.rerun()
            
            return "", []
    
    async def _generate_initial_summary(self, document_content: str) -> str:
        """初期要約を生成（新しいエージェント使用）"""
        try:
            prompt = self.initial_summarizer_agent.create_document_summary(document_content)
            initial_summary = await self.orchestrator.single_agent_invoke(
                self.initial_summarizer_agent.get_agent(),
                prompt
            )
            return initial_summary
        except Exception as e:
            return f"初期要約生成エラー: {str(e)}"
    
    async def _run_parallel_qa_only(self, pdf_data: Dict[str, Any], processing_settings: Dict[str, Any]) -> list:
        """Q&Aセッションのみを並列実行（結果を順次表示）"""
        try:
            # 設定を取得
            qa_turns = processing_settings['qa_turns']
            enable_followup = processing_settings['enable_followup']
            followup_threshold = processing_settings['followup_threshold']
            max_followups = processing_settings['max_followups']
            target_keywords = processing_settings.get('target_keywords', [])
            
            # 使用済み単語を追跡
            used_keywords = set()
            
            # 文書をセクションに分割
            sections = self._split_document(pdf_data['text_content'], qa_turns)
            self.student_agent.set_document_sections(sections)
            self.teacher_agent.set_document_content(pdf_data['text_content'])
            
            # プログレスバーとリアルタイム表示エリアを作成
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # リアルタイム結果表示用のコンテナ
            results_container = st.container()
            with results_container:
                st.subheader("💬 Q&A結果")
                result_placeholder = st.empty()
            
            qa_pairs = []
            completed_count = 0
            total_sections = len(sections)
            
            # 全セクションのタスクを一度に作成
            all_tasks = []
            section_info = []  # セクション情報を保存
            
            for section_index, section in enumerate(sections):
                # 使用する単語を決定（単語登録がある場合は優先）
                target_keyword = None
                if target_keywords and len(used_keywords) < len(target_keywords):
                    # まだ使っていない単語を選択
                    available_keywords = [kw for kw in target_keywords if kw not in used_keywords]
                    if available_keywords:
                        target_keyword = available_keywords[0]
                        used_keywords.add(target_keyword)
                
                task = self._process_section_async(section, section_index, [], 
                                                 enable_followup, followup_threshold, max_followups,
                                                 target_keyword)
                all_tasks.append(task)
                section_info.append({"section_index": section_index, "target_keyword": target_keyword})
            
            # 順序を保持して処理（asyncio.gatherを使用）
            status_text.text(f"全{total_sections}セクションを並列処理中...")

            try:
                # 順序を保持しながら並列実行
                results = await asyncio.gather(*all_tasks, return_exceptions=True)

                for i, result in enumerate(results):
                    completed_count += 1

                    if isinstance(result, Exception):
                        st.error(f"セクション{i+1}処理エラー: {str(result)}")
                    elif result:
                        qa_pairs.extend(result)

                        # セッションにも追加
                        for qa_pair in result:
                            # メイン質問とフォローアップをセットで追加
                            qa_data = {
                                'question': qa_pair['question'],
                                'answer': qa_pair['answer'],
                                'followup_question': qa_pair.get('followup_question', ''),
                                'followup_answer': qa_pair.get('followup_answer', '')
                            }
                            SessionManager.add_qa_pair_with_followup(qa_data)
                        
                        # 累積結果を表示（全てのQ&Aペアを再表示）
                        with result_placeholder.container():
                            for i, qa_pair in enumerate(qa_pairs):
                                qa_num = i + 1
                                with st.expander(f"🔍 Q&A {qa_num}: {qa_pair['question'][:50]}...", expanded=False):
                                    st.markdown(f"**❓ Q{qa_num} (メイン質問):**")
                                    st.write(f"{qa_pair['question']}")

                                    st.markdown(f"**💡 A{qa_num}:**")
                                    st.write(f"{qa_pair['answer']}")
                                    
                                    # フォローアップ質問を関連性を明確にして表示
                                    if qa_pair.get('followup_question'):
                                        st.markdown(f"**🔄 Q{qa_num}-1 (フォローアップ):**")
                                        st.markdown(f"→ {qa_pair['followup_question']}")

                                        st.markdown(f"**💡 A{qa_num}-1:**")
                                        st.markdown(f"→ {qa_pair['followup_answer']}")
                                    
                                    # キャプション情報（セクションと専門性スコア）
                                    caption_parts = []
                                    section = qa_pair.get('section', 'N/A')
                                    if section != 'N/A':
                                        caption_parts.append(f"セクション: {section}")
                                    
                                    complexity_score = qa_pair.get('complexity_score', 'N/A')
                                    if complexity_score != 'N/A':
                                        caption_parts.append(f"専門性: {complexity_score}")
                                    
                                    if caption_parts:
                                        st.caption(" | ".join(caption_parts))
                    
                    # 進捗更新
                    progress = completed_count / total_sections
                    progress_bar.progress(progress)
                    status_text.text(f"完了: {completed_count}/{total_sections} セクション")

            except Exception as e:
                st.error(f"並列処理エラー: {str(e)}")
            
            # 完了
            progress_bar.progress(1.0)
            status_text.text("Q&Aセッション完了！")
            
            return qa_pairs
            
        except Exception as e:
            st.error(f"Q&A並列処理エラー: {str(e)}")
            return []
    
    async def _generate_summary_async(self, document_content: str) -> str:
        """文書要約を非同期生成"""
        try:
            prompt = self.summarizer_agent.create_document_summary(document_content)
            summary = await self.orchestrator.single_agent_invoke(
                self.summarizer_agent.get_agent(),
                prompt
            )
            return summary
        except Exception as e:
            return f"要約生成エラー: {str(e)}"
    
    def _configure_agent_models(self, processing_settings: Dict[str, Any]):
        """各エージェントのモデルとプロンプトバージョンを個別設定"""
        try:
            # 学生エージェントの設定
            if self.student_agent:
                self.student_agent.set_model(processing_settings['student_model'])
                # プロンプトレベル設定は新しいシステムで動的に処理されるため、ここでは不要
            else:
                st.warning("モデル設定警告: 学生エージェントが初期化されていません")

            # 教師エージェントの設定
            if self.teacher_agent:
                self.teacher_agent.set_model(processing_settings['teacher_model'])
                # プロンプトレベル設定は新しいシステムで動的に処理されるため、ここでは不要
            else:
                st.warning("モデル設定警告: 教師エージェントが初期化されていません")

            # 初期要約エージェントの設定
            if self.initial_summarizer_agent:
                self.initial_summarizer_agent.set_model(processing_settings['summarizer_model'])
                # プロンプトレベル設定は新しいシステムで動的に処理されるため、ここでは不要
            else:
                st.warning("モデル設定警告: 初期要約エージェントが初期化されていません")

            # 最終レポート要約エージェントの設定
            if self.summarizer_agent:
                self.summarizer_agent.set_model(processing_settings['summarizer_model'])
                # プロンプトレベル設定は新しいシステムで動的に処理されるため、ここでは不要
            else:
                st.warning("モデル設定警告: 要約エージェントが初期化されていません")

        except Exception as e:
            st.error(f"モデル設定エラー: {str(e)}")
            # エージェント再初期化を試行
            self._initialize_agents_lazy(processing_settings.get('question_level', 'simple'))
    
    async def _run_parallel_qa_session(self, pdf_data: Dict[str, Any], processing_settings: Dict[str, Any]) -> list:
        """並列処理を活用したQ&Aセッション実行"""
        qa_pairs = []
        
        # 設定を取得
        qa_turns = processing_settings['qa_turns']
        enable_followup = processing_settings['enable_followup']
        followup_threshold = processing_settings['followup_threshold']
        max_followups = processing_settings['max_followups']
        target_keywords = processing_settings.get('target_keywords', [])
        
        # 使用済み単語を追跡
        used_keywords = set()
        
        # 文書をセクションに分割
        sections = self._split_document(pdf_data['text_content'], qa_turns)
        self.student_agent.set_document_sections(sections)
        self.teacher_agent.set_document_content(pdf_data['text_content'])
        
        # プログレスバーを作成
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # セクションを並列処理用にバッチ分け（3セクションずつ）
        batch_size = 3
        for batch_start in range(0, len(sections), batch_size):
            batch_sections = sections[batch_start:batch_start + batch_size]
            batch_tasks = []
            
            # 並列タスクを作成
            for i, section in enumerate(batch_sections):
                section_index = batch_start + i
                
                # 使用する単語を決定（単語登録がある場合は優先）
                target_keyword = None
                if target_keywords and len(used_keywords) < len(target_keywords):
                    # まだ使っていない単語を選択
                    available_keywords = [kw for kw in target_keywords if kw not in used_keywords]
                    if available_keywords:
                        target_keyword = available_keywords[0]
                        used_keywords.add(target_keyword)
                
                task = self._process_section_async(section, section_index, qa_pairs, 
                                                 enable_followup, followup_threshold, max_followups,
                                                 target_keyword)
                batch_tasks.append(task)
            
            # 並列実行
            status_text.text(f"セクション {batch_start+1}-{min(batch_start+batch_size, len(sections))} を並列処理中...")
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 結果を処理
            for result in batch_results:
                if isinstance(result, Exception):
                    st.error(f"並列処理エラー: {str(result)}")
                else:
                    qa_pairs.extend(result)
                    
                    # StreamlitのセッションにQ&Aペアを追加
                    for qa_pair in result:
                        SessionManager.add_qa_pair(qa_pair['question'], qa_pair['answer'])
            
            # 進捗更新
            progress = min(1.0, (batch_start + batch_size) / len(sections))
            progress_bar.progress(progress)
        
        # 完了
        progress_bar.progress(1.0)
        status_text.text("並列Q&Aセッション完了！")
        
        return qa_pairs
    
    async def _process_section_async(self, section: str, section_index: int, previous_qa: list,
                                   enable_followup: bool, followup_threshold: float, max_followups: int,
                                   target_keyword: str = None, semaphore: asyncio.Semaphore = None) -> list:
        """セクション処理の非同期版（セマフォ制御付き）"""
        if semaphore:
            async with semaphore:
                return await self._process_section_internal(section, section_index, previous_qa,
                                                          enable_followup, followup_threshold, max_followups,
                                                          target_keyword)
        else:
            return await self._process_section_internal(section, section_index, previous_qa,
                                                      enable_followup, followup_threshold, max_followups,
                                                      target_keyword)

    async def _process_section_internal(self, section: str, section_index: int, previous_qa: list,
                                      enable_followup: bool, followup_threshold: float, max_followups: int,
                                      target_keyword: str = None) -> list:
        """セクション処理の内部実装"""
        section_qa_pairs = []
        
        try:
            # 並列で質問と前のセクションの処理を実行
            question_task = self._generate_question_async(section, previous_qa, target_keyword)
            
            # 質問生成を待つ
            question = await question_task
            
            # 回答生成
            answer = await self._generate_answer_async(question, section, previous_qa)
            
            # メインQ&Aペア
            main_qa_pair = {
                "question": question,
                "answer": answer,
                "section": section_index,
                "type": "main"
            }
            section_qa_pairs.append(main_qa_pair)
            
            # フォローアップ質問（必要な場合）
            if enable_followup:
                complexity_score = await self._evaluate_answer_complexity(answer)
                if complexity_score >= followup_threshold:
                    followup_pairs = await self._handle_followup_questions_async(
                        section, answer, section_index, previous_qa, followup_threshold, max_followups
                    )
                    # フォローアップ質問があった場合は、メインQ&Aペアに追加
                    if followup_pairs:
                        first_followup = followup_pairs[0]  # 最初のフォローアップのみ使用
                        main_qa_pair["followup_question"] = first_followup["question"]
                        main_qa_pair["followup_answer"] = first_followup["answer"]
                        main_qa_pair["complexity_score"] = complexity_score
                    
        except Exception as e:
            st.error(f"セクション{section_index+1}の処理エラー: {str(e)}")
        
        return section_qa_pairs

    def _format_previous_questions(self, previous_qa: list) -> str:
        """過去の質問を適切にフォーマット（全て）"""
        if not previous_qa:
            return "まだ質問はありません。"

        formatted_questions = []
        for i, qa_pair in enumerate(previous_qa, 1):
            question = qa_pair.get('question', '')
            if question:
                # 質問を50文字以内に要約
                if len(question) > 50:
                    question = question[:47] + "..."
                formatted_questions.append(f"{i}. {question}")

        return "\n".join(formatted_questions) if formatted_questions else "まだ質問はありません。"

    async def _generate_question_async(self, section: str, previous_qa: list, target_keyword: str = None) -> str:
        """質問を非同期生成"""
        if not self.student_agent:
            raise Exception("学生エージェントが初期化されていません")
        if not self.teacher_agent:
            raise Exception("教師エージェントが初期化されていません")

        # 過去の質問をフォーマット
        previous_questions_text = self._format_previous_questions(previous_qa)

        # prompt_loaderを使用して動的にユーザープロンプトを生成
        from prompts.prompt_loader import PromptLoader
        prompt_loader = PromptLoader()

        # 学生エージェントのレベル設定を取得（デフォルトはStandard）
        question_level = getattr(self.student_agent, 'question_level', 'standard')


        # ユーザープロンプトにコンテキストを埋め込み
        context = {
            "previous_questions": previous_questions_text,
            "current_section_content": section,
            "document_content": self.teacher_agent.document_content
        }

        # 単語指定がある場合はコンテキストに追加
        if target_keyword:
            context["target_keyword"] = target_keyword

        user_prompt = prompt_loader.get_user_prompt("student", question_level, context)

        # 文書セクションを追加
        full_user_prompt = f"{user_prompt}\n\n文書セクション:\n{section}"

        return await self.orchestrator.single_agent_invoke(
            self.student_agent.get_agent(),
            full_user_prompt
        )
    
    async def _generate_answer_async(self, question: str, section: str, previous_qa: list) -> str:
        """回答を非同期生成"""
        if not self.teacher_agent:
            raise Exception("教師エージェントが初期化されていません")

        answer_prompt = self.teacher_agent.process_message(question, {
            "current_section_content": section,
            "document_content": self.teacher_agent.document_content,
            "previous_qa": previous_qa
        })

        return await self.orchestrator.single_agent_invoke(
            self.teacher_agent.get_agent(),
            answer_prompt
        )
    
    async def _handle_followup_questions_async(self, section: str, initial_answer: str, section_index: int, 
                                             qa_pairs: list, threshold: float, max_followups: int) -> list:
        """フォローアップ質問の非同期処理"""
        followup_pairs = []
        current_answer = initial_answer
        
        for followup_count in range(max_followups):
            try:
                # フォローアップ質問と回答を並列生成
                followup_question_task = self._generate_followup_question_async(current_answer)
                followup_question = await followup_question_task
                
                followup_answer = await self._generate_followup_answer_async(followup_question, section)
                
                # フォローアップペア
                followup_pair = {
                    "question": followup_question,
                    "answer": followup_answer,
                    "section": section_index,
                    "type": "followup",
                    "followup_count": followup_count + 1
                }
                followup_pairs.append(followup_pair)
                
                # 複雑度評価
                new_complexity = await self._evaluate_answer_complexity(followup_answer)
                if new_complexity < threshold:
                    break
                    
                current_answer = followup_answer
                
            except Exception as e:
                st.warning(f"フォローアップ質問 {followup_count + 1} の生成に失敗: {str(e)}")
                break
        
        return followup_pairs
    
    async def _generate_followup_question_async(self, current_answer: str) -> str:
        """フォローアップ質問を非同期生成"""
        from prompts.prompt_loader import PromptLoader
        prompt_loader = PromptLoader()

        # followup_question_promptセクションを取得
        prompt_config = prompt_loader.load_prompt("student", "Standard")
        followup_prompt_section = prompt_config.get('followup_question_prompt', {})

        if not followup_prompt_section:
            raise ValueError("followup_question_promptセクションが見つかりません")

        # followup_question_promptセクションを構造化して構築
        followup_prompt_parts = []
        for key, value in followup_prompt_section.items():
            if key.startswith('prompt'):
                followup_prompt_parts.append(value)
            else:
                followup_prompt_parts.append(value)

        followup_prompt_template = "\n".join(followup_prompt_parts)
        followup_question_prompt = followup_prompt_template.replace("{current_answer}", current_answer)

        return await self.orchestrator.single_agent_invoke(
            self.student_agent.get_agent(),
            followup_question_prompt
        )
    
    async def _generate_followup_answer_async(self, followup_question: str, section: str) -> str:
        """フォローアップ回答を非同期生成"""
        from prompts.prompt_loader import PromptLoader
        prompt_loader = PromptLoader()

        # teacherのfollowup_answer_promptセクションを取得
        prompt_config = prompt_loader.load_prompt("teacher", "standard")
        followup_answer_section = prompt_config.get('followup_answer_prompt', {})

        if not followup_answer_section:
            raise ValueError("followup_answer_promptセクションが見つかりません")

        # followup_answer_promptセクションを構造化して構築
        followup_prompt_parts = []
        for key, value in followup_answer_section.items():
            if key.startswith('prompt'):
                followup_prompt_parts.append(value)
            else:
                followup_prompt_parts.append(value)

        followup_prompt_template = "\n".join(followup_prompt_parts)
        followup_answer_prompt = followup_prompt_template.replace("{followup_question}", followup_question).replace("{section}", section)

        return await self.orchestrator.single_agent_invoke(
            self.teacher_agent.get_agent(),
            followup_answer_prompt
        )

    async def _run_parallel_qa_only_with_progress(self, pdf_data: Dict[str, Any], processing_settings: Dict[str, Any],
                                                  overall_progress, overall_status, step_info, start_percent: int, end_percent: int) -> list:
        """Q&Aセッションのみを並列実行（全体進捗に反映）"""
        try:
            # 設定を取得
            qa_turns = processing_settings['qa_turns']
            enable_followup = processing_settings['enable_followup']
            followup_threshold = processing_settings['followup_threshold']
            max_followups = processing_settings['max_followups']
            target_keywords = processing_settings.get('target_keywords', [])
            question_level = processing_settings.get('question_level', 'beginner')

            # 学生エージェントの質問レベルを設定
            if self.student_agent:
                self.student_agent.set_question_level(question_level)
            else:
                st.error("Q&A並列処理エラー: 学生エージェントが初期化されていません")
                # エージェント再初期化を試行
                self._initialize_agents_lazy(question_level)
                if self.student_agent:
                    self.student_agent.set_question_level(question_level)
                else:
                    raise Exception("学生エージェントの初期化に失敗しました")

            # 使用済み単語を追跡
            used_keywords = set()

            # 文書をセクションに分割
            sections = self._split_document(pdf_data['text_content'], qa_turns)
            self.student_agent.set_document_sections(sections)
            self.teacher_agent.set_document_content(pdf_data['text_content'])

            # リアルタイム結果表示用のコンテナ
            results_container = st.container()
            with results_container:
                st.subheader("💬 Q&A結果")
                result_placeholder = st.empty()

                # 初期ローディング表示
                with result_placeholder.container():
                    st.markdown("""
                    <div style="
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        padding: 40px;
                        background: linear-gradient(90deg, #f8f9ff 0%, #ffffff 100%);
                        border-radius: 12px;
                        border: 1px solid rgba(173, 216, 230, 0.3);
                    ">
                        <div style="text-align: center;">
                            <div style="
                                width: 40px;
                                height: 40px;
                                border: 4px solid #e3f2fd;
                                border-top: 4px solid #1f77b4;
                                border-radius: 50%;
                                animation: spin 1s linear infinite;
                                margin: 0 auto 15px auto;
                            "></div>
                            <p style="
                                color: #1f77b4;
                                font-size: 16px;
                                font-weight: 500;
                                margin: 0;
                            ">🤖 AIがQ&Aを生成中...</p>
                            <p style="
                                color: #666;
                                font-size: 14px;
                                margin: 5px 0 0 0;
                            ">結果は順次表示されます</p>
                        </div>
                    </div>
                    <style>
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                    </style>
                    """, unsafe_allow_html=True)

            qa_pairs = []
            completed_count = 0
            total_sections = len(sections)

            # 同時接続数を制限するセマフォ（OpenAI API制限に配慮）
            semaphore = asyncio.Semaphore(3)  # 最大3並列

            # 全セクションのタスクを一度に作成
            all_tasks = []
            section_info = []

            for section_index, section in enumerate(sections):
                # 使用する単語を決定
                target_keyword = None
                if target_keywords and len(used_keywords) < len(target_keywords):
                    available_keywords = [kw for kw in target_keywords if kw not in used_keywords]
                    if available_keywords:
                        target_keyword = available_keywords[0]
                        used_keywords.add(target_keyword)

                task = self._process_section_async(section, section_index, [],
                                                 enable_followup, followup_threshold, max_followups,
                                                 target_keyword, semaphore)
                all_tasks.append(task)
                section_info.append({"section_index": section_index, "target_keyword": target_keyword})

            # 順序を保持して処理
            overall_status.text(f"💬 全{total_sections}セクションを並列処理中...")

            try:
                # 順序を保持しながら並列実行
                results = await asyncio.gather(*all_tasks, return_exceptions=True)

                for i, result in enumerate(results):
                    completed_count += 1

                    if isinstance(result, Exception):
                        st.error(f"セクション{i+1}処理エラー: {str(result)}")
                    elif result:
                        qa_pairs.extend(result)

                        # セッションにも追加
                        for qa_pair in result:
                            # メイン質問とフォローアップをセットで追加
                            qa_data = {
                                'question': qa_pair['question'],
                                'answer': qa_pair['answer'],
                                'followup_question': qa_pair.get('followup_question', ''),
                                'followup_answer': qa_pair.get('followup_answer', '')
                            }
                            SessionManager.add_qa_pair_with_followup(qa_data)

                        # バッチ更新（5セクションごとまたは最終セクション）
                        if completed_count % 5 == 0 or completed_count == total_sections:
                            with result_placeholder.container():
                                st.info(f"✅ {len(qa_pairs)}個のQ&Aが完了しました （{completed_count}/{total_sections} セクション処理済み）")

                                # 処理中の場合のみシンプルな表示
                                if completed_count < total_sections:
                                    st.markdown("🔄 引き続きQ&Aを生成中...")

                            # 全体進捗を更新
                            progress_percent = start_percent + (end_percent - start_percent) * (completed_count / total_sections)
                            overall_progress.progress(int(progress_percent))
                            overall_status.text(f"💬 Q&A完了: {completed_count}/{total_sections} セクション")
                            step_info.text(f"ステップ 3/4: Q&A生成 ({completed_count}/{total_sections})")

            except Exception as e:
                st.error(f"並列処理エラー: {str(e)}")

            # 完了
            overall_status.text(f"✅ Q&Aセッション完了！{len(qa_pairs)}ペア生成")

            return qa_pairs

        except Exception as e:
            st.error(f"Q&A並列処理エラー: {str(e)}")
            return []

def main():
    """メイン実行関数"""
    try:
        app = QAApp()
        app.run()
    except Exception:
        st.error("アプリケーションの起動に失敗しました")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
