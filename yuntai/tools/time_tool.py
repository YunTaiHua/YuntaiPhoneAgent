"""
时间工具模块 - 提供多种时间格式读取功能
"""
import datetime
import time
from typing import Literal


class TimeTool:
    """时间工具类"""

    @staticmethod
    def get_current_timestamp(
        format_type: Literal["datetime", "filename", "short"] = "datetime"
    ) -> str:
        """
        获取当前时间戳

        Args:
            format_type: 时间格式类型
                - "datetime": 2026-01-31 14:30:45（标准格式）
                - "filename": 20260131_143045（文件名格式）
                - "short": [14:30:45]（简短格式）

        Returns:
            格式化后的时间字符串
        """
        if format_type == "datetime":
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif format_type == "filename":
            return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        elif format_type == "short":
            return time.strftime("[%H:%M:%S]")
        else:
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_date_only() -> str:
        """获取日期（不含时间）"""
        return datetime.datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def get_time_only() -> str:
        """获取时间（不含日期）"""
        return datetime.datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def get_weekday() -> str:
        """获取星期几"""
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return weekdays[datetime.datetime.now().weekday()]

    @staticmethod
    def get_time_info() -> str:
        """
        获取完整的时间信息格式化字符串

        Returns:
            格式化的时间信息字符串，包含完整时间、日期、时间和星期
        """
        time_str = TimeTool.get_current_timestamp("datetime")
        date_str = TimeTool.get_date_only()
        time_only = TimeTool.get_time_only()
        weekday_info = TimeTool.get_weekday()

        return f"""当前时间信息：
- 完整时间：{time_str}
- 日期：{date_str}
- 时间：{time_only}
- 星期：{weekday_info}"""
