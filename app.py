import streamlit as st
import asyncio
from typing import Dict, Any, Optional
import traceback

# 設定とサービスのインポート
from config.settings import Settings
from services.pdf_processor import PDFProcessor
from services.kernel_service import KernelService, AgentOrchestrator
from services.chat_manager import ChatManager, StreamingCallback
from services.session_manager import SessionManager

# エージェントのインポート
from agents.student_agent import StudentAgent
from agents.teacher_agent import TeacherAgent
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
        
        # サービスの初期化
        try:
            self.kernel_service = KernelService()
            self.pdf_processor = PDFProcessor()
            self.chat_manager = ChatManager()
            self.orchestrator = AgentOrchestrator(self.kernel_service)
        except Exception as e:
            st.error(f"サービスの初期化に失敗しました: {str(e)}")
            return
        
        # エージェントの初期化
        try:
            self.student_agent = StudentAgent(self.kernel_service)
            self.teacher_agent = TeacherAgent(self.kernel_service)
            self.summarizer_agent = SummarizerAgent(self.kernel_service)
        except Exception as e:
            st.error(f"エージェントの初期化に失敗しました: {str(e)}")
            return
    
    def run(self):
        """アプリケーションを実行"""
        # ページ設定
        st.set_page_config(
            page_title=self.settings.PAGE_TITLE,
            page_icon=self.settings.PAGE_ICON,
            layout=self.settings.LAYOUT
        )
        
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
        # セッション状態を取得
        current_step = SessionManager.get_step()
        
        try:
            if current_step == "upload":
                self._render_upload_step()
            elif current_step == "processing":
                self._render_processing_step()
            elif current_step == "qa" or current_step == "completed":
                self._render_results_step()
            
            # タブを常に表示（データがある場合）
            if (current_step != "completed" and 
                (SessionManager.get_summary() or SessionManager.get_qa_pairs() or SessionManager.get_final_report())):
                st.divider()
                st.subheader("📊 処理結果")
                self._render_results_step()
                
        except Exception as e:
            st.error(f"アプリケーションエラー: {str(e)}")
            st.code(traceback.format_exc())
    
    def _render_upload_step(self):
        """アップロード・設定ステップを描画"""
        upload_result = self.upload_tab.render_upload_section()
        
        if upload_result['start_processing'] and upload_result['uploaded_file']:
            # ファイル検証
            validation_result = ValidationUtils.validate_pdf_file(upload_result['uploaded_file'])
            
            if not validation_result['is_valid']:
                st.error(validation_result['error_message'])
                return
            
            # 処理設定を収集
            processing_settings = {
                'qa_turns': upload_result['qa_turns'],
                'model_id': upload_result['model_id'],
                'enable_followup': upload_result['enable_followup'],
                'followup_threshold': upload_result['followup_threshold'],
                'max_followups': upload_result['max_followups']
            }
            
            # 処理を開始
            self._start_processing(upload_result['uploaded_file'], processing_settings)
    
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
        
        # 使用モデルを更新
        try:
            self.kernel_service.update_model(processing_settings['model_id'])
            st.info(f"🤖 使用モデル: {processing_settings['model_id']}")
        except Exception as e:
            st.warning(f"モデル設定警告: {str(e)}")
        
        try:
            # ステップ1: PDFを処理
            with st.spinner("📄 PDFファイルを処理中..."):
                pdf_data = self.pdf_processor.process_pdf(uploaded_file)
                SessionManager.set_document_data(pdf_data)
            
            st.success("✅ PDF処理完了")
            
            # 文書情報を表示
            self.components.render_document_info(pdf_data)
            
            # ステップ2: 要約生成
            with st.spinner("📋 文書要約を生成中..."):
                summary = asyncio.run(self._generate_summary(pdf_data['text_content']))
                SessionManager.set_summary(summary)
            
            st.success("✅ 要約生成完了")
            self.components.render_summary_section(summary)
            
            # ステップ3: Q&Aセッションをストリーミング実行
            st.subheader("💬 Q&Aセッション")
            qa_pairs = self._run_streaming_qa_session(pdf_data, processing_settings)
            
            # ステップ4: 最終レポート生成
            with st.spinner("📊 最終レポートを作成中..."):
                final_report = asyncio.run(self._generate_final_report(pdf_data['text_content'], qa_pairs, summary))
                SessionManager.set_final_report(final_report)
            
            st.success("✅ 処理完了！下のタブで結果をご確認ください")
            SessionManager.stop_processing()
            SessionManager.set_step("completed")
            
            # 完了後にタブを表示
            st.divider()
            st.subheader("📊 処理結果")
            self._render_results_step()
            
        except Exception as e:
            st.error(f"処理エラー: {str(e)}")
            SessionManager.stop_processing()
    
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
            SessionManager.set_step("completed")
            
        except Exception as e:
            st.error(f"Q&Aセッション実行エラー: {str(e)}")
            SessionManager.stop_processing()
    
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
        """文書をセクションに分割"""
        # 簡易的な分割（段落ベース）
        paragraphs = content.split('\\n\\n')
        
        # セクション数に合わせて分割
        section_size = max(1, len(paragraphs) // qa_turns)
        sections = []
        
        for i in range(0, len(paragraphs), section_size):
            section = '\\n\\n'.join(paragraphs[i:i+section_size])
            if section.strip():
                sections.append(section)
        
        return sections[:qa_turns]  # 指定されたターン数まで
    
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
    
    def _evaluate_answer_complexity(self, answer: str) -> float:
        """回答の専門度を評価（0.0-1.0のスコア）"""
        # 専門用語の密度を評価
        specialized_terms = [
            # 学術・技術用語の例
            "algorithm", "methodology", "hypothesis", "correlation", "statistical",
            "paradigm", "framework", "implementation", "optimization", "analysis",
            "研究", "手法", "アルゴリズム", "統計", "解析", "実装", "最適化", "パラメータ"
        ]
        
        words = answer.lower().split()
        specialized_count = sum(1 for word in words if any(term in word for term in specialized_terms))
        
        if not words:
            return 0.0
        
        complexity_score = min(1.0, specialized_count / len(words) * 10)  # 専門用語密度を10倍してスケール調整
        
        # 文の長さも考慮（長い文は理解が困難な場合が多い）
        avg_sentence_length = len(words) / max(1, answer.count('.') + answer.count('。'))
        if avg_sentence_length > 20:
            complexity_score += 0.2
        
        return min(1.0, complexity_score)
    
    def _run_streaming_qa_session(self, pdf_data: Dict[str, Any], processing_settings: Dict[str, Any]) -> list:
        """ストリーミング形式でQ&Aセッションを実行（フォローアップ質問機能付き）"""
        qa_pairs = []
        
        # 設定を取得
        qa_turns = processing_settings['qa_turns']
        enable_followup = processing_settings['enable_followup']
        followup_threshold = processing_settings['followup_threshold']
        max_followups = processing_settings['max_followups']
        
        # 文書をセクションに分割
        sections = self._split_document(pdf_data['text_content'], qa_turns)
        self.student_agent.set_document_sections(sections)
        self.teacher_agent.set_document_content(pdf_data['text_content'])
        
        # プログレスバーを作成
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, section in enumerate(sections):
            try:
                # 進捗更新（メインQ&Aのみ）
                main_progress = (i + 1) / len(sections)
                progress_bar.progress(main_progress)
                status_text.text(f"メインQ&A {i+1}/{len(sections)} を生成中...")
                
                # Q&Aペア表示用のコンテナ
                qa_container = st.container()
                
                with qa_container:
                    # メイン質問生成
                    with st.spinner(f"❓ 質問 {i+1} を生成中..."):
                        question_prompt = self.student_agent.process_message("", {
                            "current_section_content": section,
                            "document_content": self.teacher_agent.document_content,
                            "previous_qa": qa_pairs
                        })
                        
                        question = asyncio.run(self.orchestrator.single_agent_invoke(
                            self.student_agent.get_agent(),
                            question_prompt
                        ))
                    
                    # メイン質問表示
                    st.markdown(f"**❓ Q{i+1}:** {question}")
                    
                    # メイン回答生成
                    with st.spinner(f"💡 回答 {i+1} を生成中..."):
                        answer_prompt = self.teacher_agent.process_message(question, {
                            "current_section_content": section,
                            "document_content": self.teacher_agent.document_content,
                            "previous_qa": qa_pairs
                        })
                        
                        answer = asyncio.run(self.orchestrator.single_agent_invoke(
                            self.teacher_agent.get_agent(),
                            answer_prompt
                        ))
                    
                    # メイン回答表示
                    st.markdown(f"**💡 A{i+1}:** {answer}")
                    
                    # メインQ&Aペアを保存
                    main_qa_pair = {
                        "question": question,
                        "answer": answer,
                        "section": i,
                        "type": "main"
                    }
                    qa_pairs.append(main_qa_pair)
                    SessionManager.add_qa_pair(question, answer)
                    
                    # フォローアップ質問の実行（設定が有効な場合のみ）
                    followup_pairs = []
                    if enable_followup:
                        complexity_score = self._evaluate_answer_complexity(answer)
                        if complexity_score >= followup_threshold:
                            status_text.text(f"フォローアップ質問を生成中 (セクション {i+1})...")
                            followup_pairs = self._handle_followup_questions(
                                section, answer, i, qa_pairs, followup_threshold, max_followups
                            )
                    
                    # フォローアップQ&Aを表示・保存
                    for j, followup_pair in enumerate(followup_pairs, 1):
                        st.markdown(f"**❓ Q{i+1}-{j} (フォローアップ):** {followup_pair['question']}")
                        st.markdown(f"**💡 A{i+1}-{j}:** {followup_pair['answer']}")
                        qa_pairs.append(followup_pair)
                        SessionManager.add_qa_pair(followup_pair['question'], followup_pair['answer'])
                    
                    st.divider()
                
            except Exception as e:
                st.error(f"Q&A生成エラー (セクション{i+1}): {str(e)}")
        
        # 完了
        progress_bar.progress(1.0)
        status_text.text("Q&Aセッション完了！")
        
        return qa_pairs
    
    def _handle_followup_questions(self, section: str, initial_answer: str, section_index: int, qa_pairs: list, threshold: float = 0.6, max_followups: int = 3) -> list:
        """フォローアップ質問を処理"""
        followup_pairs = []
        complexity_threshold = threshold
        
        # 初回回答の専門度を評価
        complexity_score = self._evaluate_answer_complexity(initial_answer)
        
        if complexity_score < complexity_threshold:
            return followup_pairs  # 専門度が低い場合はフォローアップなし
        
        current_answer = initial_answer
        
        for followup_count in range(max_followups):
            try:
                # フォローアップ質問生成
                followup_question_prompt = f"""
あなたは好奇心旺盛な学習者です。先生の回答が専門的で理解が難しいため、より簡単に説明してもらいたいと思っています。

先生の回答: {current_answer}

以下の観点でフォローアップ質問を1つ生成してください：
- 専門用語の意味を問う
- 具体例を求める
- より簡単な説明を求める
- 関連する基本概念の説明を求める

質問は自然で学習者らしい表現にしてください。
"""
                
                followup_question = asyncio.run(self.orchestrator.single_agent_invoke(
                    self.student_agent.get_agent(),
                    followup_question_prompt
                ))
                
                # フォローアップ回答生成
                followup_answer_prompt = f"""
学習者からフォローアップ質問を受けました。より理解しやすく、親しみやすい説明をしてください。

質問: {followup_question}
文書セクション: {section}

以下を心がけて回答してください：
- 専門用語は平易な言葉で説明
- 具体例や比喩を使用
- 段階的で理解しやすい構成
- 学習者の知識レベルに合わせた説明
"""
                
                followup_answer = asyncio.run(self.orchestrator.single_agent_invoke(
                    self.teacher_agent.get_agent(),
                    followup_answer_prompt
                ))
                
                # フォローアップペアを保存
                followup_pair = {
                    "question": followup_question,
                    "answer": followup_answer,
                    "section": section_index,
                    "type": "followup",
                    "followup_count": followup_count + 1
                }
                followup_pairs.append(followup_pair)
                
                # 新しい回答の専門度を評価
                new_complexity = self._evaluate_answer_complexity(followup_answer)
                
                # 理解しやすくなった場合は終了
                if new_complexity < complexity_threshold:
                    break
                
                current_answer = followup_answer
                
            except Exception as e:
                st.warning(f"フォローアップ質問 {followup_count + 1} の生成に失敗: {str(e)}")
                break
        
        return followup_pairs

def main():
    """メイン実行関数"""
    try:
        app = QAApp()
        app.run()
    except Exception as e:
        st.error("アプリケーションの起動に失敗しました")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
