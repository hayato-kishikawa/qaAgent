import time
import psutil
import logging
import asyncio
from functools import wraps
from typing import Dict, Any, List
from datetime import datetime
import json
import os
from contextlib import contextmanager


class PerformanceProfiler:
    """パフォーマンス監視とボトルネック分析のためのプロファイラー"""

    def __init__(self):
        self.profile_data = {}
        self.current_session = None
        self.setup_logging()

    def setup_logging(self):
        """ログファイルの設定"""
        # logsディレクトリを作成
        os.makedirs('logs', exist_ok=True)

        # プロファイル用ログファイル
        profile_log_file = f'logs/performance_profile_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

        # ロガーの設定
        self.logger = logging.getLogger('performance_profiler')
        self.logger.setLevel(logging.INFO)

        # ファイルハンドラー
        file_handler = logging.FileHandler(profile_log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # フォーマッター
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

        self.profile_log_file = profile_log_file
        self.logger.info("=== Performance Profiling Session Started ===")

    def start_session(self, session_name: str):
        """プロファイリングセッションを開始"""
        self.current_session = {
            'session_name': session_name,
            'start_time': time.time(),
            'operations': [],
            'system_metrics': {
                'start_memory': self._get_memory_usage(),
                'start_cpu': self._get_cpu_usage()
            }
        }
        self.logger.info(f"Session started: {session_name}")

    def end_session(self):
        """プロファイリングセッションを終了"""
        if not self.current_session:
            return

        end_time = time.time()
        session_duration = end_time - self.current_session['start_time']

        self.current_session.update({
            'end_time': end_time,
            'duration': session_duration,
            'system_metrics': {
                **self.current_session['system_metrics'],
                'end_memory': self._get_memory_usage(),
                'end_cpu': self._get_cpu_usage()
            }
        })

        # セッション結果をログに出力
        self._log_session_summary()

        # JSONファイルにも保存
        self._save_session_json()

        self.current_session = None

    def _get_memory_usage(self) -> Dict[str, float]:
        """メモリ使用量を取得"""
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # MB
            'vms_mb': memory_info.vms / 1024 / 1024,  # MB
            'system_memory_percent': psutil.virtual_memory().percent
        }

    def _get_cpu_usage(self) -> Dict[str, float]:
        """CPU使用率を取得"""
        return {
            'process_cpu_percent': psutil.Process().cpu_percent(),
            'system_cpu_percent': psutil.cpu_percent()
        }

    @contextmanager
    def profile_operation(self, operation_name: str, **metadata):
        """操作のプロファイリングコンテキストマネージャー"""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        operation_data = {
            'operation_name': operation_name,
            'start_time': start_time,
            'start_memory': start_memory,
            'metadata': metadata
        }

        self.logger.info(f"Operation started: {operation_name}")

        try:
            yield operation_data
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()
            duration = end_time - start_time

            operation_data.update({
                'end_time': end_time,
                'end_memory': end_memory,
                'duration': duration,
                'memory_delta': {
                    'rss_mb': end_memory['rss_mb'] - start_memory['rss_mb'],
                    'vms_mb': end_memory['vms_mb'] - start_memory['vms_mb']
                }
            })

            if self.current_session:
                self.current_session['operations'].append(operation_data)

            self._log_operation_result(operation_data)

    def profile_async_function(self, func_name: str = None):
        """非同期関数のデコレーター"""
        def decorator(func):
            operation_name = func_name or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            async def wrapper(*args, **kwargs):
                with self.profile_operation(operation_name,
                                          function=func.__name__,
                                          args_count=len(args),
                                          kwargs_count=len(kwargs)):
                    return await func(*args, **kwargs)
            return wrapper
        return decorator

    def profile_function(self, func_name: str = None):
        """同期関数のデコレーター"""
        def decorator(func):
            operation_name = func_name or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.profile_operation(operation_name,
                                          function=func.__name__,
                                          args_count=len(args),
                                          kwargs_count=len(kwargs)):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

    def _log_operation_result(self, operation_data: Dict[str, Any]):
        """操作結果をログに出力"""
        duration = operation_data['duration']
        memory_delta = operation_data['memory_delta']

        self.logger.info(
            f"Operation completed: {operation_data['operation_name']} | "
            f"Duration: {duration:.3f}s | "
            f"Memory delta: RSS {memory_delta['rss_mb']:+.2f}MB, "
            f"VMS {memory_delta['vms_mb']:+.2f}MB"
        )

        # ボトルネック検出
        if duration > 10.0:  # 10秒以上の場合
            self.logger.warning(f"BOTTLENECK DETECTED: {operation_data['operation_name']} took {duration:.3f}s")

        if memory_delta['rss_mb'] > 100:  # 100MB以上のメモリ増加
            self.logger.warning(f"HIGH MEMORY USAGE: {operation_data['operation_name']} used +{memory_delta['rss_mb']:.2f}MB")

    def _log_session_summary(self):
        """セッション全体のサマリーをログに出力"""
        if not self.current_session:
            return

        session = self.current_session
        total_duration = session['duration']
        operations = session['operations']

        # 最も時間がかかった操作トップ5
        slowest_ops = sorted(operations, key=lambda x: x['duration'], reverse=True)[:5]

        # 最もメモリを使った操作トップ5
        memory_intensive_ops = sorted(operations,
                                    key=lambda x: x['memory_delta']['rss_mb'],
                                    reverse=True)[:5]

        self.logger.info("=== SESSION SUMMARY ===")
        self.logger.info(f"Session: {session['session_name']}")
        self.logger.info(f"Total duration: {total_duration:.3f}s")
        self.logger.info(f"Total operations: {len(operations)}")

        memory_start = session['system_metrics']['start_memory']
        memory_end = session['system_metrics']['end_memory']
        total_memory_delta = memory_end['rss_mb'] - memory_start['rss_mb']

        self.logger.info(f"Total memory delta: {total_memory_delta:+.2f}MB")

        self.logger.info("=== TOP 5 SLOWEST OPERATIONS ===")
        for i, op in enumerate(slowest_ops, 1):
            self.logger.info(f"{i}. {op['operation_name']}: {op['duration']:.3f}s")

        self.logger.info("=== TOP 5 MEMORY INTENSIVE OPERATIONS ===")
        for i, op in enumerate(memory_intensive_ops, 1):
            delta = op['memory_delta']['rss_mb']
            self.logger.info(f"{i}. {op['operation_name']}: {delta:+.2f}MB")

        self.logger.info("=== BOTTLENECK ANALYSIS ===")
        bottlenecks = [op for op in operations if op['duration'] > 5.0]
        if bottlenecks:
            for bottleneck in bottlenecks:
                self.logger.info(f"BOTTLENECK: {bottleneck['operation_name']} ({bottleneck['duration']:.3f}s)")
        else:
            self.logger.info("No significant bottlenecks detected")

        self.logger.info("=== Performance Profiling Session Ended ===")

    def _save_session_json(self):
        """セッションデータをJSONファイルに保存"""
        if not self.current_session:
            return

        json_file = f'logs/performance_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        # datetime オブジェクトを文字列に変換
        session_data = {
            **self.current_session,
            'timestamp': datetime.now().isoformat()
        }

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False, default=str)

        self.logger.info(f"Session data saved to: {json_file}")

    def get_log_file_path(self) -> str:
        """ログファイルのパスを取得"""
        return self.profile_log_file


# グローバルプロファイラーインスタンス
profiler = PerformanceProfiler()