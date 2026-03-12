"""
output_capture.py - Web端输出捕获类
将终端输出同步到WebSocket
"""

import sys
import asyncio


class WebOutputCapture:
    """Web端输出捕获类 - 将终端输出同步到WebSocket"""

    def __init__(self, controller):
        self.controller = controller
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self._loop = None
        self._enabled = False

        class CustomStream:
            def __init__(self, capture, is_stdout=True):
                self.capture = capture
                self.is_stdout = is_stdout

            def write(self, text):
                if not text:
                    return 0

                # 输出到终端
                if self.is_stdout:
                    self.capture.original_stdout.write(text)
                else:
                    self.capture.original_stderr.write(text)

                # 同步到WebSocket（如果启用）
                if self.capture._enabled and self.capture._loop:
                    try:
                        # 在主事件循环中发送消息
                        future = asyncio.run_coroutine_threadsafe(
                            self.capture.controller.ws_manager.broadcast({
                                "type": "agent_output",
                                "message": text
                            }),
                            self.capture._loop
                        )
                    except Exception:
                        pass

                return len(text)

            def flush(self):
                if self.is_stdout:
                    self.capture.original_stdout.flush()
                else:
                    self.capture.original_stderr.flush()

        self.custom_stdout = CustomStream(self, is_stdout=True)
        self.custom_stderr = CustomStream(self, is_stdout=False)

    def start_capture(self, loop):
        """开始捕获输出"""
        self._loop = loop
        self._enabled = True
        sys.stdout = self.custom_stdout
        sys.stderr = self.custom_stderr

    def stop_capture(self):
        """停止捕获输出"""
        self._enabled = False
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
