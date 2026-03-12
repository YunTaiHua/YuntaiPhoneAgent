"""
tts_handler.py - TTS语音处理
"""

import os
import asyncio
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..controller import WebController


async def handle_tts_speak(websocket, data: dict, controller: "WebController"):
    """处理TTS语音播报（从控制中心）"""
    text = data.get("text", "").strip()
    if not text:
        await controller.send_toast("没有可播报的内容", "warning")
        return

    # 检查是否已选择参考音频和文本
    tts = controller.task_manager.tts_manager
    ref_audio = tts.get_current_model("audio")
    ref_text = tts.get_current_model("text")

    if not ref_audio or not ref_text:
        await controller.send_toast("请先选择参考音频和文本", "warning")
        return

    def speak_thread():
        try:
            controller.task_manager.tts_manager.speak_text_intelligently(text)
        except Exception as e:
            print(f"TTS播报失败: {e}")

    threading.Thread(target=speak_thread, daemon=True).start()
    await controller.send_toast("正在播报...", "info")


async def handle_tts_synth(websocket, data: dict, controller: "WebController"):
    """处理TTS合成"""
    text = data.get("text", "").strip()
    if not text:
        await controller.send_toast("请输入要合成的文本", "warning")
        return

    # 检查是否已选择参考音频和文本
    tts = controller.task_manager.tts_manager
    ref_audio = tts.get_current_model("audio")
    ref_text = tts.get_current_model("text")

    if not ref_audio or not ref_text:
        await controller.send_toast("请先选择参考音频和文本", "warning")
        return

    def synth_thread():
        try:
            tts = controller.task_manager.tts_manager
            # 使用正确的参数调用synthesize_text
            success, output_path = tts.synthesize_text(
                text=text,
                ref_audio_path=ref_audio,
                ref_text_path=ref_text,
                auto_play=False
            )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if success and output_path:
                    # 获取文件名
                    filename = os.path.basename(output_path)

                    # 发送TTS日志输出
                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "tts_log",
                        "message": f"✅ 语音合成完成: {filename}\n"
                    }))

                    # 构建正确的音频URL
                    audio_url = f"/api/tts/audio/{filename}"

                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "tts_synth_complete",
                        "audio_path": audio_url,
                        "audio_history": controller.get_audio_history()
                    }))
                else:
                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "tts_log",
                        "message": "❌ 语音合成失败\n"
                    }))
            finally:
                loop.close()
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.ws_manager.broadcast({
                    "type": "tts_log",
                    "message": f"❌ 合成错误: {str(e)}\n"
                }))
            finally:
                loop.close()

    threading.Thread(target=synth_thread, daemon=True).start()


async def handle_tts_select_model(websocket, data: dict, controller: "WebController"):
    """处理TTS模型选择"""
    model_type = data.get("model_type")
    model_name = data.get("model_name")

    if not model_type or not model_name:
        await controller.send_toast("参数错误", "error")
        return

    try:
        tts = controller.task_manager.tts_manager
        success = tts.set_current_model(model_type, model_name)

        # 如果选择的是参考音频，自动匹配对应的参考文本
        if success and model_type == "audio":
            audio_basename = os.path.splitext(model_name)[0]
            txt_filename = audio_basename + ".txt"
            text_files = list(tts.tts_files_database.get("text", {}).keys())
            if txt_filename in text_files:
                tts.set_current_model("text", txt_filename)

        # 如果选择的是参考文本，自动匹配对应的参考音频
        if success and model_type == "text":
            text_basename = os.path.splitext(model_name)[0]
            wav_filename = text_basename + ".wav"
            audio_files = list(tts.tts_files_database.get("audio", {}).keys())
            if wav_filename in audio_files:
                tts.set_current_model("audio", wav_filename)

        if success:
            await controller.send_toast(f"已选择: {model_name}", "success")
            await controller.ws_manager.broadcast({
                "type": "tts_models_update",
                "data": controller.get_tts_models()
            })
        else:
            await controller.send_toast(f"选择失败: 模型不存在", "error")
    except Exception as e:
        await controller.send_toast(f"选择失败: {str(e)}", "error")


async def handle_tts_load_models(websocket, controller: "WebController"):
    """处理加载TTS模型"""
    await controller.send_tts_loading("正在加载TTS模型...", True)

    def load_thread():
        try:
            success = controller.task_manager.preload_tts_modules()
            controller.tts_enabled = success
            controller._tts_loaded = True

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if success:
                    loop.run_until_complete(controller.send_toast("TTS模型加载成功", "success"))
                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "tts_models_update",
                        "data": controller.get_tts_models()
                    }))
                else:
                    loop.run_until_complete(controller.send_toast("TTS模型加载失败", "error"))
            finally:
                loop.close()
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.send_toast(f"加载错误: {str(e)}", "error"))
            finally:
                loop.close()
        finally:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.send_tts_loading("", False))
            finally:
                loop.close()

    threading.Thread(target=load_thread, daemon=True).start()


async def handle_tts_settings(websocket, data: dict, controller: "WebController"):
    """处理TTS设置请求"""
    try:
        enabled = data.get("enabled", False)
        gpt = data.get("gpt", "")
        sovits = data.get("sovits", "")
        audio = data.get("audio", "")

        controller.tts_enabled = enabled

        tts = controller.task_manager.tts_manager
        if gpt:
            tts.set_current_model("gpt", gpt)
        if sovits:
            tts.set_current_model("sovits", sovits)
        if audio:
            tts.set_current_model("audio", audio)
            # 自动匹配参考文本
            txt_filename = os.path.splitext(audio)[0] + '.txt'
            if txt_filename in tts.tts_files_database.get("text", {}):
                tts.set_current_model("text", txt_filename)

        # 更新状态
        await controller.send_state_update({
            "tts_enabled": enabled
        })
        await controller.ws_manager.broadcast({
            "type": "tts_models_update",
            "data": controller.get_tts_models()
        })

    except Exception as e:
        await controller.send_toast(f"TTS设置失败: {str(e)}", "error")
