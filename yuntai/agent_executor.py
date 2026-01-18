#!/usr/bin/env python3
"""
Agent执行器模块
"""
import re
from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig
from phone_agent.agent import AgentConfig

from yuntai.config import Color


class AgentExecutor:
    def __init__(self):
        pass

    def phone_agent_exec(self, task: str, args, task_type: str, device_id: str) -> tuple[str, list]:
        """phone_agent执行 - 使用绿色输出"""
        try:
            model_config = ModelConfig(
                base_url=args.base_url,
                model_name=args.model,
                api_key=args.apikey,
                lang=args.lang,
            )
            agent_config = AgentConfig(
                max_steps=args.max_steps,
                device_id=device_id,
                verbose=False,
                lang=args.lang,
            )
            phone_agent = PhoneAgent(model_config=model_config, agent_config=agent_config)

            task = task.strip()
            if not task:
                return "指令为空", ["指令为空"]

            # 如果是聊天相关任务，添加提示
            if "聊天" in task or "发消息" in task or "提取" in task:
                # 提取聊天记录使用专用提示词，其他聊天任务使用通用提示词
                if "提取" in task or "向下滑动" in task:
                    task = task + "\n\n" + """你是手机操作执行器，严格按指令执行：

重要：准确识别头像位置和气泡颜色是判断消息发送方的关键！

消息提取要求：
1. 准确描述每条消息气泡的颜色（如：白色、红色、蓝色、绿色、粉色等）
2. **非常重要**：准确描述每条消息的头像位置（左侧有头像、右侧有头像）
3. **绝对不要简化描述**，必须明确说明"左侧有头像"或"右侧有头像"
4. 注意：我方发送的消息通常在右侧有头像，气泡颜色可能是粉色、绿色等深色
5. 对方发送的消息通常在左侧有头像，气泡颜色通常是白色或浅色
6. 不要判断发送方，只需客观描述颜色和头像位置

执行要求：
1. 如果指令中指定了聊天对象，必须进入该对象的聊天窗口
2. 提取聊天记录时：键盘已经关闭，不需要点击空白处关闭键盘，直接向下滑动1次
3. 提取聊天记录时：不要向上滚动，只向下滑动1次
4. 发送消息时：准确输入并点击发送按钮
5. 发送消息必须完整，不要截断
6. 输出聊天记录时，包括：
   - 每条消息的内容
   - 每条消息的气泡颜色
   - 每条消息的头像位置（左侧有头像/右侧有头像）
7. 不要判断消息发送方，只需描述客观信息（颜色和头像位置）
8. 不要查看完整聊天历史或更早的聊天记录，只需当前屏幕可见消息
9. 发送消息后必须使用Back按钮关闭键盘
"""
                else:
                    task = task + "\n\n" + """你是手机操作执行器，严格按指令执行：

重要：准确识别头像位置和气泡颜色是判断消息发送方的关键！

消息提取要求：
1. 准确描述每条消息气泡的颜色（如：白色、红色、蓝色、绿色、粉色等）
2. **非常重要**：准确描述每条消息的头像位置（左侧有头像、右侧有头像）
3. **绝对不要简化描述**，必须明确说明"左侧有头像"或"右侧有头像"
4. 注意：我方发送的消息通常在右侧有头像，气泡颜色可能是粉色、绿色等深色
5. 对方发送的消息通常在左侧有头像，气泡颜色通常是白色或浅色
6. 不要判断发送方，只需客观描述颜色和头像位置

执行要求：
1. 如果指令中指定了聊天对象，必须进入该对象的聊天窗口
2. 提取聊天记录时：键盘已经关闭，不需要点击空白处关闭键盘，直接向下滑动1次
3. 提取聊天记录时：不要向上滚动，只向下滑动1次
4. 发送消息时：准确输入并点击发送按钮
5. 发送消息必须完整，不要截断
6. 输出聊天记录时，包括：
   - 每条消息的内容
   - 每条消息的气泡颜色
   - 每条消息的头像位置（左侧有头像/右侧有头像）
7. 不要判断消息发送方，只需描述客观信息（颜色和头像位置）
8. 不要查看完整聊天历史或更早的聊天记录，只需当前屏幕可见消息
9. 发送消息后必须使用Back按钮关闭键盘
"""

            raw_result = phone_agent.run(task)
            phone_agent.reset()

            # 简化输出
            filtered_result = raw_result
            filtered_result = re.sub(
                r"\n==================================================\n💭 思考过程:\n--------------------------------------------------\n.+?\n==================================================\n",
                "", filtered_result, flags=re.DOTALL)
            filtered_result = re.sub(
                r"\n==================================================\n⏱️  性能指标:\n--------------------------------------------------\n.+?\n==================================================\n",
                "", filtered_result, flags=re.DOTALL)
            filtered_result = re.sub(r"\n{3,}", "\n\n", filtered_result).strip()

            return filtered_result, [raw_result, filtered_result]

        except Exception as e:
            return f"任务执行失败：{str(e)}", [str(e)]