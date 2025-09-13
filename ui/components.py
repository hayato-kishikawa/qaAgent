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
    
    def render_prompt_version_settings(self) -> Dict[str, str]:
        """プロンプトバージョン設定を描画"""
        with st.expander("🎯 プロンプトバージョン設定", expanded=False):
            from prompts.prompt_loader import PromptLoader
            prompt_loader = PromptLoader()

            versions = {}
            agent_types = ["student", "teacher", "summarizer", "initial_summarizer"]

            col1, col2 = st.columns(2)

            with col1:
                # 学生エージェント
                student_versions = prompt_loader.get_available_versions("student")
                versions["student_version"] = st.selectbox(
                    "🎓 学生エージェント",
                    student_versions,
                    index=0,
                    key="student_version_select"
                )

                # 先生エージェント
                teacher_versions = prompt_loader.get_available_versions("teacher")
                versions["teacher_version"] = st.selectbox(
                    "👨‍🏫 先生エージェント",
                    teacher_versions,
                    index=0,
                    key="teacher_version_select"
                )

            with col2:
                # 要約エージェント
                summarizer_versions = prompt_loader.get_available_versions("summarizer")
                versions["summarizer_version"] = st.selectbox(
                    "📋 要約エージェント",
                    summarizer_versions,
                    index=0,
                    key="summarizer_version_select"
                )

                # 初期要約エージェント
                initial_summarizer_versions = prompt_loader.get_available_versions("initial_summarizer")
                versions["initial_summarizer_version"] = st.selectbox(
                    "📄 初期要約エージェント",
                    initial_summarizer_versions,
                    index=0,
                    key="initial_summarizer_version_select"
                )

            return versions

    def render_qa_settings(self) -> Dict[str, Any]:
        """Q&A設定を描画"""
        from services.openai_service import OpenAIService
        
        st.subheader("⚙️ Q&A設定")
        
        settings = {}
        
        # Q&Aターン数設定
        settings['qa_turns'] = st.slider(
            "Q&Aターン数",
            min_value=1,
            max_value=20,
            value=10,
            step=1,
            help="生成するQ&Aペアの数を設定してください"
        )
        
        # エージェント別モデル選択
        with st.expander("🤖 エージェント別モデル設定", expanded=False):
            # GPT-5系のみに制限
            gpt5_models = [
                ('GPT-5', 'gpt-5'),
                ('GPT-5 Mini', 'gpt-5-mini'),
                ('GPT-5 Nano', 'gpt-5-nano')
            ]

            # 推奨モデル設定（GPT-5系）
            recommended_models = {
                'student': 'gpt-5-mini',       # 最新軽量モデル
                'teacher': 'gpt-5',            # 最新最高性能モデル
                'summarizer': 'gpt-5-nano'     # 最新超軽量モデル
            }

            # 3つのカラムに分けて表示
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**🎓 学生エージェント**")
                st.caption("質問生成担当")
                student_model = self._render_model_selector(
                    "student_model",
                    gpt5_models,
                    recommended_models['student'],
                    "質問生成に使用するモデル。軽量モデルでも十分な性能を発揮します。"
                )
                settings['student_model'] = student_model

            with col2:
                st.markdown("**👨‍🏫 教師エージェント**")
                st.caption("回答生成担当")
                teacher_model = self._render_model_selector(
                    "teacher_model",
                    gpt5_models,
                    recommended_models['teacher'],
                    "回答生成に使用するモデル。複雑な内容に対応するため高性能モデルを推奨。"
                )
                settings['teacher_model'] = teacher_model

            with col3:
                st.markdown("**📋 要約エージェント**")
                st.caption("要約・レポート作成担当")
                summarizer_model = self._render_model_selector(
                    "summarizer_model",
                    gpt5_models,
                    recommended_models['summarizer'],
                    "要約とレポート作成に使用するモデル。軽量モデルでも十分な性能を発揮します。"
                    )
                settings['summarizer_model'] = summarizer_model
                    
        # フォローアップ設定
        st.divider()
        st.markdown("**🔄 フォローアップ質問設定**")
        
        settings['enable_followup'] = st.checkbox(
            "フォローアップ質問を有効にする",
            value=True,
            key="enable_followup_checkbox",
            help="回答が専門的すぎる場合に、より理解しやすい説明を求める追加質問を自動生成します"
        )
        
        if settings['enable_followup']:
            # 複雑さ閾値の設定
            settings['followup_threshold'] = st.slider(
                "フォローアップ質問の発動閾値", 
                min_value=0.1,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="回答の複雑さがこの閾値を超えた場合にフォローアップ質問を生成します"
            )
            
            # 最大フォローアップ数の設定
            settings['max_followups'] = st.slider(
                "最大フォローアップ質問数",
                min_value=0,
                max_value=3,
                value=1,
                step=1,
                help="1つのQ&Aペアに対する最大フォローアップ質問数"
            )
        else:
            # フォローアップ無効時のデフォルト値
            settings['followup_threshold'] = 0.3  # 調整後のデフォルト値
            settings['max_followups'] = 0

        st.divider()
        
        # 単語登録設定
        st.markdown("**📝 重要単語登録**")
        st.caption("指定した単語について必ず質問を生成します（登録単語数 < Q&Aターン数 にしてください）")
        
        # 単語入力
        keyword_input = st.text_input(
            "重要単語を入力（カンマ区切りで複数入力可能）",
            placeholder="例: 機械学習, ニューラルネットワーク, 深層学習",
            help="これらの単語について優先的に質問が生成されます"
        )
        
        # 入力された単語をリストに変換
        keywords = []
        if keyword_input.strip():
            keywords = [kw.strip() for kw in keyword_input.split(',') if kw.strip()]
        
        settings['target_keywords'] = keywords
        
        # 登録単語数とQ&Aターン数の関係をチェック
        qa_turns = settings.get('qa_turns', 10)
        if keywords and len(keywords) >= qa_turns:
            st.warning(f"⚠️ 登録単語数({len(keywords)})がQ&Aターン数({qa_turns})以上です。単語を減らすかターン数を増やしてください。")
        elif keywords:
            st.success(f"✅ {len(keywords)}個の単語を登録: {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''}")
        
        return settings
    
    def _render_model_selector(self, key: str, model_options: list, default_model: str, help_text: str) -> str:
        """モデル選択セレクトボックスを描画"""
        # セッション状態に値がある場合はそれを使用、なければデフォルト値
        current_value = st.session_state.get(key, default_model)
        
        # デフォルトモデルのインデックスを取得
        default_index = 0
        for i, (name, model_id) in enumerate(model_options):
            if model_id == current_value:
                default_index = i
                break
        
        selected_model_name = st.selectbox(
            "モデル選択",
            options=[name for name, _ in model_options],
            index=default_index,
            key=key,
            help=help_text
        )
        
        # 選択されたモデルのIDを取得
        selected_model_id = next(model_id for name, model_id in model_options if name == selected_model_name)
        st.caption(f"💡 {selected_model_id}")
        
        return selected_model_id
    
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
            import uuid
            if st.button("📋 レポートをコピー", key=f"copy_report_{uuid.uuid4().hex[:8]}"):
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
    
    @staticmethod
    def render_skeleton_summary():
        """要約セクションのスケルトンローディング"""
        st.subheader("📋 文書要約")
        with st.container():
            # テキストのスケルトン表示
            st.markdown("""
            <div style='background: linear-gradient(90deg, #f0f2f6 25%, #e6e6e6 37%, #f0f2f6 63%); 
                        background-size: 400% 100%; animation: shimmer 1.5s ease-in-out infinite;
                        height: 20px; border-radius: 4px; margin: 8px 0;'></div>
            <div style='background: linear-gradient(90deg, #f0f2f6 25%, #e6e6e6 37%, #f0f2f6 63%); 
                        background-size: 400% 100%; animation: shimmer 1.5s ease-in-out infinite;
                        height: 20px; border-radius: 4px; margin: 8px 0; width: 85%;'></div>
            <div style='background: linear-gradient(90deg, #f0f2f6 25%, #e6e6e6 37%, #f0f2f6 63%); 
                        background-size: 400% 100%; animation: shimmer 1.5s ease-in-out infinite;
                        height: 20px; border-radius: 4px; margin: 8px 0; width: 92%;'></div>
            <style>
            @keyframes shimmer {
              0% { background-position: -200% 0; }
              100% { background-position: 200% 0; }
            }
            </style>
            """, unsafe_allow_html=True)
        st.divider()
    
    @staticmethod
    def render_skeleton_qa():
        """Q&Aセクションのスケルトンローディング"""
        st.subheader("💬 Q&Aセッション")
        for i in range(3):  # 3つのスケルトンQ&Aを表示
            with st.expander(f"❓ Q{i+1}: 質問を生成中...", expanded=False):
                st.markdown("""
                <div style='background: linear-gradient(90deg, #f0f2f6 25%, #e6e6e6 37%, #f0f2f6 63%); 
                            background-size: 400% 100%; animation: shimmer 1.5s ease-in-out infinite;
                            height: 16px; border-radius: 4px; margin: 4px 0; width: 70%;'></div>
                <div style='background: linear-gradient(90deg, #f0f2f6 25%, #e6e6e6 37%, #f0f2f6 63%); 
                            background-size: 400% 100%; animation: shimmer 1.5s ease-in-out infinite;
                            height: 16px; border-radius: 4px; margin: 8px 0;'></div>
                <div style='background: linear-gradient(90deg, #f0f2f6 25%, #e6e6e6 37%, #f0f2f6 63%); 
                            background-size: 400% 100%; animation: shimmer 1.5s ease-in-out infinite;
                            height: 16px; border-radius: 4px; margin: 4px 0; width: 88%;'></div>
                """, unsafe_allow_html=True)

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