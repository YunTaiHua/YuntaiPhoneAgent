"""

Phone Agent  - 智能版 v1.3.0  -第1321次迭代

1.0版本的更新日志：
1.0.0  （2025.12.14）官方main版本，必须在文件夹的终端打开
1.0.1  （2025.12.14）加入adb connect+手机IP，程序可直接用python打开，同时加入快捷键
1.0.2  （2025.12.14）引入GLM-4构建了双AI系统，同时实现了自由聊天和手机操作，GLM-4做决策，phone_agent执行
1.0.3  （2025.12.15）改变字体颜色，GLM-4输出为金色，phone_agent输出为绿色，最终输出为蓝色
1.0.4  （2025.12.15）优化双AI协作:
--------------------1.GLM-4智能判断任务类型（然后执行以下五种任务）
--------------------2.1.自由聊天，仅GLM-4响应
--------------------2.2.手机操作，phone_agent响应
--------------------2.3.单次回复：phone_agent提取聊天记录，GLM-4生成回复内容，phone_agent将回复内容发出
--------------------2.4.持续回复：phone_agent提取聊天记录，GLM-4生成回复内容，phone_agent将回复内容发出，phone_agent提取聊天记录，GLM-4判断是否有新消息，是则生成回复内容让phone_agent发出，否则让phone_agent继续提取聊天记录
--------------------2.5.复杂操作：GLM-4直接将原指令传达给phone_agent
1.0.5  （2025.12.15）优化phone_agent提示词，增加消息判断准则，根据气泡颜色判断，并加入conversation_history.json文件构建上下文和记录日志
1.0.6  （2025.12.18）修改消息判断规则：左侧有头像->对方消息，右侧有头像->我方消息
1.0.7  （2025.12.20）修改phone_agent提示词，要求准确返回头像位置信息
1.0.8  （2025.12.21）增加可查看和清空日志的功能
1.0.9  （2025.12.21）添加重试机制，若聊天记录提取失败则尝试重新提取

1.1版本的更新日志：
1.1.0  （2025.12.22）优化GLM-4提示词，使其能根据头像位置判断发送方
1.1.1  （2025.12.22）仅修改判断规则，位置为主，颜色为辅
1.1.2  （2025.12.23）修复消息归属判断，避免将我方消息误判为对方消息，加入消息相似度比对
1.1.3  （2025.12.24）添加记忆功能，forever.txt文件只可手动改写，系统只能读取不能操作，原有的记忆模块conversation_history.json保留
1.1.4  （2025.12.26）修复openai包更新后不兼容的问题（连同client一起修改）:
--------------------1.from openai import OpenAI -> import openai
--------------------2.check_model_api函数中client=OpenAI->client=openai.OpenAI
1.1.5  （2025.12.28）修改正则表达式，支持提取跨行聊天记录，包含三种正则表达式
1.1.6  （2025.12.28）更新了连接方式，支持无线连接和USB连接，同时拆分模块，所有模块保存在目录 yuntai 中
1.1.7  （2026.01.01）新增并行版本，由CLI变为GUI
1.1.8  （2026.01.06）整合TTS实现语音播报并具备单独的TTS语音界面
1.1.9  （2026.01.07）加入手机投屏功能，更可观的看见手机的操作过程

1.2版本的更新日志：
1.2.0  （2026.01.08）1.yuntai.rely_manger.py 更新了更好的消息提取方法
--------------------2.添加了详细注释，缓解了线程竞争的冲突，修复了AttributeError为NullWriter类添加了_process_tts_block方法
--------------------3.如果存在扫描产生的USB连接调试造成scrcpy连接混乱，在cmd中使用“adb disconnect adb-AADM023705011567-kUOrAE._adb-tls-connect._tcp”
1.2.1  （2026.01.09）模块化重构，将TTS、GUI组件、业务逻辑拆分为独立模块,文件保存在yun文件夹中不影响其他文件正常调用 yuntai 包,并升级了复杂操作和基础操作，使其也能实现TTS播报
1.2.2  （2026.01.15）引入glm-4.6v-flash实现多模态分析，glm-4.6v-flash替代原来所有的glm-4，现在AI Agent可以分析文本，视频，图片，文件，同时解决3.0.0中出现的adb连接混乱的问题
1.2.3  （2026.01.17）1.引入cogview-3-flash和cogvideox-flash作为双AI辅助系统，在动态功能菜单栏内集成文生图，文生视频，图生视频，首尾帧生视频的功能
--------------------2.修复“清空输出”按钮无响应的bug，合并版本号优化版本日志，目前版本为1.2.3（即原来的3.3.9）
--------------------3.图像生成、视频生成、TTS合成、执行命令四个按钮绑定"回车"按键
--------------------4.AI系统（总结）：双AI协作系统 ———— glm-4.6v-flash（原glm-4）、autoglm-phone | 双AI辅助系统 ———— cogview-3-flash、cogvideox-flash
1.2.4  （2026.01.19）1.使用FFmpeg和whisper为系统添加接收音频的功能
--------------------2.规范化命名了输出音频的名字，添加删除历史音频按钮
--------------------3.修复检测设备按钮失效的问题
--------------------4.解决语音播报在全英文状况下返回空列表的问题
1.2.5  （2026.01.20）1.新建.env文件保存敏感信息和路径配置
--------------------2.重构代码结构，合并yun和yuntai模块
--------------------3.移除颜色代码和冗余输出，界面更简洁
1.2.6  （2026.01.24）1.优化多模态文档支持类型和处理方法，使用 markitdown 统一处理文档转换
--------------------2.在聊天模型中分离出任务判断模型，可以在 config.py 中更自由的选择模型
--------------------3.点击播放视频后自动关闭弹窗
1.2.7  （2026.01.27）1.重构 gui_controller.py 文件，将原来的3000行缩减为800行，相关函数移动到 yuntai/handlers
--------------------2.重构 gui_view.py 文件，相关函数移动到 yuntai/views
--------------------3.重构 task_manager.py 文件，相关函数移到 yuntai/managers
1.2.8  （2026.01.30）1.优化异步处理导致程序退出的问题（Frame）
--------------------2.添加获取时间的方法
--------------------3.输入框随文本长度自动变高，支持换行
1.2.9  （2026.02.04）1.适配华为鸿蒙系统
--------------------2.优化 ui 界面，重构 ui 组件的布局
--------------------3.切换主题（light/dark）
--------------------4.优化 ui 组件显示异常问题
1.3.0  （2026.02.19）使用 langchain 重构任务判断和分发逻辑

"""

# ========================================
# 【1. 全局依赖导入区】
# ========================================
import tkinter as tk
import customtkinter as ctk
import threading
import sys
import os
import atexit
import warnings
import logging
from typing import NoReturn

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 过滤冗余警告
warnings.filterwarnings('ignore')

# 重构模块
from yuntai.main_app import MainApp

# 使用统一配置
from yuntai.config import GPT_SOVITS_ROOT


# ========================================
# 【2. 主函数入口区】
# ========================================
def main():
    """主函数：切换工作目录→初始化应用→启动主循环→退出时恢复目录"""
    try:
        # 保存原始工作目录
        original_cwd = os.getcwd()

        # 使用统一配置的 GPT-SoVITS 目录
        gpt_sovits_dir = GPT_SOVITS_ROOT
        if os.path.exists(gpt_sovits_dir):
            os.chdir(gpt_sovits_dir)
            #print(f"📂 切换到工作目录: {gpt_sovits_dir}")

        # 创建并运行应用
        app = MainApp()
        app.run()

        # 恢复原始工作目录
        os.chdir(original_cwd)

    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()