"""
测试 MainApp
"""
import pytest
from unittest.mock import MagicMock, patch

from yuntai.core.main_app import MainApp


class TestMainApp:
    """测试主应用程序"""

    @patch('yuntai.core.main_app.QApplication')
    @patch('yuntai.core.main_app.validate_config', return_value=True)
    @patch('yuntai.core.main_app.print_config_summary')
    @patch('yuntai.core.main_app.GUIController')
    def test_init(self, mock_gui_controller, mock_print_config, mock_validate, mock_qapp):
        """测试初始化"""
        mock_app = MagicMock()
        mock_qapp.instance.return_value = mock_app
        
        app = MainApp()
        
        assert app is not None
        mock_validate.assert_called_once()
        mock_print_config.assert_called_once()

    @patch('yuntai.core.main_app.QApplication')
    @patch('yuntai.core.main_app.validate_config', return_value=False)
    @patch('yuntai.core.main_app.print_config_summary')
    @patch('yuntai.core.main_app.GUIController')
    def test_init_with_invalid_config(self, mock_gui_controller, mock_print_config, mock_validate, mock_qapp):
        """测试初始化 - 配置验证失败"""
        mock_app = MagicMock()
        mock_qapp.instance.return_value = mock_app
        
        app = MainApp()
        
        # 即使配置验证失败，也应该创建应用
        assert app is not None

    @patch('yuntai.core.main_app.QApplication')
    @patch('yuntai.core.main_app.validate_config', return_value=True)
    @patch('yuntai.core.main_app.print_config_summary')
    @patch('yuntai.core.main_app.GUIController')
    def test_run(self, mock_gui_controller, mock_print_config, mock_validate, mock_qapp):
        """测试运行应用"""
        mock_app = MagicMock()
        mock_qapp.instance.return_value = mock_app
        
        main_app = MainApp()
        
        # Mock exec方法
        mock_app.exec.return_value = 0
        
        # 运行应用
        result = main_app.run()
        
        # 应该调用QApplication.exec
        mock_app.exec.assert_called_once()

    @patch('yuntai.core.main_app.QApplication')
    @patch('yuntai.core.main_app.validate_config', return_value=True)
    @patch('yuntai.core.main_app.print_config_summary')
    @patch('yuntai.core.main_app.GUIController')
    def test_cleanup(self, mock_gui_controller, mock_print_config, mock_validate, mock_qapp):
        """测试清理资源"""
        mock_app = MagicMock()
        mock_qapp.instance.return_value = mock_app
        
        main_app = MainApp()
        main_app.cleanup()
        
        # 应该不抛出异常
        assert True
