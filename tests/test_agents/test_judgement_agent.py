"""
测试 JudgementAgent
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage

from yuntai.agents.judgement_agent import JudgementAgent, TaskJudgementResult
from yuntai.prompts import (
    TASK_TYPE_FREE_CHAT,
    TASK_TYPE_BASIC_OPERATION,
    TASK_TYPE_SINGLE_REPLY,
    TASK_TYPE_CONTINUOUS_REPLY,
    TASK_TYPE_COMPLEX_OPERATION,
)


class TestTaskJudgementResult:
    """测试 TaskJudgementResult 数据类"""

    def test_to_dict(self):
        """测试转换为字典"""
        result = TaskJudgementResult(
            task_type=TASK_TYPE_FREE_CHAT,
            target_app="微信",
            target_object="张三",
            is_auto=False,
            specific_content="你好"
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["task_type"] == TASK_TYPE_FREE_CHAT
        assert result_dict["target_app"] == "微信"
        assert result_dict["target_object"] == "张三"
        assert result_dict["is_auto"] is False
        assert result_dict["specific_content"] == "你好"


class TestJudgementAgent:
    """测试 JudgementAgent"""

    def test_init_with_model(self, mock_chat_model):
        """测试使用自定义模型初始化"""
        agent = JudgementAgent(model=mock_chat_model)
        assert agent.model == mock_chat_model

    def test_init_without_model(self):
        """测试不使用自定义模型初始化"""
        with patch('yuntai.agents.judgement_agent.get_judgement_model') as mock_get_model:
            mock_model = MagicMock()
            mock_get_model.return_value = mock_model
            
            agent = JudgementAgent()
            
            mock_get_model.assert_called_once()
            assert agent.model == mock_model

    def test_judge_empty_input(self, mock_chat_model):
        """测试空输入"""
        agent = JudgementAgent(model=mock_chat_model)
        
        result = agent.judge("")
        
        assert result.task_type == TASK_TYPE_FREE_CHAT
        assert result.target_app == ""
        assert result.target_object == ""
        assert result.is_auto is False
        assert result.specific_content == ""

    def test_judge_whitespace_input(self, mock_chat_model):
        """测试空白字符输入"""
        agent = JudgementAgent(model=mock_chat_model)
        
        result = agent.judge("   \n\t  ")
        
        assert result.task_type == TASK_TYPE_FREE_CHAT

    def test_judge_with_valid_json_response(self, mock_chat_model):
        """测试有效的JSON响应"""
        agent = JudgementAgent(model=mock_chat_model)
        
        # Mock返回有效的JSON
        response_json = {
            "task_type": TASK_TYPE_SINGLE_REPLY,
            "target_app": "微信",
            "target_object": "李四",
            "is_auto": False,
            "specific_content": ""
        }
        mock_chat_model.invoke.return_value = AIMessage(
            content=f"```json\n{json.dumps(response_json)}\n```"
        )
        
        result = agent.judge("给微信的李四发消息")
        
        assert result.task_type == TASK_TYPE_SINGLE_REPLY
        assert result.target_app == "微信"
        assert result.target_object == "李四"

    def test_judge_with_json_in_text(self, mock_chat_model):
        """测试JSON嵌入在文本中的响应"""
        agent = JudgementAgent(model=mock_chat_model)
        
        response_json = {
            "task_type": TASK_TYPE_BASIC_OPERATION,
            "target_app": "QQ",
            "target_object": "",
            "is_auto": False,
            "specific_content": ""
        }
        mock_chat_model.invoke.return_value = AIMessage(
            content=f"根据分析，结果是：{json.dumps(response_json)}，请执行。"
        )
        
        result = agent.judge("打开QQ")
        
        assert result.task_type == TASK_TYPE_BASIC_OPERATION
        assert result.target_app == "QQ"

    def test_judge_with_model_exception(self, mock_chat_model):
        """测试模型调用异常"""
        agent = JudgementAgent(model=mock_chat_model)
        
        # Mock抛出异常
        mock_chat_model.invoke.side_effect = Exception("API调用失败")
        
        result = agent.judge("打开微信")
        
        # 应该使用fallback逻辑
        assert result.task_type == TASK_TYPE_BASIC_OPERATION
        assert result.target_app == "微信"

    def test_judge_with_invalid_json(self, mock_chat_model):
        """测试无效的JSON响应"""
        agent = JudgementAgent(model=mock_chat_model)
        
        # Mock返回无效JSON
        mock_chat_model.invoke.return_value = AIMessage(
            content="这不是一个有效的JSON响应"
        )
        
        result = agent.judge("打开微信")
        
        # 应该使用fallback逻辑
        assert result.task_type == TASK_TYPE_BASIC_OPERATION

    def test_fallback_judge_continuous_reply(self, mock_chat_model):
        """测试fallback判断 - 持续回复"""
        agent = JudgementAgent(model=mock_chat_model)
        mock_chat_model.invoke.side_effect = Exception("触发fallback")
        
        result = agent.judge("auto打开微信给张三发消息")
        
        assert result.task_type == TASK_TYPE_CONTINUOUS_REPLY
        assert result.target_app == "微信"
        assert result.target_object == "张三"
        assert result.is_auto is True

    def test_fallback_judge_single_reply(self, mock_chat_model):
        """测试fallback判断 - 单次回复"""
        agent = JudgementAgent(model=mock_chat_model)
        mock_chat_model.invoke.side_effect = Exception("触发fallback")
        
        result = agent.judge("打开微信给李四发消息")
        
        assert result.task_type == TASK_TYPE_SINGLE_REPLY
        assert result.target_app == "微信"
        assert result.target_object == "李四"

    def test_fallback_judge_complex_operation(self, mock_chat_model):
        """测试fallback判断 - 复杂操作"""
        agent = JudgementAgent(model=mock_chat_model)
        mock_chat_model.invoke.side_effect = Exception("触发fallback")
        
        result = agent.judge('打开微信给王五发消息："你好，明天见"')
        
        assert result.task_type == TASK_TYPE_COMPLEX_OPERATION
        assert result.target_app == "微信"
        assert result.target_object == "王五"
        assert "你好，明天见" in result.specific_content

    def test_fallback_judge_basic_operation(self, mock_chat_model):
        """测试fallback判断 - 基础操作"""
        agent = JudgementAgent(model=mock_chat_model)
        mock_chat_model.invoke.side_effect = Exception("触发fallback")
        
        result = agent.judge("打开抖音")
        
        assert result.task_type == TASK_TYPE_BASIC_OPERATION
        assert result.target_app == "抖音"

    def test_fallback_judge_free_chat(self, mock_chat_model):
        """测试fallback判断 - 自由聊天"""
        agent = JudgementAgent(model=mock_chat_model)
        mock_chat_model.invoke.side_effect = Exception("触发fallback")
        
        result = agent.judge("今天天气怎么样")
        
        assert result.task_type == TASK_TYPE_FREE_CHAT

    def test_extract_app_qq(self, mock_chat_model):
        """测试提取APP - QQ"""
        agent = JudgementAgent(model=mock_chat_model)
        
        app = agent._extract_app("打开QQ")
        
        assert app == "qq"

    def test_extract_app_wechat(self, mock_chat_model):
        """测试提取APP - 微信"""
        agent = JudgementAgent(model=mock_chat_model)
        
        app = agent._extract_app("打开微信")
        
        assert app == "微信"

    def test_extract_app_douyin(self, mock_chat_model):
        """测试提取APP - 抖音"""
        agent = JudgementAgent(model=mock_chat_model)
        
        app = agent._extract_app("打开抖音")
        
        assert app == "抖音"

    def test_extract_app_not_found(self, mock_chat_model):
        """测试提取APP - 未找到"""
        agent = JudgementAgent(model=mock_chat_model)
        
        app = agent._extract_app("打开未知应用")
        
        assert app == ""

    def test_extract_object_with_gei(self, mock_chat_model):
        """测试提取聊天对象 - 给...发消息"""
        agent = JudgementAgent(model=mock_chat_model)
        
        obj = agent._extract_object("给张三发消息")
        
        assert obj == "张三"

    def test_extract_object_with_he(self, mock_chat_model):
        """测试提取聊天对象 - 和...聊天"""
        agent = JudgementAgent(model=mock_chat_model)
        
        obj = agent._extract_object("和李四聊天")
        
        assert obj == "李四"

    def test_extract_object_with_xiang(self, mock_chat_model):
        """测试提取聊天对象 - 向...发送"""
        agent = JudgementAgent(model=mock_chat_model)
        
        obj = agent._extract_object("向王五发送消息")
        
        assert obj == "王五"

    def test_extract_object_not_found(self, mock_chat_model):
        """测试提取聊天对象 - 未找到"""
        agent = JudgementAgent(model=mock_chat_model)
        
        obj = agent._extract_object("打开微信")
        
        assert obj == ""

    def test_extract_content_with_quotes(self, mock_chat_model):
        """测试提取消息内容 - 引号"""
        agent = JudgementAgent(model=mock_chat_model)
        
        content = agent._extract_content('发送消息："你好世界"')
        
        assert content == "你好世界"

    def test_extract_content_with_single_quotes(self, mock_chat_model):
        """测试提取消息内容 - 单引号"""
        agent = JudgementAgent(model=mock_chat_model)
        
        content = agent._extract_content("发送消息：'测试内容'")
        
        assert content == "测试内容"

    def test_extract_content_with_colon(self, mock_chat_model):
        """测试提取消息内容 - 冒号"""
        agent = JudgementAgent(model=mock_chat_model)
        
        content = agent._extract_content("发送消息：这是测试内容")
        
        assert content == "这是测试内容"

    def test_extract_content_with_time_format(self, mock_chat_model):
        """测试提取消息内容 - 时间格式（应被忽略）"""
        agent = JudgementAgent(model=mock_chat_model)
        
        content = agent._extract_content("时间：12:30")
        
        # 时间格式应该被忽略
        assert content == ""

    def test_extract_content_not_found(self, mock_chat_model):
        """测试提取消息内容 - 未找到"""
        agent = JudgementAgent(model=mock_chat_model)
        
        content = agent._extract_content("打开微信")
        
        assert content == ""

    def test_multiple_apps_in_input(self, mock_chat_model):
        """测试输入中包含多个APP名称"""
        agent = JudgementAgent(model=mock_chat_model)
        mock_chat_model.invoke.side_effect = Exception("触发fallback")
        
        # 应该返回第一个匹配的APP
        result = agent.judge("打开微信和QQ")
        
        assert result.target_app in ["微信", "qq"]
