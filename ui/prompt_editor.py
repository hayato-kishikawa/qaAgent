import streamlit as st
import os
import configparser
from typing import Dict, Any, List
from prompts.prompt_loader import PromptLoader

class PromptEditor:
    """プロンプト編集機能を提供するクラス"""
    
    def __init__(self):
        self.prompt_loader = PromptLoader()
        self.agent_types = ["student", "teacher", "summarizer", "initial_summarizer"]
    
    def render_prompt_editor_tab(self):
        """プロンプト編集タブを描画"""
        st.header("🎯 プロンプト編集")
        
        # エージェント選択
        selected_agent = st.selectbox(
            "編集するエージェントを選択",
            self.agent_types,
            format_func=self._format_agent_name
        )
        
        # バージョン管理セクション
        self._render_version_management(selected_agent)
        
        # プロンプト編集セクション
        self._render_prompt_editor(selected_agent)
    
    def _format_agent_name(self, agent_type: str) -> str:
        """エージェント名をUI表示用にフォーマット"""
        name_map = {
            "student": "🎓 生徒エージェント",
            "teacher": "👨‍🏫 先生エージェント", 
            "summarizer": "📋 要約エージェント",
            "initial_summarizer": "📄 初期要約エージェント"
        }
        return name_map.get(agent_type, agent_type)
    
    def _render_version_management(self, agent_type: str):
        """バージョン管理セクションを描画"""
        st.subheader("📋 バージョン管理")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 利用可能なバージョン一覧
            versions = self._get_available_versions(agent_type)
            if versions:
                current_version = st.session_state.get(f"{agent_type}_current_version", "v1_0_0")
                
                selected_version = st.selectbox(
                    "現在のバージョン",
                    versions,
                    index=versions.index(current_version) if current_version in versions else 0,
                    key=f"{agent_type}_version_select"
                )
                
                st.session_state[f"{agent_type}_current_version"] = selected_version
                
                # バージョン情報表示
                version_info = self._get_version_info(agent_type, selected_version)
                if version_info:
                    st.info(f"📝 {version_info}")
            else:
                st.warning("利用可能なバージョンが見つかりません")
        
        with col2:
            st.write("**新バージョン作成**")
            new_version_name = st.text_input(
                "新バージョン名",
                placeholder="v2_0_0",
                key=f"{agent_type}_new_version"
            )
            
            if st.button("📝 新バージョンを作成", key=f"{agent_type}_create_version"):
                if new_version_name and self._is_valid_version_name(new_version_name):
                    self._create_new_version(agent_type, new_version_name)
                    st.success(f"新バージョン '{new_version_name}' を作成しました")
                    st.rerun()
                else:
                    st.error("有効なバージョン名を入力してください (例: v2_0_0)")
    
    def _render_prompt_editor(self, agent_type: str):
        """プロンプト編集セクションを描画"""
        st.subheader("✏️ プロンプト編集")
        
        current_version = st.session_state.get(f"{agent_type}_current_version", "v1_0_0")
        
        try:
            # 現在のプロンプトを読み込み
            prompt_config = self.prompt_loader.load_prompt(agent_type, current_version)
            
            # セクションごとに編集フィールドを表示
            updated_config = {}
            
            for section_name, section_content in prompt_config.items():
                with st.expander(f"📁 {section_name.upper()}", expanded=True):
                    updated_config[section_name] = {}
                    
                    for key, value in section_content.items():
                        # テキストエリアで編集可能に
                        updated_value = st.text_area(
                            key,
                            value=value,
                            height=100 if len(value) > 50 else 50,
                            key=f"{agent_type}_{current_version}_{section_name}_{key}"
                        )
                        updated_config[section_name][key] = updated_value
            
            # 保存ボタン
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("💾 現在のバージョンを保存", key=f"{agent_type}_save_current"):
                    self._save_prompt_config(agent_type, current_version, updated_config)
                    st.success(f"バージョン '{current_version}' を保存しました")
            
            with col2:
                save_as_version = st.text_input(
                    "名前を付けて保存",
                    placeholder="v2_1_0",
                    key=f"{agent_type}_save_as_name"
                )
                
                if st.button("📋 名前を付けて保存", key=f"{agent_type}_save_as"):
                    if save_as_version and self._is_valid_version_name(save_as_version):
                        self._save_prompt_config(agent_type, save_as_version, updated_config)
                        st.success(f"新バージョン '{save_as_version}' として保存しました")
                        # バージョンリストを更新
                        st.session_state[f"{agent_type}_current_version"] = save_as_version
                        st.rerun()
                    else:
                        st.error("有効なバージョン名を入力してください")
            
            with col3:
                if st.button("🔄 リセット", key=f"{agent_type}_reset"):
                    st.rerun()
            
            # プレビューセクション
            st.subheader(" プレビュー")
            with st.expander("生成されるシステムプロンプト", expanded=False):
                try:
                    # 一時的に設定を保存してプレビュー生成
                    temp_config = updated_config
                    system_prompt = self._generate_system_prompt_preview(temp_config)
                    st.code(system_prompt, language="text")
                except Exception as e:
                    st.error(f"プレビュー生成エラー: {str(e)}")
                    
        except Exception as e:
            st.error(f"プロンプト読み込みエラー: {str(e)}")
    
    def _get_available_versions(self, agent_type: str) -> List[str]:
        """利用可能なバージョンリストを取得"""
        try:
            versions = self.prompt_loader.get_available_versions(agent_type)
            # v1_0_0を最初に来るようにソート
            if "v1_0_0" in versions:
                versions = ["v1_0_0"] + [v for v in versions if v != "v1_0_0"]
            return versions
        except Exception:
            return ["v1_0_0"]  # デフォルト
    
    def _get_version_info(self, agent_type: str, version: str) -> str:
        """バージョン情報を取得"""
        version_descriptions = {
            "v1_0_0": "初期バージョン - 基本的な機能",
            "v2_0_0": "改良版 - 機能拡張",
            "v2_1_0": "マイナーアップデート"
        }
        return version_descriptions.get(version, f"カスタムバージョン: {version}")
    
    def _is_valid_version_name(self, version_name: str) -> bool:
        """バージョン名の有効性をチェック"""
        import re
        # v1_0_0 形式をチェック
        pattern = r'^v\d+_\d+_\d+$'
        return bool(re.match(pattern, version_name))
    
    def _create_new_version(self, agent_type: str, version_name: str):
        """新しいバージョンを作成"""
        try:
            # 現在のバージョンをベースに新バージョンを作成
            current_version = st.session_state.get(f"{agent_type}_current_version", "v1_0_0")
            current_config = self.prompt_loader.load_prompt(agent_type, current_version)
            
            # 新バージョンとして保存
            self._save_prompt_config(agent_type, version_name, current_config)
            
        except Exception as e:
            st.error(f"新バージョン作成エラー: {str(e)}")
    
    def _save_prompt_config(self, agent_type: str, version: str, config: Dict[str, Dict[str, str]]):
        """プロンプト設定をファイルに保存"""
        try:
            # 保存パスを構築
            agent_dir = os.path.join("prompts", agent_type)
            os.makedirs(agent_dir, exist_ok=True)
            
            file_path = os.path.join(agent_dir, f"{version}.ini")
            
            # ConfigParserで保存
            parser = configparser.ConfigParser()
            
            for section_name, section_content in config.items():
                parser.add_section(section_name)
                for key, value in section_content.items():
                    parser.set(section_name, key, value)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                parser.write(file)
                
        except Exception as e:
            st.error(f"保存エラー: {str(e)}")
    
    def _generate_system_prompt_preview(self, config: Dict[str, Dict[str, str]]) -> str:
        """システムプロンプトのプレビューを生成"""
        system_parts = []
        
        # system セクション
        if 'system' in config:
            system_parts.append(f"役割: {config['system'].get('role', '')}")
        
        # personality セクション（studentの場合）
        if 'personality' in config:
            system_parts.append("性格:")
            for key, value in config['personality'].items():
                system_parts.append(f"- {key}: {value}")
        
        # expertise セクション（teacherの場合）
        if 'expertise' in config:
            system_parts.append("専門性:")
            for key, value in config['expertise'].items():
                system_parts.append(f"- {key}: {value}")
        
        # responsibilities セクション（summarizerの場合）
        if 'responsibilities' in config:
            system_parts.append("責任:")
            for key, value in config['responsibilities'].items():
                system_parts.append(f"- {key}: {value}")
        
        # output_format セクション（summarizerの場合）
        if 'output_format' in config:
            system_parts.append("出力形式:")
            for key, value in config['output_format'].items():
                system_parts.append(f"- {key}: {value}")
        
        # instruction セクション
        if 'instruction' in config:
            system_parts.append("指示:")
            for key, value in config['instruction'].items():
                system_parts.append(f"- {key}: {value}")
        
        return "\n".join(system_parts)