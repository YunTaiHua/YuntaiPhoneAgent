import os
import threading
import time
import traceback
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from yuntai.gui_view import ThemeColors


class TTSHandler:
    """TTS语音合成处理器"""

    def __init__(self, controller):
        self.controller = controller
        self.root = controller.root
        self.view = controller.view
        self.task_manager = controller.task_manager

    def show_panel(self):
        """显示TTS语音合成页面"""
        self.view.create_tts_page(self.task_manager.tts_manager)
        self._bind_events()
        self.tts_update_synthesized_list()

    def _bind_events(self):
        """绑定TTS页面事件"""
        # 选择模型按钮
        select_gpt_btn = self.view.get_component("tts_select_gpt_btn")
        if select_gpt_btn:
            select_gpt_btn.configure(command=self.tts_select_gpt_model)

        select_sovits_btn = self.view.get_component("tts_select_sovits_btn")
        if select_sovits_btn:
            select_sovits_btn.configure(command=self.tts_select_sovits_model)

        select_audio_btn = self.view.get_component("tts_select_audio_btn")
        if select_audio_btn:
            select_audio_btn.configure(command=self.tts_select_ref_audio)

        select_text_btn = self.view.get_component("tts_select_text_btn")
        if select_text_btn:
            select_text_btn.configure(command=self.tts_select_ref_text)

        # 功能按钮
        synth_btn = self.view.get_component("tts_synth_btn")
        if synth_btn:
            synth_btn.configure(command=self.tts_start_synthesis)

        load_btn = self.view.get_component("tts_load_btn")
        if load_btn:
            load_btn.configure(command=self.tts_load_selected_models)

        stop_btn = self.view.get_component("tts_stop_btn")
        if stop_btn:
            stop_btn.configure(command=self.tts_stop_audio_playback)

        # TTS合成文本框回车绑定
        tts_text_input = self.view.get_component("tts_text_input")
        if tts_text_input:
            tts_text_input.bind("<Return>",
                                lambda e: self._handle_tts_synthesis_enter(e))
            tts_text_input.bind("<Control-Return>",
                                lambda e: self._handle_tts_synthesis_enter(e))
            tts_text_input.bind("<Shift-Return>",
                                lambda e: self._handle_tts_synthesis_enter(e))

        # 音频列表双击事件
        audio_listbox = self.view.get_component("tts_audio_listbox")
        if audio_listbox:
            audio_listbox.bind('<Double-Button-1>', self.tts_on_audio_double_click)

        # 音频列表按钮
        play_btn = self.view.get_component("tts_play_btn")
        if play_btn:
            play_btn.configure(command=self.tts_play_selected_audio)

        refresh_btn = self.view.get_component("tts_refresh_btn")
        if refresh_btn:
            refresh_btn.configure(command=self.tts_update_synthesized_list)

        delete_btn = self.view.get_component("tts_delete_btn")
        if delete_btn:
            delete_btn.configure(command=self.tts_delete_audio_files)

    def _handle_tts_synthesis_enter(self, event):
        """处理TTS合成文本框的回车事件"""
        modifiers = event.state
        ctrl_pressed = (modifiers & 0x0004) != 0
        shift_pressed = (modifiers & 0x0001) != 0

        if ctrl_pressed or shift_pressed:
            widget = event.widget
            widget.insert(tk.INSERT, "\n")
            return "break"
        else:
            self.tts_start_synthesis()
            return "break"

    def tts_add_log(self, msg):
        """添加TTS操作日志"""
        tts_log_text = self.view.get_component("tts_log_text")
        if tts_log_text and tts_log_text.winfo_exists():
            def update_gui():
                try:
                    tts_log_text.configure(state="normal")
                    timestamp = time.strftime("[%H:%M:%S]")
                    tts_log_text.insert("end", f"{timestamp} {msg}\n")
                    tts_log_text.see("end")
                    tts_log_text.configure(state="disabled")
                except tk.TclError:
                    pass

            self.root.after(0, update_gui)
        else:
            print(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def tts_update_synthesized_list(self):
        """更新TTS历史音频列表"""
        tts_audio_listbox = self.view.get_component("tts_audio_listbox")
        if tts_audio_listbox and tts_audio_listbox.winfo_exists():
            def update_gui():
                try:
                    tts_audio_listbox.delete(0, tk.END)
                    files = self.task_manager.tts_manager.load_synthesized_files()

                    if not files:
                        output_dir = self.task_manager.tts_manager.default_tts_config["output_path"]
                        if os.path.exists(output_dir):
                            wav_files = [f for f in os.listdir(output_dir) if f.endswith('.wav')]
                            self.tts_add_log(f"📁 发现 {len(wav_files)} 个音频文件在 {output_dir}")

                            for wav_file in sorted(wav_files, reverse=True):
                                abs_path = os.path.join(output_dir, wav_file)
                                with self.task_manager.tts_manager.tts_synthesized_files_lock:
                                    self.task_manager.tts_manager.tts_synthesized_files.append((abs_path, wav_file))

                            files = self.task_manager.tts_manager.tts_synthesized_files

                    for idx, (_, filename) in enumerate(files):
                        tts_audio_listbox.insert(idx, filename)

                    self.tts_add_log(f"✅ 音频列表已更新，共 {len(files)} 个文件")

                except Exception as e:
                    self.tts_add_log(f"❌ 更新音频列表失败: {str(e)}")

            self.root.after(0, update_gui)

    def tts_play_selected_audio(self):
        """播放选中的历史音频"""
        if hasattr(self.task_manager.tts_manager,
                   'is_playing_audio') and self.task_manager.tts_manager.is_playing_audio:
            self.tts_add_log("⚠️ 已有音频正在播放，跳过本次播放请求")
            return

        tts_audio_listbox = self.view.get_component("tts_audio_listbox")
        if not tts_audio_listbox:
            return

        selected_idx = tts_audio_listbox.curselection()
        if not selected_idx:
            self.tts_add_log("⚠️ 请先选择一个音频文件！")
            return

        idx = selected_idx[0]
        files = self.task_manager.tts_manager.load_synthesized_files()
        if 0 <= idx < len(files):
            audio_path = files[idx][0]

            if not os.path.exists(audio_path):
                self.tts_add_log(f"❌ 音频文件不存在: {audio_path}")
                return

            def play_thread():
                try:
                    self.tts_add_log(f"🔊 正在播放: {os.path.basename(audio_path)}")
                    self.task_manager.tts_manager.play_audio_file(audio_path)
                    self.tts_add_log(f"✅ 播放完成: {os.path.basename(audio_path)}")
                except Exception as e:
                    self.tts_add_log(f"❌ 播放失败: {str(e)}")

            threading.Thread(target=play_thread, daemon=True).start()
        else:
            self.tts_add_log("❌ 选择的文件索引无效")

    def tts_delete_audio_files(self):
        """删除所有历史音频文件"""
        result = messagebox.askyesno(
            "确认删除",
            "确定要删除所有历史音频文件吗？此操作不可恢复！",
            icon="warning"
        )

        if not result:
            self.tts_add_log("ℹ️ 已取消删除操作")
            return

        try:
            output_dir = self.task_manager.tts_manager.default_tts_config["output_path"]
            if not os.path.exists(output_dir):
                self.tts_add_log("⚠️ 音频目录不存在")
                return

            wav_files = [f for f in os.listdir(output_dir) if f.endswith('.wav')]

            if not wav_files:
                self.tts_add_log("ℹ️ 没有找到历史音频文件")
                return

            deleted_count = 0
            for wav_file in wav_files:
                file_path = os.path.join(output_dir, wav_file)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as e:
                    self.tts_add_log(f"❌ 删除失败 {wav_file}: {str(e)}")

            if deleted_count > 0:
                self.tts_add_log(f"✅ 已删除 {deleted_count} 个历史音频文件")
                self.tts_update_synthesized_list()
            else:
                self.tts_add_log("❌ 没有成功删除任何文件")

        except Exception as e:
            self.tts_add_log(f"❌ 删除音频文件失败: {str(e)}")

    def tts_on_audio_double_click(self, event):
        """双击播放音频"""
        self.tts_play_selected_audio()

    def tts_stop_audio_playback(self):
        """停止当前正在播放的音频"""
        if self.task_manager.stop_audio_playback():
            self.tts_add_log("⏹️ 已停止音频播放")
        else:
            self.tts_add_log("ℹ️ 当前没有正在播放的音频")

    def tts_select_gpt_model(self):
        """选择GPT模型"""
        if not self.task_manager.tts_manager.tts_files_database["gpt"]:
            self.tts_add_log("⚠️ 未找到任何GPT模型文件！")
            return

        def on_select(filename):
            if self.task_manager.tts_manager.set_current_model("gpt", filename):
                gpt_var = self.view.get_component("tts_gpt_var")
                if gpt_var:
                    gpt_var.set(filename)
                self.tts_add_log(f"📌 已选择GPT模型：{filename}")

        self._create_file_selection_popup(
            "选择GPT模型",
            self.task_manager.tts_manager.tts_files_database["gpt"],
            on_select
        )

    def tts_select_sovits_model(self):
        """选择SoVITS模型"""
        if not self.task_manager.tts_manager.tts_files_database["sovits"]:
            self.tts_add_log("⚠️ 未找到任何SoVITS模型文件！")
            return

        def on_select(filename):
            if self.task_manager.tts_manager.set_current_model("sovits", filename):
                sovits_var = self.view.get_component("tts_sovits_var")
                if sovits_var:
                    sovits_var.set(filename)
                self.tts_add_log(f"📌 已选择SoVITS模型：{filename}")

        self._create_file_selection_popup(
            "选择SoVITS模型",
            self.task_manager.tts_manager.tts_files_database["sovits"],
            on_select
        )

    def tts_select_ref_audio(self):
        """选择参考音频"""
        if not self.task_manager.tts_manager.tts_files_database["audio"]:
            self.tts_add_log("⚠️ 未找到任何参考音频文件！")
            return

        def on_select(filename):
            if self.task_manager.tts_manager.set_current_model("audio", filename):
                audio_var = self.view.get_component("tts_audio_var")
                if audio_var:
                    audio_var.set(filename)
                self.tts_add_log(f"📌 已选择参考音频：{filename}")

                txt_filename = os.path.splitext(filename)[0] + '.txt'
                if txt_filename in self.task_manager.tts_manager.tts_files_database["text"]:
                    if self.task_manager.tts_manager.set_current_model("text", txt_filename):
                        text_var = self.view.get_component("tts_text_var")
                        if text_var:
                            text_var.set(txt_filename)
                        self.tts_add_log(f"✅ 自动匹配参考文本：{txt_filename}")

        self._create_file_selection_popup(
            "选择参考音频",
            self.task_manager.tts_manager.tts_files_database["audio"],
            on_select
        )

    def tts_select_ref_text(self):
        """选择参考文本"""
        if not self.task_manager.tts_manager.tts_files_database["text"]:
            self.tts_add_log("⚠️ 未找到任何参考文本文件！")
            return

        def on_select(filename):
            if self.task_manager.tts_manager.set_current_model("text", filename):
                text_var = self.view.get_component("tts_text_var")
                if text_var:
                    text_var.set(filename)
                self.tts_add_log(f"📌 已选择参考文本：{filename}")

        self._create_file_selection_popup(
            "选择参考文本",
            self.task_manager.tts_manager.tts_files_database["text"],
            on_select
        )

    def _create_file_selection_popup(self, title, file_dict, select_callback):
        """创建文件选择弹窗"""
        select_win = ctk.CTkToplevel(self.root)
        select_win.title(title)
        select_win.geometry("500x400")
        select_win.transient(self.root)
        select_win.grab_set()

        style = ttk.Style()
        style.configure("Custom.Treeview", font=("Consolas", 12))
        style.configure("Custom.Treeview.Heading", font=("Consolas", 12, "bold"))

        tree = ttk.Treeview(select_win, style="Custom.Treeview", show="tree")
        tree.column("#0", width=450, minwidth=450)
        tree.pack(fill="both", expand=True, padx=15, pady=15)

        filenames = sorted(file_dict.keys())
        for filename in filenames:
            tree.insert("", "end", text=filename, values=(filename))

        def confirm_selection():
            selected = tree.selection()
            if selected:
                filename = tree.item(selected[0], "values")[0]
                select_callback(filename)
                select_win.destroy()
            else:
                messagebox.showwarning("警告", "请选择一个文件！")

        ctk.CTkButton(
            select_win,
            text="确认",
            font=("Microsoft YaHei", 12),
            width=120,
            height=35,
            command=confirm_selection
        ).pack(pady=15)

    def tts_load_selected_models(self):
        """加载选中的TTS模型"""
        if not self.task_manager.tts_manager.get_current_model("gpt") or \
                not self.task_manager.tts_manager.get_current_model("sovits"):
            self.tts_add_log("⚠️ 请先选择GPT和SoVITS模型！")
            return

        def load_thread():
            try:
                if not self.task_manager.tts_manager.tts_modules_loaded:
                    success, message = self.task_manager.tts_manager.load_tts_modules()
                    if not success:
                        self.tts_add_log(f"❌ 无法加载TTS模块: {message}")
                        return

                gpt_model = self.task_manager.tts_manager.get_current_model("gpt")
                sovits_model = self.task_manager.tts_manager.get_current_model("sovits")

                self.tts_add_log("🔄 正在加载GPT模型...")
                if 'change_gpt_weights' in self.task_manager.tts_manager.tts_modules:
                    self.task_manager.tts_manager.tts_modules['change_gpt_weights'](gpt_model)
                    self.tts_add_log("✅ GPT模型加载成功")

                self.tts_add_log("🔄 正在加载SoVITS模型...")
                if 'change_sovits_weights' in self.task_manager.tts_manager.tts_modules:
                    self.task_manager.tts_manager.tts_modules['change_sovits_weights'](sovits_model)
                    self.tts_add_log("✅ SoVITS模型加载成功")

                self.tts_add_log("✅ TTS模型加载完成，可以开始合成")
            except Exception as e:
                self.tts_add_log(f"❌ TTS模型加载失败: {str(e)}")
                traceback.print_exc()

        threading.Thread(target=load_thread, daemon=True).start()

    def tts_start_synthesis(self):
        """启动TTS合成"""
        if self.task_manager.tts_manager.is_tts_synthesizing:
            self.tts_add_log("⚠️ 正在合成中，请稍候")
            return

        tts_text_input = self.view.get_component("tts_text_input")
        if not tts_text_input:
            return

        target_text = tts_text_input.get("1.0", "end-1c").strip()
        if not target_text:
            self.tts_add_log("⚠️ 合成文本不能为空！")
            return

        if not self.task_manager.tts_manager.get_current_model("gpt") or \
                not self.task_manager.tts_manager.get_current_model("sovits"):
            self.tts_add_log("⚠️ 请先选择并加载模型！")
            return
        if not self.task_manager.tts_manager.get_current_model("audio"):
            self.tts_add_log("⚠️ 请先选择参考音频！")
            return
        if not self.task_manager.tts_manager.get_current_model("text"):
            self.tts_add_log("⚠️ 请先选择参考文本！")
            return

        ref_audio = self.task_manager.tts_manager.get_current_model("audio")
        ref_text = self.task_manager.tts_manager.get_current_model("text")

        def synth_thread():
            try:
                self.tts_add_log("🔄 语音合成中...")
                success, result = self.task_manager.tts_synthesize_text(
                    target_text, ref_audio, ref_text, auto_play=True
                )

                if success:
                    self.tts_add_log(f"✅ 合成完成")
                    self.tts_update_synthesized_list()
                else:
                    self.tts_add_log(f"❌ 合成失败: {result}")
            except Exception as e:
                self.tts_add_log(f"❌ 合成出错：{e}")

        threading.Thread(target=synth_thread, daemon=True).start()

    def show_tts_settings_popup(self):
        """显示TTS设置弹窗（从主控制器移动过来）"""
        import os
        popup = ctk.CTkToplevel(self.root)
        popup.title("🎤 TTS语音设置（语音合成有延迟）")
        popup.geometry("500x400")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        ctk.CTkLabel(
            popup,
            text="🎤 TTS语音设置（语音合成有延迟）",
            font=("Microsoft YaHei", 20, "bold")
        ).pack(pady=20)

        tts_enable_frame = ctk.CTkFrame(popup, fg_color="transparent")
        tts_enable_frame.pack(fill="x", padx=30, pady=10)

        tts_switch_var = ctk.StringVar(value="on" if self.task_manager.tts_manager.tts_enabled else "off")
        tts_switch = ctk.CTkSwitch(
            tts_enable_frame,
            text="启用语音播报",
            variable=tts_switch_var,
            onvalue="on",
            offvalue="off",
            font=("Microsoft YaHei", 14)
        )
        tts_switch.pack(pady=10)

        model_frame = ctk.CTkFrame(popup, fg_color="transparent")
        model_frame.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(
            model_frame,
            text="选择TTS模型:",
            font=("Microsoft YaHei", 14)
        ).pack(anchor="w", pady=(0, 10))

        gpt_frame = ctk.CTkFrame(model_frame, fg_color="transparent")
        gpt_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            gpt_frame,
            text="GPT模型:",
            font=("Microsoft YaHei", 12),
            width=80
        ).pack(side="left")

        gpt_var = ctk.StringVar(value="未选择")
        current_gpt = self.task_manager.tts_manager.get_current_model("gpt")
        if current_gpt and os.path.basename(current_gpt) in self.task_manager.tts_manager.tts_files_database["gpt"]:
            gpt_var.set(os.path.basename(current_gpt))

        gpt_menu = ctk.CTkOptionMenu(
            gpt_frame,
            variable=gpt_var,
            values=["未选择"] + list(self.task_manager.tts_manager.tts_files_database["gpt"].keys()),
            font=("Microsoft YaHei", 12),
            width=200
        )
        gpt_menu.pack(side="left", padx=(10, 0))

        sovits_frame = ctk.CTkFrame(model_frame, fg_color="transparent")
        sovits_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            sovits_frame,
            text="SoVITS模型:",
            font=("Microsoft YaHei", 12),
            width=80
        ).pack(side="left")

        sovits_var = ctk.StringVar(value="未选择")
        current_sovits = self.task_manager.tts_manager.get_current_model("sovits")
        if current_sovits and os.path.basename(current_sovits) in self.task_manager.tts_manager.tts_files_database[
            "sovits"]:
            sovits_var.set(os.path.basename(current_sovits))

        sovits_menu = ctk.CTkOptionMenu(
            sovits_frame,
            variable=sovits_var,
            values=["未选择"] + list(self.task_manager.tts_manager.tts_files_database["sovits"].keys()),
            font=("Microsoft YaHei", 12),
            width=200
        )
        sovits_menu.pack(side="left", padx=(10, 0))

        audio_frame = ctk.CTkFrame(model_frame, fg_color="transparent")
        audio_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            audio_frame,
            text="参考音频:",
            font=("Microsoft YaHei", 12),
            width=80
        ).pack(side="left")

        audio_var = ctk.StringVar(value="未选择")
        current_audio = self.task_manager.tts_manager.get_current_model("audio")
        if current_audio and os.path.basename(current_audio) in self.task_manager.tts_manager.tts_files_database[
            "audio"]:
            audio_var.set(os.path.basename(current_audio))

        audio_menu = ctk.CTkOptionMenu(
            audio_frame,
            variable=audio_var,
            values=["未选择"] + list(self.task_manager.tts_manager.tts_files_database["audio"].keys()),
            font=("Microsoft YaHei", 12),
            width=200
        )
        audio_menu.pack(side="left", padx=(10, 0))

        button_frame = ctk.CTkFrame(popup, fg_color="transparent")
        button_frame.pack(pady=20)

        def apply_settings():
            self.task_manager.tts_manager.tts_enabled = (tts_switch_var.get() == "on")

            # 通过主控制器更新TTS指示器
            self.controller.update_tts_indicator(self.task_manager.tts_manager.tts_enabled)

            if gpt_var.get() != "未选择":
                self.task_manager.tts_manager.set_current_model("gpt", gpt_var.get())

            if sovits_var.get() != "未选择":
                self.task_manager.tts_manager.set_current_model("sovits", sovits_var.get())

            if audio_var.get() != "未选择":
                self.task_manager.tts_manager.set_current_model("audio", audio_var.get())
                txt_filename = os.path.splitext(audio_var.get())[0] + '.txt'
                if txt_filename in self.task_manager.tts_manager.tts_files_database["text"]:
                    self.task_manager.tts_manager.set_current_model("text", txt_filename)

            self.controller.show_toast("TTS设置已保存", "success")
            popup.destroy()

        ctk.CTkButton(
            button_frame,
            text="保存设置",
            font=("Microsoft YaHei", 14),
            height=40,
            width=120,
            fg_color=ThemeColors.PRIMARY,
            command=apply_settings
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            button_frame,
            text="取消",
            font=("Microsoft YaHei", 14),
            height=40,
            width=120,
            fg_color=ThemeColors.TEXT_SECONDARY,
            command=popup.destroy
        ).pack(side="left", padx=10)
