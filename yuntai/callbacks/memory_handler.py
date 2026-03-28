"""
记忆管理回调处理器模块
======================

本模块实现记忆管理回调处理器，用于自动记录对话历史到记忆系统。

主要功能：
    - 对话记录：自动捕获 LLM 的输入输出
    - 记忆存储：将对话保存到记忆管理器
    - 会话管理：支持按会话分类记录
    - 文件持久化：支持将对话保存到文件

类说明：
    - MemoryCallbackHandler: 基础记忆管理处理器
    - SessionMemoryCallbackHandler: 会话记忆处理器
    - FileBasedMemoryCallbackHandler: 基于文件的记忆处理器

使用示例：
    >>> from yuntai.callbacks import MemoryCallbackHandler
    >>> 
    >>> # 创建处理器
    >>> handler = MemoryCallbackHandler(
    ...     memory_manager=my_memory_manager,
    ...     auto_save=True
    ... )
    >>> 
    >>> # 在模型调用时使用
    >>> response = model.invoke(messages, config={"callbacks": [handler]})
"""
import logging
from datetime import datetime
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import HumanMessage, AIMessage

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


class MemoryCallbackHandler(BaseCallbackHandler):
    """
    记忆管理回调处理器
    
    自动捕获 LLM 的输入输出并记录到记忆系统。
    支持自动保存和历史记录管理。
    
    Attributes:
        memory_manager: 记忆管理器实例
        auto_save: 是否自动保存到记忆
        max_history: 最大历史记录数
        _current_user_input: 当前用户输入
        _current_ai_response: 当前 AI 响应
        _conversation_history: 对话历史列表
    
    使用示例：
        >>> handler = MemoryCallbackHandler(auto_save=True, max_history=50)
        >>> response = model.invoke(messages, config={"callbacks": [handler]})
    """
    
    def __init__(
        self,
        memory_manager=None,
        auto_save: bool = True,
        max_history: int = 50
    ):
        """
        初始化记忆管理处理器
        
        Args:
            memory_manager: 记忆管理器实例，需要实现 add_message 方法
            auto_save: 是否自动保存到记忆，默认为 True
            max_history: 最大历史记录数，默认为 50
        """
        super().__init__()
        # 记忆管理器实例
        self.memory_manager = memory_manager
        # 是否自动保存
        self.auto_save = auto_save
        # 最大历史记录数
        self.max_history = max_history
        
        # 临时存储当前对话
        self._current_user_input = ""
        self._current_ai_response = ""
        # 对话历史列表
        self._conversation_history = []
        
        logger.debug("MemoryCallbackHandler 初始化完成")
        
    def on_llm_start(
        self,
        serialized: dict[str, object],
        prompts: list[str],
        **kwargs: object
    ) -> None:
        """
        LLM 开始调用时，记录用户输入
        
        Args:
            serialized: 序列化的模型信息
            prompts: 提示词列表
            **kwargs: 其他参数
        """
        if prompts:
            # 提取用户输入（通常是最后一个提示词）
            self._current_user_input = prompts[-1] if prompts else ""
            logger.debug("记录用户输入，长度: %d", len(self._current_user_input))
    
    def on_llm_end(self, response: LLMResult, **kwargs: object) -> None:
        """
        LLM 调用结束时，记录 AI 响应
        
        Args:
            response: LLM 响应结果
            **kwargs: 其他参数
        """
        if response.generations and response.generations[0]:
            # 提取 AI 响应
            self._current_ai_response = response.generations[0][0].text
            
            # 自动保存到记忆
            if self.auto_save and self.memory_manager:
                self._save_to_memory()
    
    def _save_to_memory(self):
        """
        保存对话到记忆
        
        将当前对话保存到记忆管理器和历史记录列表。
        """
        # 检查是否有有效内容
        if not self._current_user_input or not self._current_ai_response:
            return
        
        try:
            # 添加到记忆管理器
            if hasattr(self.memory_manager, 'add_message'):
                self.memory_manager.add_message("user", self._current_user_input)
                self.memory_manager.add_message("assistant", self._current_ai_response)
                logger.debug("已保存对话到记忆管理器")
            
            # 添加到历史记录
            self._conversation_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user": self._current_user_input,
                "assistant": self._current_ai_response
            })
            
            # 限制历史记录长度
            if len(self._conversation_history) > self.max_history:
                self._conversation_history = self._conversation_history[-self.max_history:]
            
            # 清空当前对话
            self._current_user_input = ""
            self._current_ai_response = ""
            
        except Exception as e:
            logger.error("保存到记忆失败: %s", str(e), exc_info=True)
            print(f"⚠️ 保存到记忆失败: {e}")
    
    def get_conversation_history(self, limit: int = 10) -> list[dict[str, str]]:
        """
        获取对话历史
        
        Args:
            limit: 返回的记录数量限制，默认为 10
        
        Returns:
            对话历史列表，每条记录包含 timestamp, user, assistant 字段
        """
        return self._conversation_history[-limit:]
    
    def clear_history(self):
        """
        清空历史记录
        
        清除所有保存的对话历史。
        """
        logger.info("清空对话历史")
        self._conversation_history = []
    
    def get_messages_for_langchain(self, limit: int = 10) -> list:
        """
        获取 LangChain 格式的消息列表
        
        将对话历史转换为 LangChain 消息格式。
        
        Args:
            limit: 返回的记录数量限制
        
        Returns:
            LangChain 消息列表，包含 HumanMessage 和 AIMessage
        """
        messages = []
        history = self.get_conversation_history(limit)
        
        # 遍历历史记录，构建消息列表
        for conv in history:
            messages.append(HumanMessage(content=conv["user"]))
            messages.append(AIMessage(content=conv["assistant"]))
        
        return messages


