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
            
            # 処理を開始
            self._start_processing(upload_result['uploaded_file'], upload_result['qa_turns'])
    
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
    
    def _start_processing(self, uploaded_file, qa_turns: int):
        """PDFの処理を開始"""
        SessionManager.start_processing()
        SessionManager.set_qa_turns(qa_turns)
        SessionManager.set_progress("PDFファイルを処理中...", True)
        
        try:
            # PDFを処理
            pdf_data = self.pdf_processor.process_pdf(uploaded_file)
            SessionManager.set_document_data(pdf_data)
            
            # 文書情報を表示
            self.components.render_document_info(pdf_data)
            
            # 非同期でQ&Aセッションを開始
            asyncio.run(self._run_qa_session(pdf_data, qa_turns))
            
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
