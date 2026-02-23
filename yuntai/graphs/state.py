"""
LangGraph 状态定义
"""
from typing import TypedDict, List, Dict, Optional, Annotated
from operator import add


def merge_lists(left: List, right: List) -> List:
    """合并列表，去重"""
    result = list(left)
    for item in right:
        if item not in result:
            result.append(item)
    return result


class ReplyState(TypedDict):
    app_name: str
    chat_object: str
    device_id: str
    
    cycle_count: int
    max_cycles: int
    should_continue: bool
    terminate_flag: bool
    
    extracted_records: str
    parse_success: bool
    parsed_messages: List[Dict[str, str]]
    
    other_messages: Annotated[List[str], merge_lists]
    my_messages: Annotated[List[str], merge_lists]
    current_other_messages: List[str]
    current_my_messages: List[str]
    
    latest_message: str
    previous_latest_message: str
    is_new_message: bool
    
    generated_reply: str
    send_success: bool
    last_sent_reply: str
    
    error: Optional[str]
    retry_count: int
    wait_seconds: int
    
    result_message: str
    
    seen_other_messages: List[str]


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