class SessionMemoryCallbackHandler(MemoryCallbackHandler):
    """
    会话记忆回调处理器
    
    支持按会话（如按APP、按聊天对象）分类记录对话。
    继承自 MemoryCallbackHandler，增加会话管理功能。
    
    Attributes:
        _sessions: 会话存储字典
        _current_session_id: 当前会话 ID
    
    使用示例：
        >>> handler = SessionMemoryCallbackHandler()
        >>> handler.set_session("wechat_zhangsan")
        >>> response = model.invoke(messages, config={"callbacks": [handler]})
    """
    
    def __init__(
        self,
        memory_manager=None,
        auto_save: bool = True,
        max_history: int = 50
    ):
        """
        初始化会话记忆处理器
        
        Args:
            memory_manager: 记忆管理器实例
            auto_save: 是否自动保存到记忆
            max_history: 最大历史记录数
        """
        super().__init__(memory_manager, auto_save, max_history)
        
        # 会话存储：{session_id: [conversations]}
        self._sessions: dict[str, list[dict]] = {}
        # 当前会话 ID
        self._current_session_id: str | None = None
        
        logger.debug("SessionMemoryCallbackHandler 初始化完成")
    
    def set_session(self, session_id: str):
        """
        设置当前会话 ID
        
        切换到指定的会话，如果会话不存在则创建。
        
        Args:
            session_id: 会话标识符，如 "wechat_zhangsan"
        """
        logger.info("设置会话: %s", session_id)
        self._current_session_id = session_id
        
        # 初始化会话（如果不存在）
        if session_id not in self._sessions:
            self._sessions[session_id] = []
    
    def get_current_session(self) -> str | None:
        """
        获取当前会话 ID
        
        Returns:
            当前会话 ID，如果未设置则返回 None
        """
        return self._current_session_id
    
    def _save_to_memory(self):
        """
        保存对话到当前会话
        
        将对话保存到当前会话和全局历史记录。
        """
        # 检查是否有有效内容
        if not self._current_user_input or not self._current_ai_response:
            return
        
        # 构建对话记录
        conversation = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": self._current_user_input,
            "assistant": self._current_ai_response
        }
        
        # 保存到当前会话
        if self._current_session_id:
            # 确保会话存在
            if self._current_session_id not in self._sessions:
                self._sessions[self._current_session_id] = []
            
            # 添加到会话
            self._sessions[self._current_session_id].append(conversation)
            
            # 限制会话历史长度
            if len(self._sessions[self._current_session_id]) > self.max_history:
                self._sessions[self._current_session_id] = \
                    self._sessions[self._current_session_id][-self.max_history:]
            
            logger.debug("已保存对话到会话: %s", self._current_session_id)
        
        # 同时保存到全局历史（调用父类方法）
        super()._save_to_memory()
    
    def get_session_history(
        self,
        session_id: str | None = None,
        limit: int = 10
    ) -> list[dict[str, str]]:
        """
        获取指定会话的历史记录
        
        Args:
            session_id: 会话 ID，如果为 None 则使用当前会话
            limit: 返回的记录数量限制
        
        Returns:
            会话历史记录列表
        """
        # 确定要查询的会话 ID
        sid = session_id or self._current_session_id
        if not sid or sid not in self._sessions:
            return []
        
        return self._sessions[sid][-limit:]
    
    def get_all_sessions(self) -> dict[str, list[dict]]:
        """
        获取所有会话
        
        Returns:
            所有会话的字典，键为会话 ID，值为对话列表
        """
        return self._sessions
    
    def clear_session(self, session_id: str | None = None):
        """
        清空指定会话
        
        Args:
            session_id: 会话 ID，如果为 None 则清空当前会话
        """
        sid = session_id or self._current_session_id
        if sid and sid in self._sessions:
            logger.info("清空会话: %s", sid)
            self._sessions[sid] = []
    
    def clear_all_sessions(self):
        """
        清空所有会话
        
        清除所有会话的对话记录。
        """
        logger.info("清空所有会话")
        self._sessions = {}


