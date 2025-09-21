import os
import configparser
from typing import Dict, Any

class PromptLoader:
    """プロンプトファイル（.ini形式）を読み込むユーティリティクラス"""

    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir
        self._cache = {}  # プロンプトキャッシュ
        self._file_timestamps = {}  # ファイルタイムスタンプキャッシュ
    
    def load_prompt(self, agent_type: str, version: str = "v1_0_0") -> Dict[str, Any]:
        """
        指定されたエージェントタイプとバージョンのプロンプトを読み込む

        Args:
            agent_type: エージェントタイプ（student, teacher, summarizer）
            version: プロンプトバージョン（"v1_0_0", "v2_0_0" など）

        Returns:
            プロンプト設定の辞書
        """
        prompt_path = os.path.join(self.prompts_dir, agent_type, f"{version}.ini")
        cache_key = f"{agent_type}_{version}"

        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {prompt_path}")

        # ファイルの更新時刻を確認
        current_mtime = os.path.getmtime(prompt_path)

        # キャッシュが存在し、ファイルが更新されていない場合はキャッシュを返す
        if (cache_key in self._cache and
            cache_key in self._file_timestamps and
            self._file_timestamps[cache_key] == current_mtime):
            return self._cache[cache_key]

        try:
            config = configparser.ConfigParser()
            config.read(prompt_path, encoding='utf-8')

            if not config.sections():
                raise ValueError(f"プロンプトファイルが空または不正な形式です: {prompt_path}")

            # ConfigParserの内容を辞書に変換
            prompt_dict = {}
            for section in config.sections():
                prompt_dict[section] = dict(config.items(section))

            # キャッシュに保存
            self._cache[cache_key] = prompt_dict
            self._file_timestamps[cache_key] = current_mtime

            return prompt_dict

        except Exception as e:
            raise RuntimeError(f"プロンプトファイルの読み込みエラー ({prompt_path}): {str(e)}")
    
    def get_system_prompt(self, agent_type: str, version: str = "v1_0_0") -> str:
        """
        システムプロンプトを構築して返す

        Args:
            agent_type: エージェントタイプ
            version: プロンプトバージョン

        Returns:
            システムプロンプト文字列
        """
        system_cache_key = f"system_{agent_type}_{version}"

        # システムプロンプトのキャッシュを確認
        if system_cache_key in self._cache:
            return self._cache[system_cache_key]

        prompt_config = self.load_prompt(agent_type, version)

        # システムプロンプトを構築
        system_parts = []

        # identity セクション（新構造）
        if 'identity' in prompt_config:
            identity_section = prompt_config['identity']
            if 'role' in identity_section:
                system_parts.append(f"【役割】\n{identity_section['role']}")
            if 'approach' in identity_section:
                system_parts.append(f"【アプローチ】\n{identity_section['approach']}")
            if 'personality' in identity_section:
                system_parts.append(f"【性格】\n{identity_section['personality']}")
            if 'curiosity' in identity_section:
                system_parts.append(f"【好奇心】\n{identity_section['curiosity']}")

        # instructions セクション（新構造）
        if 'instructions' in prompt_config:
            system_parts.append("【指示】")
            for key, value in prompt_config['instructions'].items():
                system_parts.append(f"- {key}: {value}")

        # format セクション（新構造）
        if 'format' in prompt_config:
            system_parts.append("【出力形式】")
            for key, value in prompt_config['format'].items():
                system_parts.append(f"- {key}: {value}")

        # examples セクション（新構造）
        if 'examples' in prompt_config:
            system_parts.append("【質問例】")
            for key, value in prompt_config['examples'].items():
                system_parts.append(f"- {value}")

        # 旧構造との互換性を保持
        # system セクション（旧構造）
        if 'system' in prompt_config:
            system_parts.append(f"役割: {prompt_config['system'].get('role', '')}")

        # personality セクション（旧構造、studentの場合）
        if 'personality' in prompt_config:
            system_parts.append("性格:")
            for key, value in prompt_config['personality'].items():
                system_parts.append(f"- {key}: {value}")

        # expertise セクション（旧構造、teacherの場合）
        if 'expertise' in prompt_config:
            system_parts.append("専門性:")
            for key, value in prompt_config['expertise'].items():
                system_parts.append(f"- {key}: {value}")

        # responsibilities セクション（旧構造、summarizerの場合）
        if 'responsibilities' in prompt_config:
            system_parts.append("責任:")
            for key, value in prompt_config['responsibilities'].items():
                system_parts.append(f"- {key}: {value}")

        # output_format セクション（旧構造、summarizerの場合）
        if 'output_format' in prompt_config:
            system_parts.append("出力形式:")
            for key, value in prompt_config['output_format'].items():
                system_parts.append(f"- {key}: {value}")

        # instruction セクション（旧構造）
        if 'instruction' in prompt_config:
            system_parts.append("指示:")
            for key, value in prompt_config['instruction'].items():
                system_parts.append(f"- {key}: {value}")

        system_prompt = "\n\n".join(system_parts)

        # システムプロンプトをキャッシュに保存
        self._cache[system_cache_key] = system_prompt

        return system_prompt
    
    def get_available_versions(self, agent_type: str) -> list:
        """
        指定されたエージェントタイプで利用可能なバージョンのリストを取得
        
        Args:
            agent_type: エージェントタイプ
            
        Returns:
            利用可能なバージョンのリスト
        """
        agent_dir = os.path.join(self.prompts_dir, agent_type)
        if not os.path.exists(agent_dir):
            return []
        
        versions = []
        for file in os.listdir(agent_dir):
            if file.endswith('.ini'):
                versions.append(file.replace('.ini', ''))
        
        # v1_0_0を最初に来るようにソート
        versions = sorted(versions, key=lambda x: (x != 'v1_0_0', x))
        return versions