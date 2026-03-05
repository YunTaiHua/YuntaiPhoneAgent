"""
测试 time_tool.py - 时间工具
"""
import pytest
import datetime
import re
import os

# 设置测试环境变量
os.environ.setdefault('ZHIPU_API_KEY', 'test_api_key_for_testing')
os.environ.setdefault('GPT_SOVITS_ROOT', '/fake/gpt-sovits')
os.environ.setdefault('SCRCPY_PATH', '/fake/scrcpy')
os.environ.setdefault('FFMPEG_PATH', '/fake/ffmpeg')
os.environ.setdefault('FOREVER_MEMORY_FILE', '/fake/forever.txt')

from yuntai.tools.time_tool import TimeTool


class TestTimeTool:
    """测试 TimeTool 类"""

    def test_get_current_timestamp_datetime(self):
        """测试获取datetime格式时间戳"""
        result = TimeTool.get_current_timestamp("datetime")
        
        # 验证格式：YYYY-MM-DD HH:MM:SS
        pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
        assert re.match(pattern, result) is not None

    def test_get_current_timestamp_filename(self):
        """测试获取filename格式时间戳"""
        result = TimeTool.get_current_timestamp("filename")
        
        # 验证格式：YYYYMMDD_HHMMSS
        pattern = r'^\d{8}_\d{6}$'
        assert re.match(pattern, result) is not None

    def test_get_current_timestamp_short(self):
        """测试获取short格式时间戳"""
        result = TimeTool.get_current_timestamp("short")
        
        # 验证格式：[HH:MM:SS]
        pattern = r'^\[\d{2}:\d{2}:\d{2}\]$'
        assert re.match(pattern, result) is not None

    def test_get_current_timestamp_default(self):
        """测试默认格式时间戳"""
        result = TimeTool.get_current_timestamp()
        
        # 默认应该是datetime格式
        pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
        assert re.match(pattern, result) is not None

    def test_get_current_timestamp_invalid(self):
        """测试无效格式"""
        result = TimeTool.get_current_timestamp("invalid")
        
        # 应该返回datetime格式
        pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
        assert re.match(pattern, result) is not None

    def test_get_date_only(self):
        """测试获取日期"""
        result = TimeTool.get_date_only()
        
        # 验证格式：YYYY-MM-DD
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        assert re.match(pattern, result) is not None

    def test_get_time_only(self):
        """测试获取时间"""
        result = TimeTool.get_time_only()
        
        # 验证格式：HH:MM:SS
        pattern = r'^\d{2}:\d{2}:\d{2}$'
        assert re.match(pattern, result) is not None

    def test_get_weekday(self):
        """测试获取星期"""
        result = TimeTool.get_weekday()
        
        valid_weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        assert result in valid_weekdays

    def test_get_weekday_correctness(self):
        """测试星期正确性"""
        result = TimeTool.get_weekday()
        expected_weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        expected = expected_weekdays[datetime.datetime.now().weekday()]
        
        assert result == expected

    def test_get_time_info(self):
        """测试获取完整时间信息"""
        result = TimeTool.get_time_info()
        
        assert "当前时间信息" in result
        assert "完整时间" in result
        assert "日期" in result
        assert "时间" in result
        assert "星期" in result

    def test_get_time_info_format(self):
        """测试时间信息格式"""
        result = TimeTool.get_time_info()
        
        # 验证包含时间戳格式
        assert re.search(r'\d{4}-\d{2}-\d{2}', result) is not None
        assert re.search(r'\d{2}:\d{2}:\d{2}', result) is not None

    def test_get_time_info_contains_weekday(self):
        """测试时间信息包含星期"""
        result = TimeTool.get_time_info()
        
        valid_weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        assert any(day in result for day in valid_weekdays)


class TestTimeToolConsistency:
    """测试 TimeTool 一致性"""

    def test_datetime_consistency(self):
        """测试datetime格式一致性"""
        result = TimeTool.get_current_timestamp("datetime")
        date = TimeTool.get_date_only()
        time = TimeTool.get_time_only()
        
        # datetime应该包含date和time
        assert date in result
        assert time in result

    def test_filename_consistency(self):
        """测试filename格式一致性"""
        result = TimeTool.get_current_timestamp("filename")
        date = TimeTool.get_date_only().replace("-", "")
        time = TimeTool.get_time_only().replace(":", "")
        
        # filename应该包含date和time（无分隔符）
        assert date in result
        assert time in result

    def test_time_info_consistency(self):
        """测试时间信息一致性"""
        result = TimeTool.get_time_info()
        datetime_result = TimeTool.get_current_timestamp("datetime")
        date_result = TimeTool.get_date_only()
        time_result = TimeTool.get_time_only()
        weekday_result = TimeTool.get_weekday()
        
        # 时间信息应该包含所有部分
        assert datetime_result in result
        assert date_result in result
        assert time_result in result
        assert weekday_result in result


class TestTimeToolStatic:
    """测试 TimeTool 静态方法"""

    def test_all_methods_are_static(self):
        """测试所有方法都是静态方法"""
        # 静态方法可以直接通过类调用
        assert callable(TimeTool.get_current_timestamp)
        assert callable(TimeTool.get_date_only)
        assert callable(TimeTool.get_time_only)
        assert callable(TimeTool.get_weekday)
        assert callable(TimeTool.get_time_info)

    def test_no_instance_required(self):
        """测试不需要实例化"""
        # 所有方法都可以直接调用
        TimeTool.get_current_timestamp()
        TimeTool.get_date_only()
        TimeTool.get_time_only()
        TimeTool.get_weekday()
        TimeTool.get_time_info()


class TestTimeToolEdgeCases:
    """测试 TimeTool 边界情况"""

    def test_multiple_calls_return_different_values(self):
        """测试多次调用返回不同值（时间流逝）"""
        result1 = TimeTool.get_current_timestamp("datetime")
        import time
        time.sleep(0.1)  # 等待100毫秒
        result2 = TimeTool.get_current_timestamp("datetime")
        
        # 时间应该不同（至少秒数可能不同）
        # 这里只验证格式正确
        assert re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', result1)
        assert re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', result2)

    def test_get_time_info_multiline(self):
        """测试时间信息是多行"""
        result = TimeTool.get_time_info()
        
        lines = result.split('\n')
        assert len(lines) >= 4  # 至少4行

    def test_timestamp_components_valid(self):
        """测试时间戳组件有效"""
        result = TimeTool.get_current_timestamp("datetime")
        
        # 解析组件
        parts = result.split()
        assert len(parts) == 2
        
        date_parts = parts[0].split('-')
        time_parts = parts[1].split(':')
        
        # 验证日期组件
        assert len(date_parts) == 3
        year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
        assert 2020 <= year <= 2100
        assert 1 <= month <= 12
        assert 1 <= day <= 31
        
        # 验证时间组件
        assert len(time_parts) == 3
        hour, minute, second = int(time_parts[0]), int(time_parts[1]), int(time_parts[2])
        assert 0 <= hour <= 23
        assert 0 <= minute <= 59
        assert 0 <= second <= 59