class FileBasedMemoryCallbackHandler(MemoryCallbackHandler):
    """
    基于文件的记忆回调处理器
    
    自动将对话历史保存到文件。
    继承自 MemoryCallbackHandler，增加文件持久化功能。
    
    Attributes:
        file_manager: 文件管理器实例
    
    使用示例：
        >>> handler = FileBasedMemoryCallbackHandler(
        ...     file_manager=my_file_manager,
        ...     auto_save=True
        ... )
        >>> response = model.invoke(messages, config={"callbacks": [handler]})
    """
    
    def __init__(
        self,
        file_manager=None,
        memory_manager=None,
        auto_save: bool = True,
        max_history: int = 50
    ):
        """
        初始化基于文件的记忆处理器
        
        Args:
            file_manager: 文件管理器实例，需要实现 save_conversation_history 方法
            memory_manager: 记忆管理器实例
            auto_save: 是否自动保存到记忆
            max_history: 最大历史记录数
        """
        super().__init__(memory_manager, auto_save, max_history)
        # 文件管理器实例
        self.file_manager = file_manager
        
        logger.debug("FileBasedMemoryCallbackHandler 初始化完成")
    
    def _save_to_memory(self):
        """
        保存对话到文件
        
        将对话保存到内存和文件系统。
        """
        # 检查是否有有效内容
        if not self._current_user_input or not self._current_ai_response:
            return
        
        # 先调用父类方法保存到内存
        super()._save_to_memory()
        
        # 保存到文件
        if self.file_manager:
            try:
                # 构建会话数据
                session_data = {
                    "type": "free_chat",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_input": self._current_user_input,
                    "assistant_reply": self._current_ai_response,
                }
                
                # 调用文件管理器保存
                if hasattr(self.file_manager, 'save_conversation_history'):
                    self.file_manager.save_conversation_history(session_data)
                    logger.debug("已保存对话到文件")
                    
            except Exception as e:
                logger.error("保存到文件失败: %s", str(e), exc_info=True)
                print(f"⚠️ 保存到文件失败: {e}")
