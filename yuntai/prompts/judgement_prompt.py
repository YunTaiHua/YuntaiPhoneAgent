"""
任务判断提示词模块
==================

提供任务类型判断的提示词模板和任务类型常量。

任务类型常量:
    - TASK_TYPE_FREE_CHAT: 自由聊天，用户只是想聊天
    - TASK_TYPE_BASIC_OPERATION: 基础操作，如打开APP
    - TASK_TYPE_SINGLE_REPLY: 单次回复，发送一次消息
    - TASK_TYPE_CONTINUOUS_REPLY: 持续回复，自动回复模式
    - TASK_TYPE_COMPLEX_OPERATION: 复杂操作，包含具体消息内容

主要组件:
    - TASK_JUDGEMENT_PROMPT: 任务判断提示词

使用场景:
    - 分析用户指令意图
    - 决定执行流程
"""
import logging

logger = logging.getLogger(__name__)

TASK_TYPE_FREE_CHAT = "free_chat"
TASK_TYPE_BASIC_OPERATION = "basic_operation"
TASK_TYPE_SINGLE_REPLY = "single_reply"
TASK_TYPE_CONTINUOUS_REPLY = "continuous_reply"
TASK_TYPE_COMPLEX_OPERATION = "complex_operation"

TASK_JUDGEMENT_PROMPT = """你是一个任务识别专家，负责分析用户输入的指令并判断任务类型。

任务类型定义：
1. free_chat：用户只是想和你自由聊天，或者表达感谢、问候等，不涉及手机操作
   - 如"你好"、"今天天气怎么样"、"谢谢你帮我打开抖音"
   - 判断依据：不包含"打开"、"发送"、"发消息"等操作关键词，主要是自然语言交流

2. basic_operation：用户想要打开某个APP
   - 如"打开QQ"、"打开微信"、"打开淘宝"
   - 判断依据：只包含"打开"和APP名称，不包含其他操作如"发消息"、"选购"、"点赞"等

3. single_reply：用户想要在某个APP中给某个联系人发送一次消息，但**没有指定具体消息内容**
   - 如"打开QQ给黄恬发消息"、"在微信里给张三发送消息"
   - 判断依据：包含"打开"、"发消息"/"发送"和联系人，但**不包含具体的消息内容文本**
   - **关键区别**：指令中没有引号或冒号后的具体消息内容

4. continuous_reply：用户想要在某个APP中给某个联系人持续回复消息
   - 如"打开QQ给黄恬发消息auto"、"打开微信给张三发消息 auto"
   - 判断依据：包含"打开"、"发消息"/"发送"和联系人，且包含"auto"或"持续"，同样**没有指定具体消息内容**

5. complex_operation：用户想要执行复杂的手机操作，**包括发送具体指定的消息内容**
   - 如"打开QQ给黄恬发送消息：你好呀"、"在微信里给张三发消息：晚上有空吗？"
   - 如"打开淘宝选购一个便宜的文具盒"、"打开抖音点赞"、"在QQ里搜索文件"、"用百度查一下明天的天气预报"、"使用学习通查看最新消息"
   - **发送具体消息的判断依据**：包含"打开"、"发消息"/"发送"、联系人，**并且有具体的消息内容文本（通常用引号或冒号标注）**

识别规则：
1. 首先检查是否包含感谢、问候等自然语言，如果是则归为free_chat
2. 检查是否包含"auto"或"持续"，如果有且包含"发消息"，则是continuous_reply（前提：没有具体消息内容）
3. 检查是否包含"发消息"或"发送"，如果有且不包含"auto"：
   - 如果**有具体的消息内容文本**，则是complex_operation
   - 如果**没有具体的消息内容文本**，则是single_reply
4. 检查是否只包含"打开"和APP名称，不包含其他操作，则是basic_operation
5. 如果包含"打开"或APP名称或其他复杂操作词，则是complex_operation
6. 其他情况默认是free_chat

返回格式要求：
请以JSON格式返回，包含以下字段：
{
  "task_type": "任务类型，只能是free_chat/basic_operation/single_reply/continuous_reply/complex_operation",
  "target_app": "目标APP，如QQ、微信等，如果没有则为空字符串",
  "target_object": "聊天对象，如果没有则为空字符串",
  "is_auto": true/false，是否为持续回复模式,
  "specific_content": "具体的消息内容，如果有则返回完整内容，否则为空字符串"
}

注意：只返回JSON格式，不要有其他任何内容。"""

__all__ = [
    "TASK_JUDGEMENT_PROMPT",
    "TASK_TYPE_FREE_CHAT",
    "TASK_TYPE_BASIC_OPERATION",
    "TASK_TYPE_SINGLE_REPLY",
    "TASK_TYPE_CONTINUOUS_REPLY",
    "TASK_TYPE_COMPLEX_OPERATION",
]
