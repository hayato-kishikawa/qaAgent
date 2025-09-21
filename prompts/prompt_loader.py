import os
import configparser
from typing import Dict, Any

class PromptLoader:
    """プロンプトファイル（.ini形式）を読み込むユーティリティクラス"""

    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir
        self._cache = {}  # プロンプトキャッシュ
        self._file_timestamps = {}  # ファイルタイムスタンプキャッシュ
    
    def load_prompt(self, agent_type: str, level: str = "Standard") -> Dict[str, Any]:
        """
        指定されたエージェントタイプとレベルのプロンプトを読み込む

        Args:
            agent_type: エージェントタイプ（student, teacher, summarizer）
            level: 質問レベル（"Standard", "Simple", "Beginner"）

        Returns:
            プロンプト設定の辞書
        """
        prompt_path = os.path.join(self.prompts_dir, agent_type, "prompt.ini")
        cache_key = f"{agent_type}_{level}"

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

            # 指定されたレベルのSystem/Userセクションを抽出
            system_section = f"{level.lower()}-system"
            user_section = f"{level.lower()}-user"

            result = {
                'system': prompt_dict.get(system_section, {}),
                'user': prompt_dict.get(user_section, {}),
                'followup_question_prompt': prompt_dict.get('followup_question_prompt', {}),
                'followup_answer_prompt': prompt_dict.get('followup_answer_prompt', {})
            }

            # キャッシュに保存
            self._cache[cache_key] = result
            self._file_timestamps[cache_key] = current_mtime

            return result

        except Exception as e:
            raise RuntimeError(f"プロンプトファイルの読み込みエラー ({prompt_path}): {str(e)}")
    
    def get_system_prompt(self, agent_type: str, level: str = "Standard") -> str:
        """
        システムプロンプトを構築して返す

        Args:
            agent_type: エージェントタイプ
            level: 質問レベル

        Returns:
            システムプロンプト文字列
        """
        system_cache_key = f"system_{agent_type}_{level}"

        # システムプロンプトのキャッシュを確認
        if system_cache_key in self._cache:
            return self._cache[system_cache_key]

        prompt_config = self.load_prompt(agent_type, level)

        # システムプロンプトを構築（新しいSystem/User構造）
        system_section = prompt_config.get('system', {})

        if not system_section:
            raise ValueError(f"システムプロンプトが見つかりません: {agent_type}, {level}")

        # システムセクションを構造化して構築
        system_prompt_parts = []

        # セクション別に整理
        current_section = None
        for key, value in system_section.items():
            if key.startswith('identity'):
                if current_section != 'identity':
                    if current_section is not None:
                        system_prompt_parts.append("")  # セクション間の改行
                    system_prompt_parts.append("# Identity")
                    current_section = 'identity'
                system_prompt_parts.append(f"- {value}")
            elif key.startswith('instruction'):
                if current_section != 'instruction':
                    if current_section is not None:
                        system_prompt_parts.append("")  # セクション間の改行
                    system_prompt_parts.append("# Instructions")
                    current_section = 'instruction'
                system_prompt_parts.append(f"- {value}")
            elif key.startswith('format'):
                if current_section != 'format':
                    if current_section is not None:
                        system_prompt_parts.append("")  # セクション間の改行
                    system_prompt_parts.append("# Output Format")
                    current_section = 'format'
                system_prompt_parts.append(f"- {value}")
            elif key.startswith('example'):
                if current_section != 'example':
                    if current_section is not None:
                        system_prompt_parts.append("")  # セクション間の改行
                    system_prompt_parts.append("# Examples")
                    current_section = 'example'
                system_prompt_parts.append(f"- {value}")

        system_prompt = "\n".join(system_prompt_parts)

        # システムプロンプトをキャッシュに保存
        self._cache[system_cache_key] = system_prompt

        return system_prompt
    
    def get_user_prompt(self, agent_type: str, level: str = "Standard", context: Dict[str, Any] = None) -> str:
        """
        ユーザープロンプトを構築して返す（過去質問などの動的コンテキスト付き）

        Args:
            agent_type: エージェントタイプ
            level: 質問レベル
            context: 動的に挿入するコンテキスト情報

        Returns:
            ユーザープロンプト文字列
        """
        prompt_config = self.load_prompt(agent_type, level)
        user_section = prompt_config.get('user', {})

        if not user_section:
            return ""

        # ユーザーセクションのテキストを構築
        user_prompt_parts = []
        for key, value in user_section.items():
            if key.startswith('user'):
                user_prompt_parts.append(f"- {value}")
            else:
                user_prompt_parts.append(value)

        user_prompt = "\n".join(user_prompt_parts)

        # コンテキスト情報で動的に置換
        if context:
            for placeholder, replacement in context.items():
                user_prompt = user_prompt.replace(f"{{{placeholder}}}", str(replacement))

        return user_prompt

    def get_available_levels(self, agent_type: str) -> list:
        """
        指定されたエージェントタイプで利用可能なレベルのリストを取得

        Returns:
            利用可能なレベルのリスト
        """
        prompt_path = os.path.join(self.prompts_dir, agent_type, "prompt.ini")
        if not os.path.exists(prompt_path):
            return []

        try:
            config = configparser.ConfigParser()
            config.read(prompt_path, encoding='utf-8')

            levels = []
            for section in config.sections():
                if section.endswith('-system'):
                    level = section.replace('-system', '')
                    levels.append(level)

            return sorted(levels)
        except Exception:
            return []