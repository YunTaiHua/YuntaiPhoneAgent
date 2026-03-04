"""
  TTSHandler - TTS语音合成处理器 (PyQt6 重构版)
  负责处理TTS语音合成相关功能
"""

import os
import threading
import time
import traceback

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QComboBox, QCheckBox, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QKeySequence, QShortcut

from yuntai.gui.gui_view import GUIView
from yuntai.gui.styles import (
    ThemeColors, ThemeFonts, ThemeCorner,
    DialogStyle, get_dialog_stylesheet, get_dialog_button_stylesheet,
    get_dialog_card_stylesheet, get_dialog_tree_stylesheet,
    get_dialog_combobox_stylesheet, get_dialog_checkbox_stylesheet,
    show_warning_dialog, show_confirm_dialog
)
from yuntai.core.config import ThemeColors


class TTSHandler(QObject):
    """TTS语音合成处理器"""

    # 定义信号用于跨线程UI更新
    update_audio_list_signal = pyqtSignal(list)  # files list
    add_log_signal = pyqtSignal(str)  # log message
    # 新增信号用于替代QTimer.singleShot
    retry_bind_events_signal = pyqtSignal(int)  # attempt count
    update_audio_list_delayed_signal = pyqtSignal()  # 延迟更新音频列表

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.view = controller.view
        self.task_manager = controller.task_manager

        # 标记事件是否已绑定
        self._events_bound = False
        self._events_bound_success = False

        # 连接信号
        self.update_audio_list_signal.connect(self._on_update_audio_list)
        self.add_log_signal.connect(self._on_add_log)
        self.retry_bind_events_signal.connect(self._on_retry_bind_events)
        self.update_audio_list_delayed_signal.connect(self._on_update_audio_list_delayed)

    def _on_update_audio_list(self, files):
        """在主线程中更新音频列表"""
        if 'tts_audio_listbox' not in self.view.components:
            return
            
        tts_audio_listbox = self.view.components['tts_audio_listbox']
        tts_audio_listbox.clear()
        
        for _, filename in files:
            item = QListWidgetItem(filename)
            tts_audio_listbox.addItem(item)
        
        # 同步更新TTS管理器的文件列表
        with self.task_manager.tts_manager.tts_synthesized_files_lock:
            self.task_manager.tts_manager.tts_synthesized_files = files

    def _on_add_log(self, msg):
        """在主线程中添加日志"""
        tts_log_text = self.view.get_component("tts_log_text")
        if tts_log_text:
            try:
                timestamp = time.strftime("[%H:%M:%S]")
                current_text = tts_log_text.toPlainText()
                tts_log_text.setText(current_text + f"{timestamp} {msg}\n")
                # 滚动到底部
                cursor = tts_log_text.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                tts_log_text.setTextCursor(cursor)
            except Exception:
                pass
        else:
            print(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def show_panel(self):
        """显示TTS语音合成页面"""
        # 确保 tts_manager 被设置到 page_builder
        if hasattr(self.view, 'page_builder'):
            self.view.page_builder.tts_manager = self.task_manager.tts_manager

        # 先显示页面（这会触发页面创建）
        self.view.show_page(2)

        # 绑定事件（只绑定一次，但只有在成功时才标记为已绑定）
        if not self._events_bound:
            # 使用信号槽等待组件创建，避免阻塞主线程
            self._try_bind_events(0)

        # 更新音频列表（延迟执行，确保组件已创建）
        # 使用QTimer.singleShot延迟发射信号，确保组件已创建
        QTimer.singleShot(50, self.update_audio_list_delayed_signal.emit)
    
    def _try_bind_events(self, attempt: int, max_attempts: int = 10):
        """尝试绑定事件，使用信号槽非阻塞等待组件创建"""
        if attempt >= max_attempts:
            return

        if self.view.components.get('tts_audio_listbox') is not None:
            self._bind_events()
            # 检查绑定是否成功
            if self._events_bound_success:
                self._events_bound = True
        else:
            # 组件尚未创建，通过信号延迟重试
            QTimer.singleShot(50, lambda: self.retry_bind_events_signal.emit(attempt + 1))

    def _on_retry_bind_events(self, attempt: int):
        """信号槽：重试绑定事件"""
        self._try_bind_events(attempt)

    def _try_update_audio_list(self):
        """尝试更新音频列表"""
        if self.view.components.get('tts_audio_listbox') is not None:
            self.tts_update_synthesized_list()

    def _on_update_audio_list_delayed(self):
        """信号槽：延迟更新音频列表"""
        self._try_update_audio_list()

    def _bind_events(self):
        """绑定TTS页面事件"""
        # 选择模型按钮
        select_gpt_btn = self.view.get_component("tts_select_gpt_btn")
        if select_gpt_btn is not None:
            try:
                select_gpt_btn.clicked.disconnect()
            except:
                pass
            select_gpt_btn.clicked.connect(self.tts_select_gpt_model)

        select_sovits_btn = self.view.get_component("tts_select_sovits_btn")
        if select_sovits_btn is not None:
            try:
                select_sovits_btn.clicked.disconnect()
            except:
                pass
            select_sovits_btn.clicked.connect(self.tts_select_sovits_model)

        select_audio_btn = self.view.get_component("tts_select_audio_btn")
        if select_audio_btn is not None:
            try:
                select_audio_btn.clicked.disconnect()
            except:
                pass
            select_audio_btn.clicked.connect(self.tts_select_ref_audio)

        select_text_btn = self.view.get_component("tts_select_text_btn")
        if select_text_btn is not None:
            try:
                select_text_btn.clicked.disconnect()
            except:
                pass
            select_text_btn.clicked.connect(self.tts_select_ref_text)

        # 功能按钮
        synth_btn = self.view.get_component("tts_synth_btn")
        if synth_btn is not None:
            try:
                synth_btn.clicked.disconnect()
            except:
                pass
            synth_btn.clicked.connect(self.tts_start_synthesis)

        load_btn = self.view.get_component("tts_load_btn")
        if load_btn is not None:
            try:
                load_btn.clicked.disconnect()
            except:
                pass
            load_btn.clicked.connect(self.tts_load_selected_models)

        stop_btn = self.view.get_component("tts_stop_btn")
        if stop_btn is not None:
            try:
                stop_btn.clicked.disconnect()
            except:
                pass
            stop_btn.clicked.connect(self.tts_stop_audio_playback)

        # TTS合成文本框快捷键
        tts_text_input = self.view.get_component("tts_text_input")
        if tts_text_input is not None:
            # Enter 键合成
            enter_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), tts_text_input)
            enter_shortcut.activated.connect(self.tts_start_synthesis)

        # 音频列表双击事件
        audio_listbox = self.view.components.get('tts_audio_listbox')
        # 注意：PyQt6对象不能直接用if判断，必须显式检查is not None
        if audio_listbox is not None:
            try:
                audio_listbox.itemDoubleClicked.disconnect()
            except:
                pass
            audio_listbox.itemDoubleClicked.connect(self.tts_on_audio_double_click)

        # 音频列表按钮
        play_btn = self.view.get_component("tts_play_btn")
        if play_btn is not None:
            try:
                play_btn.clicked.disconnect()
            except:
                pass
            play_btn.clicked.connect(self.tts_play_selected_audio)

        refresh_btn = self.view.get_component("tts_refresh_btn")
        if refresh_btn is not None:
            try:
                refresh_btn.clicked.disconnect()
            except:
                pass
            refresh_btn.clicked.connect(self.tts_update_synthesized_list)

        delete_btn = self.view.get_component("tts_delete_btn")
        if delete_btn is not None:
            try:
                delete_btn.clicked.disconnect()
            except:
                pass
            delete_btn.clicked.connect(self.tts_delete_audio_files)

        # 检查所有关键组件是否都已绑定成功
        # 只有当audio_listbox存在且双击事件绑定成功时，才标记为成功
        if audio_listbox is not None:
            self._events_bound_success = True
        else:
            self._events_bound_success = False

    def tts_add_log(self, msg):
        """添加TTS操作日志 - 线程安全"""
        self.add_log_signal.emit(msg)

    def tts_update_synthesized_list(self):
        """更新TTS历史音频列表 - 在后台线程中执行"""
        def scan_thread():
            try:
                # 获取输出目录
                output_dir = self.task_manager.tts_manager.default_tts_config["output_path"]
                
                # 确保目录存在
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                    self.update_audio_list_signal.emit([])
                    return
                
                # 扫描目录中的wav文件
                wav_files = [f for f in os.listdir(output_dir) if f.endswith('.wav')]
                
                if not wav_files:
                    self.update_audio_list_signal.emit([])
                    return
                
                # 按时间倒序排列
                files = []
                for wav_file in sorted(wav_files, reverse=True):
                    abs_path = os.path.join(output_dir, wav_file)
                    files.append((abs_path, wav_file))
                
                # 通过信号更新UI
                self.update_audio_list_signal.emit(files)
                
            except Exception as e:
                self.tts_add_log(f"❌ 更新音频列表失败: {str(e)}")

        threading.Thread(target=scan_thread, daemon=True).start()

    def tts_play_selected_audio(self):
        """播放选中的历史音频"""
        if hasattr(self.task_manager.tts_manager,
                   'is_playing_audio') and self.task_manager.tts_manager.is_playing_audio:
            self.tts_add_log("⚠️ 已有音频正在播放，跳过本次播放请求")
            return

        tts_audio_listbox = self.view.get_component("tts_audio_listbox")
        if not tts_audio_listbox:
            return

        selected_items = tts_audio_listbox.selectedItems()
        if not selected_items:
            self.tts_add_log("⚠️ 请先选择一个音频文件！")
            return

        idx = tts_audio_listbox.row(selected_items[0])
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
        result = show_confirm_dialog(
            self.view,
            "确认删除",
            "确定要删除所有历史音频文件吗？此操作不可恢复！",
            "确认删除",
            "取消",
            "danger"
        )

        if not result:
            self.tts_add_log("ℹ️ 已取消删除操作")
            return

        def delete_thread():
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
                    # 刷新列表
                    self.tts_update_synthesized_list()
                else:
                    self.tts_add_log("❌ 没有成功删除任何文件")

            except Exception as e:
                self.tts_add_log(f"❌ 删除音频文件失败: {str(e)}")

        threading.Thread(target=delete_thread, daemon=True).start()

    def tts_on_audio_double_click(self, item):
        """双击播放音频"""
        
        # 直接使用双击的item，而不是依赖选中状态
        tts_audio_listbox = self.view.components.get('tts_audio_listbox')
        if not tts_audio_listbox:
            return
        
        # 获取双击项的索引
        idx = tts_audio_listbox.row(item)
        
        try:
            files = self.task_manager.tts_manager.load_synthesized_files()
        except Exception as e:
            self.tts_add_log(f"❌ 加载音频文件列表失败: {str(e)}")
            return
        
        if 0 <= idx < len(files):
            audio_path = files[idx][0]
            
            if not os.path.exists(audio_path):
                self.tts_add_log(f"❌ 音频文件不存在: {audio_path}")
                return
            
            # 检查是否有音频正在播放
            if hasattr(self.task_manager.tts_manager, 'is_playing_audio') and self.task_manager.tts_manager.is_playing_audio:
                self.tts_add_log("⚠️ 已有音频正在播放，跳过本次播放请求")
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
                gpt_label = self.view.get_component("tts_gpt_label")
                if gpt_label:
                    gpt_label.setText(filename)
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
                sovits_label = self.view.get_component("tts_sovits_label")
                if sovits_label:
                    sovits_label.setText(filename)
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
                audio_label = self.view.get_component("tts_audio_label")
                if audio_label:
                    audio_label.setText(filename)
                self.tts_add_log(f"📌 已选择参考音频：{filename}")

                txt_filename = os.path.splitext(filename)[0] + '.txt'
                if txt_filename in self.task_manager.tts_manager.tts_files_database["text"]:
                    if self.task_manager.tts_manager.set_current_model("text", txt_filename):
                        text_label = self.view.get_component("tts_text_label")
                        if text_label:
                            text_label.setText(txt_filename)
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
                text_label = self.view.get_component("tts_text_label")
                if text_label:
                    text_label.setText(filename)
                self.tts_add_log(f"📌 已选择参考文本：{filename}")

        self._create_file_selection_popup(
            "选择参考文本",
            self.task_manager.tts_manager.tts_files_database["text"],
            on_select
        )

    def _create_file_selection_popup(self, title, file_dict, select_callback):
        """创建文件选择弹窗"""
        dialog = QDialog(self.view)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(DialogStyle.DIALOG_WIDTH_MEDIUM, DialogStyle.DIALOG_HEIGHT_MEDIUM)
        dialog.setModal(True)
        
        # 获取当前主题颜色
        colors = self.view.colors if hasattr(self.view, 'colors') else ThemeColors
        dialog.setStyleSheet(get_dialog_stylesheet(colors))

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN
        )
        layout.setSpacing(DialogStyle.DIALOG_SPACING)

        # 标题
        title_label = QLabel(title)
        title_label.setFont(ThemeFonts.SUBTITLE)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent; border: none;")
        layout.addWidget(title_label)

        # 文件树
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        tree.setFont(ThemeFonts.CODE_SMALL)
        tree.setStyleSheet(get_dialog_tree_stylesheet(colors))

        filenames = sorted(file_dict.keys())
        for filename in filenames:
            item = QTreeWidgetItem([filename])
            tree.addTopLevelItem(item)

        layout.addWidget(tree, 1)

        def confirm_selection():
            selected = tree.selectedItems()
            if selected:
                filename = selected[0].text(0)
                select_callback(filename)
                dialog.accept()
            else:
                show_warning_dialog(dialog, "警告", "请选择一个文件！", "知道了")

        # 确认按钮
        confirm_btn = QPushButton("确认")
        confirm_btn.setFont(ThemeFonts.BODY_MEDIUM)
        confirm_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT)
        confirm_btn.setFixedWidth(DialogStyle.BUTTON_WIDTH)
        confirm_btn.setStyleSheet(get_dialog_button_stylesheet("primary", colors))
        confirm_btn.clicked.connect(confirm_selection)
        layout.addWidget(confirm_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        dialog.exec()

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

        target_text = tts_text_input.toPlainText().strip()
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
        """显示TTS设置弹窗"""
        dialog = QDialog(self.view)
        dialog.setWindowTitle("🎤 TTS语音设置")
        dialog.setFixedSize(DialogStyle.DIALOG_WIDTH_MEDIUM, DialogStyle.DIALOG_HEIGHT_MEDIUM)
        dialog.setModal(True)
        
        # 获取当前主题颜色
        colors = self.view.colors if hasattr(self.view, 'colors') else ThemeColors
        dialog.setStyleSheet(get_dialog_stylesheet(colors))

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN
        )
        layout.setSpacing(DialogStyle.DIALOG_SPACING)

        # 标题
        title_label = QLabel("🎤 TTS语音设置")
        title_label.setFont(ThemeFonts.TITLE)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent; border: none;")
        layout.addWidget(title_label)

        # 提示信息
        info_label = QLabel("（语音合成有延迟）")
        info_label.setFont(ThemeFonts.BODY_XSMALL)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent; border: none;")
        layout.addWidget(info_label)

        # 启用开关
        tts_switch = QCheckBox("启用语音播报")
        tts_switch.setFont(ThemeFonts.BODY_MEDIUM)
        tts_switch.setStyleSheet(get_dialog_checkbox_stylesheet(colors))
        tts_switch.setChecked(self.task_manager.tts_manager.tts_enabled)
        layout.addWidget(tts_switch)

        # 模型选择区域
        model_frame = QFrame()
        model_frame.setStyleSheet(get_dialog_card_stylesheet(colors))
        model_layout = QVBoxLayout(model_frame)
        model_layout.setContentsMargins(15, 15, 15, 15)
        model_layout.setSpacing(10)

        model_label = QLabel("选择TTS模型:")
        model_label.setFont(ThemeFonts.BODY_MEDIUM)
        model_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent; border: none;")
        model_layout.addWidget(model_label)

        # GPT模型
        gpt_layout = QHBoxLayout()
        gpt_label = QLabel("GPT模型:")
        gpt_label.setFont(ThemeFonts.BODY_MEDIUM)
        gpt_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent; border: none;")
        gpt_label.setFixedWidth(80)
        gpt_layout.addWidget(gpt_label)

        gpt_combo = QComboBox()
        gpt_combo.setFont(ThemeFonts.BODY_MEDIUM)
        gpt_combo.setStyleSheet(get_dialog_combobox_stylesheet(colors))
        gpt_combo.setFixedWidth(200)
        gpt_items = ["未选择"] + list(self.task_manager.tts_manager.tts_files_database["gpt"].keys())
        gpt_combo.addItems(gpt_items)
        current_gpt = self.task_manager.tts_manager.get_current_model("gpt")
        if current_gpt and os.path.basename(current_gpt) in self.task_manager.tts_manager.tts_files_database["gpt"]:
            gpt_combo.setCurrentText(os.path.basename(current_gpt))
        gpt_layout.addWidget(gpt_combo)
        gpt_layout.addStretch()
        model_layout.addLayout(gpt_layout)

        # SoVITS模型
        sovits_layout = QHBoxLayout()
        sovits_label = QLabel("SoVITS模型:")
        sovits_label.setFont(ThemeFonts.BODY_MEDIUM)
        sovits_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent; border: none;")
        sovits_label.setFixedWidth(80)
        sovits_layout.addWidget(sovits_label)

        sovits_combo = QComboBox()
        sovits_combo.setFont(ThemeFonts.BODY_MEDIUM)
        sovits_combo.setStyleSheet(get_dialog_combobox_stylesheet(colors))
        sovits_combo.setFixedWidth(200)
        sovits_items = ["未选择"] + list(self.task_manager.tts_manager.tts_files_database["sovits"].keys())
        sovits_combo.addItems(sovits_items)
        current_sovits = self.task_manager.tts_manager.get_current_model("sovits")
        if current_sovits and os.path.basename(current_sovits) in self.task_manager.tts_manager.tts_files_database["sovits"]:
            sovits_combo.setCurrentText(os.path.basename(current_sovits))
        sovits_layout.addWidget(sovits_combo)
        sovits_layout.addStretch()
        model_layout.addLayout(sovits_layout)

        # 参考音频
        audio_layout = QHBoxLayout()
        audio_label = QLabel("参考音频:")
        audio_label.setFont(ThemeFonts.BODY_MEDIUM)
        audio_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent; border: none;")
        audio_label.setFixedWidth(80)
        audio_layout.addWidget(audio_label)

        audio_combo = QComboBox()
        audio_combo.setFont(ThemeFonts.BODY_MEDIUM)
        audio_combo.setStyleSheet(get_dialog_combobox_stylesheet(colors))
        audio_combo.setFixedWidth(200)
        audio_items = ["未选择"] + list(self.task_manager.tts_manager.tts_files_database["audio"].keys())
        audio_combo.addItems(audio_items)
        current_audio = self.task_manager.tts_manager.get_current_model("audio")
        if current_audio and os.path.basename(current_audio) in self.task_manager.tts_manager.tts_files_database["audio"]:
            audio_combo.setCurrentText(os.path.basename(current_audio))
        audio_layout.addWidget(audio_combo)
        audio_layout.addStretch()
        model_layout.addLayout(audio_layout)

        layout.addWidget(model_frame)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        def apply_settings():
            self.task_manager.tts_manager.tts_enabled = tts_switch.isChecked()
            self.controller.update_tts_indicator(self.task_manager.tts_manager.tts_enabled)

            if gpt_combo.currentText() != "未选择":
                self.task_manager.tts_manager.set_current_model("gpt", gpt_combo.currentText())

            if sovits_combo.currentText() != "未选择":
                self.task_manager.tts_manager.set_current_model("sovits", sovits_combo.currentText())

            if audio_combo.currentText() != "未选择":
                self.task_manager.tts_manager.set_current_model("audio", audio_combo.currentText())
                txt_filename = os.path.splitext(audio_combo.currentText())[0] + '.txt'
                if txt_filename in self.task_manager.tts_manager.tts_files_database["text"]:
                    self.task_manager.tts_manager.set_current_model("text", txt_filename)

            self.controller.show_toast("TTS设置已保存", "success")
            dialog.accept()

        save_btn = QPushButton("保存设置")
        save_btn.setFont(ThemeFonts.BODY_MEDIUM)
        save_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT)
        save_btn.setFixedWidth(DialogStyle.BUTTON_WIDTH)
        save_btn.setStyleSheet(get_dialog_button_stylesheet("primary", colors))
        save_btn.clicked.connect(apply_settings)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setFont(ThemeFonts.BODY_MEDIUM)
        cancel_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT)
        cancel_btn.setFixedWidth(DialogStyle.BUTTON_WIDTH)
        cancel_btn.setStyleSheet(get_dialog_button_stylesheet("secondary", colors))
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        dialog.exec()
