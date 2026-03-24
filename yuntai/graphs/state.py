"""LangGraph 状态定义"""
from typing import Annotated, TypedDict
from operator import add


def merge_lists(left: list, right: list) -> list:
    """合并列表，去重"""
    result = list(left)
    for item in right:
        if item not in result:
            result.append(item)
    return result


class ReplyState(TypedDict):
    """回复工作流状态定义"""

    # 基本信息
    app_name: str
    chat_object: str
    device_id: str

    # 循环控制
    cycle_count: int
    max_cycles: int
    should_continue: bool
    terminate_flag: bool

    # 消息解析
    extracted_records: str
    parse_success: bool
    parsed_messages: list[dict[str, str]]

    # 消息记录
    other_messages: Annotated[list[str], merge_lists]
    my_messages: Annotated[list[str], merge_lists]
    current_other_messages: list[str]
    current_my_messages: list[str]

    # 最新消息
    latest_message: str
    previous_latest_message: str
    is_new_message: bool

    # 回复生成
    generated_reply: str
    send_success: bool
    last_sent_reply: str

    # 错误处理
    error: str | None
    retry_count: int
    wait_seconds: int

    # 结果
    result_message: str
    seen_other_messages: list[str]


class ReplyStateBuilder:
    
    @staticmethod
    def create(app_name: str, chat_object: str, device_id: str = "", max_cycles: int = 30) -> ReplyState:
        return ReplyState(
            app_name=app_name,
            chat_object=chat_object,
            device_id=device_id,
            cycle_count=0,
            max_cycles=max_cycles,
            should_continue=True,
            terminate_flag=False,
            extracted_records="",
            parse_success=False,
            parsed_messages=[],
            other_messages=[],
            my_messages=[],
            current_other_messages=[],
            current_my_messages=[],
            latest_message="",
            previous_latest_message="",
            is_new_message=False,
            generated_reply="",
            send_success=False,
            last_sent_reply="",
            error=None,
            retry_count=0,
            wait_seconds=1,
            result_message="",
            seen_other_messages=[],
        )
