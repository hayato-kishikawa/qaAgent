import streamlit as st
import hashlib
import os

def check_password():
    """パスワード認証を確認する関数"""
    
    def password_entered():
        """パスワード入力時の処理"""
        # 環境変数またはsecrets.tomlからパスワードを取得
        expected_password = st.secrets.get("APP_PASSWORD", os.getenv("APP_PASSWORD", "tig"))
        
        # 入力されたパスワードをハッシュ化
        entered_password = st.session_state["password"]
        
        if entered_password == expected_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # パスワードをセッション状態から削除
        else:
            st.session_state["password_correct"] = False

    # パスワードが正しい場合はTrueを返す
    if st.session_state.get("password_correct", False):
        return True

    # パスワード入力フォームを表示
    st.markdown("## 🔐 認証が必要です")
    st.markdown("このアプリにアクセスするにはパスワードが必要です。")
    
    st.text_input(
        "パスワードを入力してください", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )
    
    if st.session_state.get("password_correct", None) is False:
        st.error("❌ パスワードが正しくありません")
    
    return False

def logout():
    """ログアウト処理"""
    st.session_state["password_correct"] = False
    st.rerun()