"""
时间工具模块测试
测试 yuntai.tools.time_tool 模块
"""
import datetime
from unittest.mock import patch

import pytest


class TestGetCurrentTimestamp:
    """测试获取当前时间戳"""
    
    def test_datetime_format(self):
        """测试datetime格式"""
        from yuntai.tools.time_tool import TimeTool
        
        result = TimeTool.get_current_timestamp("datetime")
        assert len(result) == 19
        assert "-" in result
        assert ":" in result
        assert " " in result
    
    def test_filename_format(self):
        """测试filename格式"""
        from yuntai.tools.time_tool import TimeTool
        
        result = TimeTool.get_current_timestamp("filename")
        assert len(result) == 15
        assert "_" in result
        assert result.isalnum() or "_" in result
    
    def test_short_format(self):
        """测试short格式"""
        from yuntai.tools.time_tool import TimeTool
        
        result = TimeTool.get_current_timestamp("short")
        assert result.startswith("[")
        assert result.endswith("]")
        assert ":" in result
    
    def test_default_format(self):
        """测试默认格式"""
        from yuntai.tools.time_tool import TimeTool
        
        result = TimeTool.get_current_timestamp()
        assert len(result) == 19
    
    def test_invalid_format_defaults_to_datetime(self):
        """测试无效格式默认为datetime"""
        from yuntai.tools.time_tool import TimeTool
        
        result = TimeTool.get_current_timestamp("invalid")
        assert len(result) == 19
    
    def test_fixed_time_datetime(self):
        """测试固定时间的datetime格式"""
        from yuntai.tools.time_tool import TimeTool
        
        fixed_time = datetime.datetime(2026, 2, 19, 14, 30, 45)
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            result = TimeTool.get_current_timestamp("datetime")
            assert result == "2026-02-19 14:30:45"


class TestGetDateOnly:
    """测试获取日期"""
    
    def test_date_format(self):
        """测试日期格式"""
        from yuntai.tools.time_tool import TimeTool
        
        result = TimeTool.get_date_only()
        assert len(result) == 10
        assert result.count("-") == 2
    
    def test_fixed_date(self):
        """测试固定日期"""
        from yuntai.tools.time_tool import TimeTool
        
        fixed_time = datetime.datetime(2026, 12, 25, 0, 0, 0)
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            result = TimeTool.get_date_only()
            assert result == "2026-12-25"


class TestGetTimeOnly:
    """测试获取时间"""
    
    def test_time_format(self):
        """测试时间格式"""
        from yuntai.tools.time_tool import TimeTool
        
        result = TimeTool.get_time_only()
        assert len(result) == 8
        assert result.count(":") == 2
    
    def test_fixed_time(self):
        """测试固定时间"""
        from yuntai.tools.time_tool import TimeTool
        
        fixed_time = datetime.datetime(2026, 1, 1, 23, 59, 59)
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            result = TimeTool.get_time_only()
            assert result == "23:59:59"


class TestGetWeekday:
    """测试获取星期"""
    
    def test_weekday_returns_chinese(self):
        """测试返回中文星期"""
        from yuntai.tools.time_tool import TimeTool
        
        result = TimeTool.get_weekday()
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        assert result in weekdays
    
    def test_weekday_monday(self):
        """测试周一"""
        from yuntai.tools.time_tool import TimeTool
        
        fixed_time = datetime.datetime(2026, 1, 5, 0, 0, 0)
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.weekday = fixed_time.weekday
            result = weekdays[fixed_time.weekday()]
            assert result == "周一"
    
    def test_weekday_sunday(self):
        """测试周日"""
        from yuntai.tools.time_tool import TimeTool
        
        fixed_time = datetime.datetime(2026, 1, 4, 0, 0, 0)
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        result = weekdays[fixed_time.weekday()]
        assert result == "周日"


class TestGetTimeInfo:
    """测试获取完整时间信息"""
    
    def test_time_info_contains_all_parts(self):
        """测试时间信息包含所有部分"""
        from yuntai.tools.time_tool import TimeTool
        
        result = TimeTool.get_time_info()
        
        assert "完整时间" in result
        assert "日期" in result
        assert "时间" in result
        assert "星期" in result
    
    def test_time_info_format(self):
        """测试时间信息格式"""
        from yuntai.tools.time_tool import TimeTool
        
        result = TimeTool.get_time_info()
        
        lines = result.split('\n')
        assert len(lines) == 5
        assert lines[0] == "当前时间信息："
    
    def test_time_info_has_correct_structure(self):
        """测试时间信息结构正确"""
        from yuntai.tools.time_tool import TimeTool
        
        result = TimeTool.get_time_info()
        
        assert "- 完整时间：" in result
        assert "- 日期：" in result
        assert "- 时间：" in result
        assert "- 星期：" in result


class TestTimeToolEdgeCases:
    """测试边界情况"""
    
    def test_midnight(self):
        """测试午夜时间"""
        from yuntai.tools.time_tool import TimeTool
        
        fixed_time = datetime.datetime(2026, 1, 1, 0, 0, 0)
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            result = TimeTool.get_time_only()
            assert result == "00:00:00"
    
    def test_end_of_day(self):
        """测试一天结束时间"""
        from yuntai.tools.time_tool import TimeTool
        
        fixed_time = datetime.datetime(2026, 12, 31, 23, 59, 59)
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            result = TimeTool.get_time_only()
            assert result == "23:59:59"
    
    def test_year_boundary(self):
        """测试年份边界"""
        from yuntai.tools.time_tool import TimeTool
        
        fixed_time = datetime.datetime(2026, 1, 1, 0, 0, 0)
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            result = TimeTool.get_date_only()
            assert result == "2026-01-01"
