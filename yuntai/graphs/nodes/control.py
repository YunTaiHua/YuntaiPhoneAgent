"""流程控制节点"""
import time
import threading

from yuntai.graphs.state import ReplyState

_terminate_event: threading.Event | None = None


def set_terminate_event(event: threading.Event) -> None:
    """设置终止事件"""
    global _terminate_event
    _terminate_event = event


def check_terminate() -> bool:
    """检查是否收到终止信号"""
    if _terminate_event and _terminate_event.is_set():
        return True
    return False


def check_continue(state: ReplyState) -> dict:
    """
    检查是否继续节点
    
    输入: cycle_count, max_cycles, terminate_flag
    输出: should_continue
    """
    cycle_count = state["cycle_count"]
    max_cycles = state["max_cycles"]
    
    if check_terminate() or state.get("terminate_flag"):
        print("🛑 检测到终止信号，正在退出...")
        return {"should_continue": False, "terminate_flag": True}
    
    if cycle_count >= max_cycles:
        print(f"📊 达到最大循环次数 {max_cycles}")
        return {"should_continue": False}
    
    return {"should_continue": True}


def do_wait(state: ReplyState) -> dict:
    """
    等待节点
    
    输入: wait_seconds
    输出: None (仅等待)
    """
    wait_seconds = state.get("wait_seconds", 1)
    
    print(f"⏳ 等待 {wait_seconds} 秒...")
    
    for _ in range(wait_seconds):
        if check_terminate() or state.get("terminate_flag"):
            break
        time.sleep(1)
    
    return {}
