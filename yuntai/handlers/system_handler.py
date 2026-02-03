import os
import threading
import customtkinter as ctk
from tkinter import messagebox

from yuntai.config import (
    CONVERSATION_HISTORY_FILE, RECORD_LOGS_DIR,
    FOREVER_MEMORY_FILE, CONNECTION_CONFIG_FILE,
    ZHIPU_API_BASE_URL, ZHIPU_MODEL, ZHIPU_API_KEY,
    DEVICE_TYPE_HARMONY
)
from yuntai.gui_view import ThemeColors
import tkinter as tk


class SystemHandler:
    """系统管理处理器 (历史/设置/文件)"""

    def __init__(self, controller):
        self.controller = controller
        self.root = controller.root
        self.view = controller.view
        self.task_manager = controller.task_manager

    def show_history_panel(self):
        """显示历史记录页面"""
        self.view.create_history_page()
        self._bind_history_events()
        self.load_history_data()

    def _bind_history_events(self):
        """绑定历史页面事件"""
        refresh_btn = self.view.get_component("refresh_history_btn")
        if refresh_btn:
            refresh_btn.configure(command=self.load_history_data)

        clear_btn = self.view.get_component("clear_history_btn")
        if clear_btn:
            clear_btn.configure(command=self.clear_history_data)

    def show_settings_panel(self):
        """显示系统设置页面"""
        self.view.create_settings_page()
        self._bind_settings_events()

    def _bind_settings_events(self):
        """绑定设置页面事件"""
        # 映射设置按钮到不同的Handler方法或主Controller方法
        settings_btns = [
            (self.view.get_component("settings_btn_0"), self.controller.connection_handler.show_panel),
            (self.view.get_component("settings_btn_1"), self.check_system_gui),
            (self.view.get_component("settings_btn_2"), self.controller.tts_handler.show_panel),
            (self.view.get_component("settings_btn_3"), self.show_file_management),
        ]

        for btn, command in settings_btns:
            if btn:
                btn.configure(command=command)

    def load_history_data(self):
        """加载历史数据"""
        try:
            history = self.task_manager.file_manager.safe_read_json_file(
                CONVERSATION_HISTORY_FILE,
                {"sessions": [], "free_chats": []}
            )

            text_content = ""

            # 聊天会话
            sessions = history.get("sessions", [])
            if sessions:
                text_content += "📱 聊天会话:\n" + "=" * 50 + "\n\n"
                for session in sessions[-20:]:
                    text_content += f"时间: {session.get('timestamp', '未知')}\n"
                    text_content += f"目标: {session.get('target_app', '未知')} -> {session.get('target_object', '未知')}\n"
                    if session.get('reply_generated'):
                        text_content += f"回复: {session.get('reply_generated')}\n"
                    text_content += "-" * 30 + "\n\n"

            # 自由聊天
            free_chats = history.get("free_chats", [])
            if free_chats:
                text_content += "\n💬 自由聊天:\n" + "=" * 50 + "\n\n"
                for chat in free_chats[-20:]:
                    text_content += f"时间: {chat.get('timestamp', '未知')}\n"
                    text_content += f"用户: {chat.get('user_input', '')}\n"
                    text_content += f"回复: {chat.get('assistant_reply', '')}\n"
                    text_content += "-" * 30 + "\n\n"

            if not text_content:
                text_content = "暂无历史记录"

            # 更新历史文本框
            history_text = self.view.get_component("history_text")
            if history_text:
                history_text.configure(state="normal")
                history_text.delete("1.0", tk.END)
                history_text.insert("1.0", text_content)
                history_text.configure(state="disabled")

            self.controller.show_toast("历史记录已刷新", "success")

        except Exception as e:
            self.controller.show_toast(f"加载历史失败: {str(e)}", "error")

    def clear_history_data(self):
        """清空历史数据"""
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗？此操作不可恢复！"):
            try:
                success = self.task_manager.file_manager.safe_write_json_file(
                    CONVERSATION_HISTORY_FILE,
                    {"sessions": [], "free_chats": []}
                )
                if success:
                    self.load_history_data()
                    self.controller.show_toast("历史记录已清空", "success")
                else:
                    self.controller.show_toast("清空历史失败", "error")
            except Exception as e:
                self.controller.show_toast(f"清空历史失败: {str(e)}", "error")

    def check_system_gui(self):
        """可视化系统检查"""
        from yuntai.config import ZHIPU_API_BASE_URL, ZHIPU_MODEL, ZHIPU_API_KEY

        device_type_var = self.view.get_component("device_type_var")
        is_harmony = False
        if device_type_var and device_type_var.get() and "HarmonyOS" in device_type_var.get():
            is_harmony = True

        check_window = ctk.CTkToplevel(self.root)
        check_window.title("🔍 系统检查")
        check_window.geometry("600x400")
        check_window.resizable(False, False)
        check_window.transient(self.root)
        check_window.grab_set()

        title_frame = ctk.CTkFrame(check_window, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            title_frame,
            text="🔍 系统检查",
            font=("Microsoft YaHei", 20, "bold")
        ).pack(anchor="w")

        device_type_name = "HarmonyOS (HDC)" if is_harmony else "Android (ADB)"
        ctk.CTkLabel(
            title_frame,
            text=f"正在检查 {device_type_name} 系统配置...",
            font=("Microsoft YaHei", 12),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack(anchor="w", pady=(5, 0))

        result_frame = ctk.CTkFrame(check_window, corner_radius=10)
        result_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        result_text = ctk.CTkTextbox(
            result_frame,
            font=("Consolas", 12),
            activate_scrollbars=True
        )
        result_text.pack(fill="both", expand=True, padx=10, pady=10)

        status_label = ctk.CTkLabel(
            check_window,
            text="准备开始检查...",
            font=("Microsoft YaHei", 11)
        )
        status_label.pack(side="left", padx=20, pady=(0, 10))

        def check_thread():
            try:
                tool_name = "HDC" if is_harmony else "ADB"
                check_window.after(0, lambda: status_label.configure(text=f"检查{tool_name}环境..."))

                if is_harmony:
                    tool_result = self.task_manager.utils.check_hdc()

                    result_text.insert("end", "=" * 60 + "\n")
                    result_text.insert("end", "📱 HDC 环境检查\n")
                    result_text.insert("end", "=" * 60 + "\n")
                    if tool_result:
                        result_text.insert("end", "✅ HDC检查通过\n")
                        result_text.insert("end", "  HDC工具已安装\n")
                        result_text.insert("end", "  HarmonyOS设备连接功能正常\n\n")
                    else:
                        result_text.insert("end", "❌ HDC检查失败\n")
                        result_text.insert("end", "  HDC工具未安装或不在PATH中\n")
                        result_text.insert("end", "\n💡 解决方案:\n")
                        result_text.insert("end", "  1. 下载HarmonyOS SDK\n")
                        result_text.insert("end", "  2. 从SDK目录找到hdc工具\n")
                        result_text.insert("end", "  3. 将hdc添加到系统PATH环境变量\n\n")
                else:
                    tool_result = self.task_manager.utils.check_system_requirements()

                    result_text.insert("end", "=" * 60 + "\n")
                    result_text.insert("end", "📱 ADB 环境检查\n")
                    result_text.insert("end", "=" * 60 + "\n")
                    if tool_result:
                        result_text.insert("end", "✅ ADB检查通过\n")
                        result_text.insert("end", "  ADB工具已安装\n")
                        result_text.insert("end", "  Android设备连接功能正常\n\n")
                    else:
                        result_text.insert("end", "❌ ADB检查失败\n")
                        result_text.insert("end", "  请确保已安装ADB并添加到系统PATH\n\n")

                check_window.after(0, lambda: status_label.configure(text="检查模型API..."))

                api_result = self.task_manager.utils.check_model_api(
                    ZHIPU_API_BASE_URL,
                    ZHIPU_MODEL,
                    ZHIPU_API_KEY
                )

                result_text.insert("end", "=" * 60 + "\n")
                result_text.insert("end", "🤖 模型API检查\n")
                result_text.insert("end", "=" * 60 + "\n")
                if api_result:
                    result_text.insert("end", "✅ 模型API检查通过\n")
                    result_text.insert("end", f"  模型: {ZHIPU_MODEL}\n")
                    result_text.insert("end", f"  密钥: {ZHIPU_API_KEY[:10]}...\n\n")
                else:
                    result_text.insert("end", "❌ 模型API检查失败\n")
                    result_text.insert("end", "  请检查API密钥或网络连接\n\n")

                check_window.after(0, lambda: status_label.configure(text="检查TTS功能..."))

                result_text.insert("end", "=" * 60 + "\n")
                result_text.insert("end", "🎤 TTS功能检查\n")
                result_text.insert("end", "=" * 60 + "\n")

                if self.task_manager.tts_manager.tts_available:
                    result_text.insert("end", "✅ TTS模块可用\n")

                    gpt_count = len(self.task_manager.tts_manager.tts_files_database["gpt"])
                    sovits_count = len(self.task_manager.tts_manager.tts_files_database["sovits"])
                    audio_count = len(self.task_manager.tts_manager.tts_files_database["audio"])
                    text_count = len(self.task_manager.tts_manager.tts_files_database["text"])

                    result_text.insert("end", f"  GPT模型: {gpt_count} 个\n")
                    result_text.insert("end", f"  SoVITS模型: {sovits_count} 个\n")
                    result_text.insert("end", f"  参考音频: {audio_count} 个\n")
                    result_text.insert("end", f"  参考文本: {text_count} 个\n")

                    if gpt_count > 0 and sovits_count > 0 and audio_count > 0 and text_count > 0:
                        result_text.insert("end", "  ✅ TTS资源完整\n")
                    else:
                        result_text.insert("end", "  ⚠️  TTS资源不完整\n")
                else:
                    result_text.insert("end", "❌ TTS模块不可用\n")
                    result_text.insert("end", "  请安装GPT-SoVITS并配置环境\n")

                result_text.insert("end", "\n")

                check_window.after(0, lambda: status_label.configure(text="检查设备连接..."))

                result_text.insert("end", "=" * 60 + "\n")
                result_text.insert("end", "📱 设备连接检查\n")
                result_text.insert("end", "=" * 60 + "\n")

                if self.task_manager.is_connected:
                    result_text.insert("end", f"✅ 设备已连接: {self.task_manager.device_id}\n")
                    conn_type = self.task_manager.config.get('connection_type', '未知')
                    result_text.insert("end", f"  连接类型: {conn_type}\n")
                else:
                    result_text.insert("end", "⚠️  设备未连接\n")
                    result_text.insert("end", "  请前往设备管理页面连接设备\n")

                result_text.insert("end", "\n" + "=" * 60 + "\n")
                result_text.insert("end", "📋 检查结论\n")
                result_text.insert("end", "=" * 60 + "\n")

                if tool_result and api_result:
                    result_text.insert("end", "🎉 系统检查通过，核心组件正常\n")
                    check_window.after(0, lambda: status_label.configure(
                        text="检查完成，核心组件正常",
                        text_color=ThemeColors.SUCCESS
                    ))
                else:
                    result_text.insert("end", "⚠️  系统检查发现一些问题\n")
                    check_window.after(0, lambda: status_label.configure(
                        text="检查完成，发现一些问题",
                        text_color=ThemeColors.WARNING
                    ))

                result_text.see("1.0")

            except Exception as e:
                result_text.insert("end", f"\n❌ 检查过程中发生错误: {str(e)}\n")
                check_window.after(0, lambda: status_label.configure(
                    text=f"检查出错: {str(e)[:30]}...",
                    text_color=ThemeColors.DANGER
                ))

        threading.Thread(target=check_thread, daemon=True).start()

    def show_file_management(self):
        """显示文件管理"""
        try:
            info_text = f"""文件管理:

历史记录文件: {CONVERSATION_HISTORY_FILE}
日志目录: {RECORD_LOGS_DIR}/
永久记忆文件: {FOREVER_MEMORY_FILE}
连接配置文件: {CONNECTION_CONFIG_FILE}

TTS相关目录:
• GPT模型目录: {self.task_manager.tts_manager.default_tts_config['gpt_model_dir']}
• SoVITS模型目录: {self.task_manager.tts_manager.default_tts_config['sovits_model_dir']}
• 参考音频目录: {self.task_manager.tts_manager.default_tts_config['ref_audio_root']}
• TTS输出目录: {self.task_manager.tts_manager.default_tts_config['output_path']}

文件状态:
• 历史记录文件: {'存在' if os.path.exists(CONVERSATION_HISTORY_FILE) else '不存在'}
• 日志目录: {'存在' if os.path.exists(RECORD_LOGS_DIR) else '不存在'}
• 永久记忆文件: {'存在' if os.path.exists(FOREVER_MEMORY_FILE) else '不存在'}
• 连接配置文件: {'存在' if os.path.exists(CONNECTION_CONFIG_FILE) else '不存在'}"""
            messagebox.showinfo("文件管理", info_text)
        except Exception as e:
            messagebox.showerror("错误", f"获取文件信息失败: {str(e)}")
