import streamlit as st

class StyleManager:
    """アプリケーションのスタイルを管理するクラス"""
    
    @staticmethod
    def apply_custom_styles():
        """カスタムCSSスタイルを適用"""
        st.markdown("""
        <style>
        /* メインコンテナのスタイル */
        .main {
            padding-top: 2rem;
        }
        
        /* ヘッダーのスタイル */
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        
        .main-header h1 {
            color: white;
            margin: 0;
            text-align: center;
        }
        
        /* Q&Aセクションのスタイル */
        .qa-section {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            border-left: 4px solid #007bff;
        }
        
        .question-block {
            background-color: #e3f2fd;
            padding: 0.8rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            border-left: 3px solid #2196f3;
        }
        
        .answer-block {
            background-color: #f3e5f5;
            padding: 0.8rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 3px solid #9c27b0;
        }
        
        /* ボタンのスタイル */
        .stButton > button {
            border-radius: 8px;
            border: none;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        /* プライマリボタン */
        .stButton > button[data-baseweb="button"][data-testid="baseButton-primary"] {
            background: linear-gradient(45deg, #007bff, #0056b3);
        }
        
        /* ファイルアップローダーのスタイル */
        .uploadedFile {
            border: 2px dashed #007bff;
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
            margin: 1rem 0;
        }
        
        /* メトリックカードのスタイル */
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
            margin: 0.5rem 0;
        }
        
        /* プログレスバーのスタイル */
        .stProgress .st-bo {
            background: linear-gradient(90deg, #007bff, #28a745);
        }
        
        /* サイドバーのスタイル */
        .css-1d391kg {
            background-color: #f8f9fa;
        }
        
        /* タブのスタイル */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding: 0 24px;
            background-color: #f1f3f4;
            border-radius: 8px 8px 0 0;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #007bff;
            color: white;
        }
        
        /* エキスパンダーのスタイル */
        .streamlit-expanderHeader {
            background-color: #f8f9fa;
            border-radius: 8px;
            font-weight: 500;
        }
        
        /* アラートのスタイル */
        .stAlert {
            border-radius: 8px;
            font-weight: 500;
        }
        
        /* 成功メッセージ */
        .stSuccess {
            background-color: #d4edda;
            border-color: #c3e6cb;
            color: #155724;
        }
        
        /* エラーメッセージ */
        .stError {
            background-color: #f8d7da;
            border-color: #f5c6cb;
            color: #721c24;
        }
        
        /* 警告メッセージ */
        .stWarning {
            background-color: #fff3cd;
            border-color: #ffeaa7;
            color: #856404;
        }
        
        /* 情報メッセージ */
        .stInfo {
            background-color: #d1ecf1;
            border-color: #bee5eb;
            color: #0c5460;
        }
        
        /* スピナーのスタイル */
        .stSpinner {
            text-align: center;
            margin: 2rem 0;
        }
        
        /* マークダウンのスタイル */
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #333;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
        }
        
        .stMarkdown h1 {
            border-bottom: 2px solid #007bff;
            padding-bottom: 0.3rem;
        }
        
        .stMarkdown h2 {
            color: #007bff;
        }
        
        .stMarkdown code {
            background-color: #f8f9fa;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            border: 1px solid #e9ecef;
        }
        
        .stMarkdown pre {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            overflow-x: auto;
        }
        
        /* レスポンシブデザイン */
        @media (max-width: 768px) {
            .main {
                padding: 1rem;
            }
            
            .stColumns {
                flex-direction: column;
            }
            
            .metric-card {
                margin: 0.25rem 0;
            }
        }
        
        /* ダークモード対応 */
        @media (prefers-color-scheme: dark) {
            .qa-section {
                background-color: #2d3748;
                color: white;
            }
            
            .question-block {
                background-color: #2a4365;
                color: white;
            }
            
            .answer-block {
                background-color: #553c9a;
                color: white;
            }
            
            .metric-card {
                background-color: #2d3748;
                color: white;
            }
        }
        
        /* アニメーション */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .fade-in {
            animation: fadeIn 0.5s ease-out;
        }
        
        /* ホバーエフェクト */
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: all 0.3s ease;
        }
        
        /* カスタムアイコン */
        .icon-success::before {
            content: "✅";
            margin-right: 0.5rem;
        }
        
        .icon-error::before {
            content: "❌";
            margin-right: 0.5rem;
        }
        
        .icon-warning::before {
            content: "⚠️";
            margin-right: 0.5rem;
        }
        
        .icon-info::before {
            content: "ℹ️";
            margin-right: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def create_custom_component(content: str, component_type: str = "default") -> str:
        """カスタムHTMLコンポーネントを作成"""
        component_classes = {
            "question": "question-block",
            "answer": "answer-block", 
            "qa_section": "qa-section",
            "metric": "metric-card",
            "success": "icon-success",
            "error": "icon-error",
            "warning": "icon-warning",
            "info": "icon-info"
        }
        
        css_class = component_classes.get(component_type, "fade-in")
        
        return f'<div class="{css_class}">{content}</div>'
    
    @staticmethod
    def render_custom_metrics(metrics: dict, columns: int = 4):
        """カスタムメトリックカードを描画"""
        cols = st.columns(columns)
        
        for i, (label, value) in enumerate(metrics.items()):
            with cols[i % columns]:
                st.markdown(
                    StyleManager.create_custom_component(
                        f"<h4>{label}</h4><h2>{value}</h2>",
                        "metric"
                    ),
                    unsafe_allow_html=True
                )
    
    @staticmethod
    def render_qa_with_style(question: str, answer: str, pair_number: int):
        """スタイル付きQ&Aペアを描画"""
        # Q&Aセクション全体
        qa_content = f"""
        <div class="qa-section fade-in">
            <div class="question-block">
                <strong>Q{pair_number}:</strong> {question}
            </div>
            <div class="answer-block">
                <strong>A{pair_number}:</strong> {answer}
            </div>
        </div>
        """
        
        st.markdown(qa_content, unsafe_allow_html=True)