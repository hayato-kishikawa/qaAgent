import streamlit as st

class StyleManager:
    """アプリケーションのスタイルを管理するクラス"""

    @staticmethod
    def apply_custom_styles():
        """カスタムCSSスタイルを適用（ダークモード完全対応版）"""
        st.markdown("""
        <style>
        /* CSS変数でテーマカラーを定義 - ライトモード */
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --bg-tertiary: #e9ecef;
            --text-primary: #333333;
            --text-secondary: #666666;
            --text-inverse: #ffffff;
            --border-color: #dee2e6;
            --border-light: #e9ecef;
            --shadow-sm: rgba(0, 0, 0, 0.05);
            --shadow-md: rgba(0, 0, 0, 0.1);
            --shadow-lg: rgba(0, 0, 0, 0.15);
            --qa-section-bg: #f8f9fa;
            --question-bg: #e3f2fd;
            --question-border: #2196f3;
            --answer-bg: #f3e5f5;
            --answer-border: #9c27b0;
            --code-bg: #f8f9fa;
            --code-border: #e9ecef;
            --metric-bg: #ffffff;
            --tab-bg: #ffffff;
            --tab-hover-bg: #f8f9fa;
            --tab-active-bg: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            --subtab-bg: #ffffff;
            --subtab-hover-bg: #f8f9fa;
            --subtab-active-bg: linear-gradient(135deg, #1a73e8 0%, #1557b0 100%);
            --gradient-primary: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            --gradient-button: linear-gradient(45deg, #007bff, #0056b3);
            --gradient-progress: linear-gradient(90deg, #007bff, #28a745);
        }

        /* ダークモード用CSS変数 */
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-primary: #0e1117;
                --bg-secondary: #262730;
                --bg-tertiary: #1e1e1e;
                --text-primary: #fafafa;
                --text-secondary: #b0b0b0;
                --text-inverse: #ffffff;
                --border-color: #4a5568;
                --border-light: #2d3748;
                --shadow-sm: rgba(0, 0, 0, 0.3);
                --shadow-md: rgba(0, 0, 0, 0.4);
                --shadow-lg: rgba(0, 0, 0, 0.5);
                --qa-section-bg: #2d3748;
                --question-bg: #2a4365;
                --question-border: #4299e1;
                --answer-bg: #44337a;
                --answer-border: #b794f4;
                --code-bg: #1a202c;
                --code-border: #2d3748;
                --metric-bg: #262730;
                --tab-bg: #262730;
                --tab-hover-bg: #2d3748;
                --tab-active-bg: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
                --subtab-bg: #1e1e1e;
                --subtab-hover-bg: #2d3748;
                --subtab-active-bg: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
                --gradient-primary: linear-gradient(90deg, #4c51bf 0%, #6b46c1 100%);
                --gradient-button: linear-gradient(45deg, #4299e1, #3182ce);
                --gradient-progress: linear-gradient(90deg, #4299e1, #48bb78);
            }
        }

        /* メインコンテナのスタイル */
        .main {
            padding-top: 2rem;
        }

        /* ヘッダーのスタイル */
        .main-header {
            background: var(--gradient-primary);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
        }

        .main-header h1 {
            color: var(--text-inverse);
            margin: 0;
            text-align: center;
        }

        /* Q&Aセクションのスタイル */
        .qa-section {
            background-color: var(--qa-section-bg);
            color: var(--text-primary);
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            border-left: 4px solid #007bff;
        }

        .question-block {
            background-color: var(--question-bg);
            color: var(--text-primary);
            padding: 0.8rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            border-left: 3px solid var(--question-border);
        }

        .answer-block {
            background-color: var(--answer-bg);
            color: var(--text-primary);
            padding: 0.8rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 3px solid var(--answer-border);
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
            box-shadow: 0 4px 8px var(--shadow-md);
        }

        /* プライマリボタン */
        .stButton > button[data-baseweb="button"][data-testid="baseButton-primary"] {
            background: var(--gradient-button);
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
            background: var(--metric-bg);
            color: var(--text-primary);
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px var(--shadow-md);
            text-align: center;
            margin: 0.5rem 0;
        }

        /* プログレスバーのスタイル */
        .stProgress .st-bo {
            background: var(--gradient-progress);
        }

        /* サイドバーのスタイル */
        .css-1d391kg {
            background-color: var(--bg-secondary);
        }
        
        /* メインタブのスタイル - レベル1（最上位） */
        .stTabs[data-tabs-level="0"] [data-baseweb="tab-list"],
        .stTabs:not(.stTabs .stTabs) [data-baseweb="tab-list"] {
            gap: 16px;
            background: var(--bg-secondary);
            padding: 12px;
            border-radius: 20px;
            box-shadow: 0 8px 32px var(--shadow-md);
            border: 2px solid var(--border-color);
        }

        .stTabs[data-tabs-level="0"] [data-baseweb="tab"],
        .stTabs:not(.stTabs .stTabs) [data-baseweb="tab"] {
            height: 56px;
            padding: 0 32px;
            background: var(--tab-bg);
            border-radius: 16px;
            font-weight: 700;
            font-size: 17px;
            color: var(--text-primary);
            border: 2px solid var(--border-color);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 8px var(--shadow-sm);
        }

        .stTabs[data-tabs-level="0"] [data-baseweb="tab"]:hover,
        .stTabs:not(.stTabs .stTabs) [data-baseweb="tab"]:hover {
            background: var(--tab-hover-bg);
            transform: translateY(-3px);
            box-shadow: 0 8px 24px var(--shadow-lg);
            border-color: var(--text-secondary);
        }

        .stTabs[data-tabs-level="0"] [aria-selected="true"],
        .stTabs:not(.stTabs .stTabs) [aria-selected="true"] {
            background: var(--tab-active-bg);
            color: var(--text-inverse);
            border: 2px solid transparent;
            transform: translateY(-3px);
            box-shadow: 0 12px 32px var(--shadow-lg);
        }

        .stTabs[data-tabs-level="0"] [aria-selected="true"]:hover,
        .stTabs:not(.stTabs .stTabs) [aria-selected="true"]:hover {
            transform: translateY(-4px);
            box-shadow: 0 16px 40px var(--shadow-lg);
        }

        /* メインタブコンテンツエリア */
        .stTabs[data-tabs-level="0"] [data-baseweb="tab-panel"],
        .stTabs:not(.stTabs .stTabs) [data-baseweb="tab-panel"] {
            padding: 32px;
            background: var(--bg-primary);
            border-radius: 0 0 20px 20px;
            box-shadow: 0 8px 32px var(--shadow-md);
            margin-top: -12px;
            border: 2px solid var(--border-color);
            border-top: none;
        }

        /* サブタブのスタイル - レベル2（入力オプション用） */
        .stTabs .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            background: var(--bg-tertiary);
            padding: 4px;
            border-radius: 12px;
            box-shadow: inset 0 2px 4px var(--shadow-md);
            border: 1px solid var(--border-color);
        }

        .stTabs .stTabs [data-baseweb="tab"] {
            height: 40px;
            padding: 0 18px;
            background: var(--subtab-bg);
            border-radius: 8px;
            font-weight: 500;
            font-size: 14px;
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px var(--shadow-sm);
        }

        .stTabs .stTabs [data-baseweb="tab"]:hover {
            background: var(--subtab-hover-bg);
            color: var(--text-primary);
            border-color: var(--border-color);
            transform: translateY(-1px);
            box-shadow: 0 2px 6px var(--shadow-md);
        }

        .stTabs .stTabs [aria-selected="true"] {
            background: var(--subtab-active-bg);
            color: var(--text-inverse);
            border: 1px solid transparent;
            transform: translateY(-1px);
            box-shadow: 0 3px 8px var(--shadow-md);
        }

        .stTabs .stTabs [aria-selected="true"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px var(--shadow-lg);
        }
        
        /* エキスパンダーのスタイル */
        .streamlit-expanderHeader {
            background-color: var(--bg-secondary);
            border-radius: 8px;
            font-weight: 500;
            color: var(--text-primary);
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
            color: var(--text-primary);
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
        }

        .stMarkdown h1 {
            border-bottom: 2px solid #007bff;
            padding-bottom: 0.3rem;
        }

        .stMarkdown h2 {
            color: var(--text-primary);
        }

        .stMarkdown code {
            background-color: var(--code-bg);
            color: var(--text-primary);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            border: 1px solid var(--code-border);
        }

        .stMarkdown pre {
            background-color: var(--code-bg);
            color: var(--text-primary);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid var(--code-border);
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
            box-shadow: 0 4px 12px var(--shadow-lg);
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