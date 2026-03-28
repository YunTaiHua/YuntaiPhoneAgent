"""
LangGraph 状态定义模块
======================

本模块定义持续回复工作流的状态数据结构，使用 TypedDict 实现类型安全。

主要功能：
    - 定义工作流状态字段
    - 提供状态构建器
    - 支持列表合并去重

类说明：
    - ReplyState: 回复工作流状态定义（TypedDict）
    - ReplyStateBuilder: 状态构建器

使用示例：
    >>> from yuntai.graphs import ReplyState, ReplyStateBuilder
    >>> 
    >>> # 创建初始状态
    >>> state = ReplyStateBuilder.create(
    ...     app_name="微信",
    ...     chat_object="张三",
    ...     device_id="device_123"
    ... )
"""
import logging
from typing import Annotated, TypedDict
from operator import add

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


def merge_lists(left: list, right: list) -> list:
    """
    合并列表并去重
    
    用于 LangGraph 状态中列表字段的合并操作。
    将右侧列表中的元素添加到左侧列表，跳过重复元素。
    
    Args:
        left: 左侧列表（现有状态）
        right: 右侧列表（新状态）
    
    Returns:
        合并后的列表（已去重）
    
    使用示例：
        >>> merged = merge_lists([1, 2], [2, 3])
        >>> print(merged)  # [1, 2, 3]
    """
    # 复制左侧列表
    result = list(left)
    # 遍历右侧列表，添加不存在的元素
    for item in right:
        if item not in result:
            result.append(item)
    return result


class ReplyState(TypedDict):
    """
    回复工作流状态定义
    
    定义持续回复工作流中传递的所有状态字段。
    使用 TypedDict 确保类型安全和 IDE 支持。
    
    Attributes:
        app_name: 目标 APP 名称（如 "微信"、"QQ"）
        chat_object: 聊天对象名称
        device_id: 设备 ID
        cycle_count: 当前循环次数
        max_cycles: 最大循环次数
        should_continue: 是否继续循环
        terminate_flag: 终止标志
        extracted_records: 提取的原始聊天记录
        parse_success: 解析是否成功
        parsed_messages: 解析后的消息列表
        other_messages: 对方消息列表（累积）
        my_messages: 我方消息列表（累积）
        current_other_messages: 当前轮次对方消息
        current_my_messages: 当前轮次我方消息
        latest_message: 最新消息内容
        previous_latest_message: 上一轮最新消息
        is_new_message: 是否有新消息
        generated_reply: 生成的回复内容
        send_success: 发送是否成功
        last_sent_reply: 最后发送的回复
        error: 错误信息
        retry_count: 重试次数
        wait_seconds: 等待秒数
        result_message: 结果消息
        seen_other_messages: 已见过的对方消息
    
    使用示例：
        >>> state: ReplyState = {
        ...     "app_name": "微信",
        ...     "chat_object": "张三",
        ...     ...
        ... }
    """

    # ==================== 基本信息 ====================
    # 目标 APP 名称
    app_name: str
    # 聊天对象名称
    chat_object: str
    # 设备 ID
    device_id: str

    # ==================== 循环控制 ====================
    # 当前循环次数
    cycle_count: int
    # 最大循环次数
    max_cycles: int
    # 是否继续循环
    should_continue: bool
    # 终止标志
    terminate_flag: bool

    # ==================== 消息解析 ====================
    # 提取的原始聊天记录
    extracted_records: str
    # 解析是否成功
    parse_success: bool
    # 解析后的消息列表
    parsed_messages: list[dict[str, str]]

    # ==================== 消息记录 ====================
    # 对方消息列表（累积，使用 merge_lists 合并）
    other_messages: Annotated[list[str], merge_lists]
    # 我方消息列表（累积，使用 merge_lists 合并）
    my_messages: Annotated[list[str], merge_lists]
    # 当前轮次对方消息
    current_other_messages: list[str]
    # 当前轮次我方消息
    current_my_messages: list[str]

    # ==================== 最新消息 ====================
    # 最新消息内容
    latest_message: str
    # 上一轮最新消息（用于比较）
    previous_latest_message: str
    # 是否有新消息
    is_new_message: bool

    # ==================== 回复生成 ====================
    # 生成的回复内容
    generated_reply: str
    # 发送是否成功
    send_success: bool
    # 最后发送的回复
    last_sent_reply: str

    # ==================== 错误处理 ====================
    # 错误信息
    error: str | None
    # 重试次数
    retry_count: int
    # 等待秒数
    wait_seconds: int

    # ==================== 结果 ====================
    # 结果消息
    result_message: str
    # 已见过的对方消息（用于去重）
    seen_other_messages: list[str]


class ReplyStateBuilder:
    """
    回复状态构建器
    
    提供静态方法创建初始状态，确保所有字段都有默认值。
    
    使用示例：
        >>> state = ReplyStateBuilder.create(
        ...     app_name="微信",
        ...     chat_object="张三",
        ...     device_id="device_123",
        ...     max_cycles=30
        ... )
    """
    
    @staticmethod
    def create(
        app_name: str,
        chat_object: str,
        device_id: str = "",
        max_cycles: int = 30
    ) -> ReplyState:
        """
        创建初始状态
        
        创建包含所有必需字段的初始状态字典。
        
        Args:
            app_name: 目标 APP 名称
            chat_object: 聊天对象名称
            device_id: 设备 ID，默认为空
            max_cycles: 最大循环次数，默认为 30
        
        Returns:
            ReplyState: 初始状态字典
        
        使用示例：
            >>> state = ReplyStateBuilder.create("微信", "张三")
        """
        logger.debug("创建初始状态: APP=%s, 对象=%s", app_name, chat_object)
        
        return ReplyState(
            # 基本信息
            app_name=app_name,
            chat_object=chat_object,
            device_id=device_id,
            
            # 循环控制
            cycle_count=0,
            max_cycles=max_cycles,
            should_continue=True,
            terminate_flag=False,
            
            # 消息解析
            extracted_records="",
            parse_success=False,
            parsed_messages=[],
            
            # 消息记录
            other_messages=[],
            my_messages=[],
            current_other_messages=[],
            current_my_messages=[],
            
            # 最新消息
            latest_message="",
            previous_latest_message="",
            is_new_message=False,
            
            # 回复生成
            generated_reply="",
            send_success=False,
            last_sent_reply="",
            
            # 错误处理
            error=None,
            retry_count=0,
            wait_seconds=1,
            
            # 结果
            result_message="",
            seen_other_messages=[],
        )
