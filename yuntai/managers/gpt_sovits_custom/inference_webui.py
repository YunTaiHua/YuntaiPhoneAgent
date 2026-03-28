"""
GPT-SoVITS 推理 WebUI 模块
==========================

本模块提供 GPT-SoVITS 语音合成系统的完整推理功能。

主要功能:
    - get_tts_wav: 文本转语音合成主函数
    - change_gpt_weights: 切换 GPT 模型权重
    - change_sovits_weights: 切换 SoVITS 模型权重
    - I18nAuto: 国际化自动翻译工具

支持的语种:
    - 中文、英文、日文、粤语、韩文
    - 中英混合、日英混合、粤英混合、韩英混合
    - 多语种混合识别

模型版本:
    - v1: 基础版本
    - v2: 改进版本
    - v3: BigVGAN 声码器版本
    - v4: HiFi-GAN 声码器版本
    - v2Pro/v2ProPlus: 带说话人嵌入的增强版本

使用示例:
    >>> from yuntai.managers.gpt_sovits_custom import get_tts_wav
    >>> # 切换模型
    >>> change_gpt_weights("path/to/gpt.ckpt")
    >>> change_sovits_weights("path/to/sovits.pth")
    >>> # 合成语音
    >>> for sr, audio in get_tts_wav(
    ...     ref_wav_path="reference.wav",
    ...     prompt_text="参考文本",
    ...     prompt_language="中文",
    ...     text="要合成的文本",
    ...     text_language="中文"
    ... ):
    ...     pass  # 处理音频数据

注意事项:
    - 需要配置 GPT_SOVITS_ROOT 环境变量
    - 参考音频建议 3-10 秒
    - v3/v4 版本不支持无参考文本模式
"""
import os
from pathlib import Path

os.environ['TQDM_DISABLE'] = '1'

try:
    import psutil

    def set_high_priority():
        """把当前 Python 进程设为 HIGH_PRIORITY_CLASS"""
        if os.name != "nt":
            return
        p = psutil.Process(os.getpid())
        try:
            p.nice(psutil.HIGH_PRIORITY_CLASS)
        except psutil.AccessDenied:
            pass
    set_high_priority()
except ImportError:
    pass

import json
import logging
import os
import re
import sys
import traceback
import warnings


try:
    import torch
    import torchaudio
except ImportError as e:
    raise ImportError(f"torch 或 torchaudio 导入失败: {e}")


try:
    from text.LangSegmenter import LangSegmenter
except ImportError:
    LangSegmenter = None

logging.getLogger("markdown_it").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("charset_normalizer").setLevel(logging.ERROR)
logging.getLogger("torchaudio._extension").setLevel(logging.ERROR)
logging.getLogger("multipart.multipart").setLevel(logging.ERROR)
warnings.simplefilter(action="ignore", category=FutureWarning)

logger = logging.getLogger(__name__)

version = model_version = os.environ.get("version", "v2")

from config import change_choices, get_weights_names, name2gpt_path, name2sovits_path

SoVITS_names, GPT_names = get_weights_names()
from config import pretrained_sovits_name

path_sovits_v3 = pretrained_sovits_name["v3"]
path_sovits_v4 = pretrained_sovits_name["v4"]
is_exist_s2gv3 = Path(path_sovits_v3).exists()
is_exist_s2gv4 = Path(path_sovits_v4).exists()

weight_json_path = Path("./weight.json")
if weight_json_path.exists():
    pass
else:
    weight_json_path.write_text(json.dumps({"GPT": {}, "SoVITS": {}}, ensure_ascii=False), encoding="utf-8")

weight_data = json.loads(weight_json_path.read_text(encoding="utf-8"))
gpt_path = os.environ.get("gpt_path", weight_data.get("GPT", {}).get(version, GPT_names[-1]))
sovits_path = os.environ.get("sovits_path", weight_data.get("SoVITS", {}).get(version, SoVITS_names[0]))
if isinstance(gpt_path, list):
    gpt_path = gpt_path[0]
if isinstance(sovits_path, list):
    sovits_path = sovits_path[0]

gpt_sovits_root = os.environ.get("GPT_SOVITS_ROOT")
if not gpt_sovits_root:
    raise EnvironmentError("环境变量 GPT_SOVITS_ROOT 未设置，请在.env文件中配置")
gpt_sovits_root_path = Path(gpt_sovits_root)
cnhubert_base_path = os.environ.get("cnhubert_base_path", str(gpt_sovits_root_path / "GPT_SoVITS" / "pretrained_models" / "chinese-hubert-base"))
bert_path = os.environ.get("bert_path", str(gpt_sovits_root_path / "GPT_SoVITS" / "pretrained_models" / "chinese-roberta-wwm-ext-large"))
infer_ttswebui = os.environ.get("infer_ttswebui", 9872)
infer_ttswebui = int(infer_ttswebui)
is_share = os.environ.get("is_share", "False")
is_share = eval(is_share)
if "_CUDA_VISIBLE_DEVICES" in os.environ:
    os.environ["CUDA_VISIBLE_DEVICES"] = os.environ["_CUDA_VISIBLE_DEVICES"]
is_half = eval(os.environ.get("is_half", "True")) and torch.cuda.is_available()
punctuation = set(["!", "?", "…", ",", ".", "-", " "])

try:
    import gradio as gr
except ImportError:
    gr = None

try:
    import librosa
except ImportError:
    librosa = None

import numpy as np


try:
    from feature_extractor import cnhubert
except ImportError:
    cnhubert = None


try:
    from transformers import AutoModelForMaskedLM, AutoTokenizer
except ImportError:
    AutoModelForMaskedLM = None
    AutoTokenizer = None

cnhubert.cnhubert_base_path = cnhubert_base_path

import random


try:
    from GPT_SoVITS.module.models import Generator, SynthesizerTrn, SynthesizerTrnV3
except ImportError:
    Generator = None
    SynthesizerTrn = None
    SynthesizerTrnV3 = None


def set_seed(seed: int) -> None:
    """
    设置随机种子
    
    用于确保推理结果的可复现性。
    
    Args:
        seed: 随机种子值，-1 表示使用随机种子
    """
    if seed == -1:
        seed = random.randint(0, 1000000)
    seed = int(seed)
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)


from time import time as ttime


try:
    from .t2s_lightning_module import Text2SemanticLightningModule
except ImportError:
    Text2SemanticLightningModule = None


try:
    from peft import LoraConfig, get_peft_model
except ImportError:
    LoraConfig = None
    get_peft_model = None


try:
    from text import cleaned_text_to_sequence
except ImportError:
    cleaned_text_to_sequence = None

try:
    from text.cleaner import clean_text
except ImportError:
    clean_text = None


try:
    from tools.assets import css, js, top_html
except ImportError:
    css = None
    js = None
    top_html = None

try:
    from tools.i18n.i18n import I18nAuto, scan_language_list
except ImportError:
    I18nAuto = None
    scan_language_list = None

language = os.environ.get("language", "Auto")
language = sys.argv[-1] if sys.argv[-1] in scan_language_list() else language
i18n = I18nAuto(language=language)

if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"


dict_language_v1 = {
    i18n("中文"): "all_zh",
    i18n("英文"): "en",
    i18n("日文"): "all_ja",
    i18n("中英混合"): "zh",
    i18n("日英混合"): "ja",
    i18n("多语种混合"): "auto",
}
dict_language_v2 = {
    i18n("中文"): "all_zh",
    i18n("英文"): "en",
    i18n("日文"): "all_ja",
    i18n("粤语"): "all_yue",
    i18n("韩文"): "all_ko",
    i18n("中英混合"): "zh",
    i18n("日英混合"): "ja",
    i18n("粤英混合"): "yue",
    i18n("韩英混合"): "ko",
    i18n("多语种混合"): "auto",
    i18n("多语种混合(粤语)"): "auto_yue",
}
dict_language = dict_language_v1 if version == "v1" else dict_language_v2

tokenizer = AutoTokenizer.from_pretrained(bert_path)
bert_model = AutoModelForMaskedLM.from_pretrained(bert_path)
if is_half == True:
    bert_model = bert_model.half().to(device)
else:
    bert_model = bert_model.to(device)


def get_bert_feature(text: str, word2ph: list) -> torch.Tensor:
    """
    获取 BERT 特征
    
    使用预训练的 BERT 模型提取文本特征。
    
    Args:
        text: 输入文本
        word2ph: 每个词对应的音素数量列表
        
    Returns:
        BERT 特征张量
    """
    with torch.no_grad():
        inputs = tokenizer(text, return_tensors="pt")
        for i in inputs:
            inputs[i] = inputs[i].to(device)
        res = bert_model(**inputs, output_hidden_states=True)
        res = torch.cat(res["hidden_states"][-3:-2], -1)[0].cpu()[1:-1]
    assert len(word2ph) == len(text)
    phone_level_feature = []
    for i in range(len(word2ph)):
        repeat_feature = res[i].repeat(word2ph[i], 1)
        phone_level_feature.append(repeat_feature)
    phone_level_feature = torch.cat(phone_level_feature, dim=0)
    return phone_level_feature.T


class DictToAttrRecursive(dict):
    """
    递归字典转属性类
    
    将字典递归转换为支持属性访问的对象。
    """
    
    def __init__(self, input_dict: dict):
        """
        初始化
        
        Args:
            input_dict: 输入字典
        """
        super().__init__(input_dict)
        for key, value in input_dict.items():
            if isinstance(value, dict):
                value = DictToAttrRecursive(value)
            self[key] = value
            setattr(self, key, value)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(f"Attribute {item} not found")

    def __setattr__(self, key, value):
        if isinstance(value, dict):
            value = DictToAttrRecursive(value)
        super(DictToAttrRecursive, self).__setitem__(key, value)
        super().__setattr__(key, value)

    def __delattr__(self, item):
        try:
            del self[item]
        except KeyError:
            raise AttributeError(f"Attribute {item} not found")


ssl_model = cnhubert.get_model()
if is_half == True:
    ssl_model = ssl_model.half().to(device)
else:
    ssl_model = ssl_model.to(device)


try:
    from process_ckpt import get_sovits_version_from_path_fast, load_sovits_new
except ImportError:
    get_sovits_version_from_path_fast = None
    load_sovits_new = None

v3v4set = {"v3", "v4"}


def change_sovits_weights(sovits_path: str, prompt_language: str | None = None, text_language: str | None = None):
    """
    切换 SoVITS 模型权重
    
    加载指定的 SoVITS 模型并更新全局配置。
    
    Args:
        sovits_path: SoVITS 模型文件路径
        prompt_language: 提示词语种，可选
        text_language: 目标文本语种，可选
        
    Yields:
        Gradio 更新字典
    """
    if "！" in sovits_path or "!" in sovits_path:
        sovits_path = name2sovits_path[sovits_path]
    global vq_model, hps, version, model_version, dict_language, if_lora_v3
    version, model_version, if_lora_v3 = get_sovits_version_from_path_fast(sovits_path)
    is_exist = is_exist_s2gv3 if model_version == "v3" else is_exist_s2gv4
    path_sovits = path_sovits_v3 if model_version == "v3" else path_sovits_v4
    if if_lora_v3 == True and is_exist == False:
        info = path_sovits + "SoVITS %s" % model_version + i18n("底模缺失，无法加载相应 LoRA 权重")
        gr.Warning(info)
        raise FileExistsError(info)
    dict_language = dict_language_v1 if version == "v1" else dict_language_v2
    if prompt_language is not None and text_language is not None:
        if prompt_language in list(dict_language.keys()):
            prompt_text_update, prompt_language_update = (
                {"__type__": "update"},
                {"__type__": "update", "value": prompt_language},
            )
        else:
            prompt_text_update = {"__type__": "update", "value": ""}
            prompt_language_update = {"__type__": "update", "value": i18n("中文")}
        if text_language in list(dict_language.keys()):
            text_update, text_language_update = {"__type__": "update"}, {"__type__": "update", "value": text_language}
        else:
            text_update = {"__type__": "update", "value": ""}
            text_language_update = {"__type__": "update", "value": i18n("中文")}
        if model_version in v3v4set:
            visible_sample_steps = True
            visible_inp_refs = False
        else:
            visible_sample_steps = False
            visible_inp_refs = True
        yield (
            {"__type__": "update", "choices": list(dict_language.keys())},
            {"__type__": "update", "choices": list(dict_language.keys())},
            prompt_text_update,
            prompt_language_update,
            text_update,
            text_language_update,
            {
                "__type__": "update",
                "visible": visible_sample_steps,
                "value": 32 if model_version == "v3" else 8,
                "choices": [4, 8, 16, 32, 64, 128] if model_version == "v3" else [4, 8, 16, 32],
            },
            {"__type__": "update", "visible": visible_inp_refs},
            {"__type__": "update", "value": False, "interactive": True if model_version not in v3v4set else False},
            {"__type__": "update", "visible": True if model_version == "v3" else False},
            {"__type__": "update", "value": i18n("模型加载中，请等待"), "interactive": False},
        )

    dict_s2 = load_sovits_new(sovits_path)
    hps = dict_s2["config"]
    hps = DictToAttrRecursive(hps)
    hps.model.semantic_frame_rate = "25hz"
    if "enc_p.text_embedding.weight" not in dict_s2["weight"]:
        hps.model.version = "v2"
    elif dict_s2["weight"]["enc_p.text_embedding.weight"].shape[0] == 322:
        hps.model.version = "v1"
    else:
        hps.model.version = "v2"
    version = hps.model.version
    if model_version not in v3v4set:
        if "Pro" not in model_version:
            model_version = version
        else:
            hps.model.version = model_version
        vq_model = SynthesizerTrn(
            hps.data.filter_length // 2 + 1,
            hps.train.segment_size // hps.data.hop_length,
            n_speakers=hps.data.n_speakers,
            **hps.model,
        )
    else:
        hps.model.version = model_version
        vq_model = SynthesizerTrnV3(
            hps.data.filter_length // 2 + 1,
            hps.train.segment_size // hps.data.hop_length,
            n_speakers=hps.data.n_speakers,
            **hps.model,
        )
    if "pretrained" not in sovits_path:
        try:
            del vq_model.enc_q
        except AttributeError:
            pass
    if is_half == True:
        vq_model = vq_model.half().to(device)
    else:
        vq_model = vq_model.to(device)
    vq_model.eval()
    if if_lora_v3 == False:
        vq_model.load_state_dict(dict_s2["weight"], strict=False)
        logger.debug(f"加载 SoVITS 权重: {sovits_path}")
    else:
        path_sovits = path_sovits_v3 if model_version == "v3" else path_sovits_v4
        vq_model.load_state_dict(load_sovits_new(path_sovits)["weight"], strict=False)
        lora_rank = dict_s2["lora_rank"]
        lora_config = LoraConfig(
            target_modules=["to_k", "to_q", "to_v", "to_out.0"],
            r=lora_rank,
            lora_alpha=lora_rank,
            init_lora_weights=True,
        )
        vq_model.cfm = get_peft_model(vq_model.cfm, lora_config)
        vq_model.load_state_dict(dict_s2["weight"], strict=False)
        vq_model.cfm = vq_model.cfm.merge_and_unload()
        vq_model.eval()
        logger.debug(f"加载 SoVITS LoRA 权重: {sovits_path}, rank: {lora_rank}")

    yield (
        {"__type__": "update", "choices": list(dict_language.keys())},
        {"__type__": "update", "choices": list(dict_language.keys())},
        prompt_text_update,
        prompt_language_update,
        text_update,
        text_language_update,
        {
            "__type__": "update",
            "visible": visible_sample_steps,
            "value": 32 if model_version == "v3" else 8,
            "choices": [4, 8, 16, 32, 64, 128] if model_version == "v3" else [4, 8, 16, 32],
        },
        {"__type__": "update", "visible": visible_inp_refs},
        {"__type__": "update", "value": False, "interactive": True if model_version not in v3v4set else False},
        {"__type__": "update", "visible": True if model_version == "v3" else False},
        {"__type__": "update", "value": i18n("合成语音"), "interactive": True},
    )
    data = json.loads(weight_json_path.read_text(encoding="utf-8"))
    data["SoVITS"][version] = sovits_path
    weight_json_path.write_text(json.dumps(data), encoding="utf-8")


try:
    next(change_sovits_weights(sovits_path))
except StopIteration:
    pass
except Exception as e:
    logger.debug(f"初始化SoVITS权重失败: {e}")


def change_gpt_weights(gpt_path: str) -> None:
    """
    切换 GPT 模型权重
    
    加载指定的 GPT 模型并更新全局配置。
    
    Args:
        gpt_path: GPT 模型文件路径
    """
    if "！" in gpt_path or "!" in gpt_path:
        gpt_path = name2gpt_path[gpt_path]
    global hz, max_sec, t2s_model, config
    hz = 50
    dict_s1 = torch.load(gpt_path, map_location="cpu", weights_only=False)
    config = dict_s1["config"]
    max_sec = config["data"]["max_sec"]
    t2s_model = Text2SemanticLightningModule(config, "****", is_train=False)
    t2s_model.load_state_dict(dict_s1["weight"])
    if is_half == True:
        t2s_model = t2s_model.half()
    t2s_model = t2s_model.to(device)
    t2s_model.eval()
    data = json.loads(weight_json_path.read_text(encoding="utf-8"))
    data["GPT"][version] = gpt_path
    weight_json_path.write_text(json.dumps(data), encoding="utf-8")
    logger.debug(f"加载 GPT 权重: {gpt_path}")


change_gpt_weights(gpt_path)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import torch

now_dir = Path.cwd()


def clean_hifigan_model() -> None:
    """清理 HiFi-GAN 模型，释放显存"""
    global hifigan_model
    if hifigan_model:
        hifigan_model = hifigan_model.cpu()
        hifigan_model = None
        try:
            torch.cuda.empty_cache()
        except RuntimeError as e:
            logger.debug(f"清理CUDA缓存失败: {e}")


def clean_bigvgan_model() -> None:
    """清理 BigVGAN 模型，释放显存"""
    global bigvgan_model
    if bigvgan_model:
        bigvgan_model = bigvgan_model.cpu()
        bigvgan_model = None
        try:
            torch.cuda.empty_cache()
        except RuntimeError as e:
            logger.debug(f"清理CUDA缓存失败: {e}")


def clean_sv_cn_model() -> None:
    """清理说话人验证模型，释放显存"""
    global sv_cn_model
    if sv_cn_model:
        sv_cn_model.embedding_model = sv_cn_model.embedding_model.cpu()
        sv_cn_model = None
        try:
            torch.cuda.empty_cache()
        except RuntimeError as e:
            logger.debug(f"清理CUDA缓存失败: {e}")


def init_bigvgan() -> None:
    """初始化 BigVGAN 声码器（用于 v3 模型）"""
    global bigvgan_model, hifigan_model, sv_cn_model
    from BigVGAN import bigvgan

    bigvgan_path = now_dir / "GPT_SoVITS" / "pretrained_models" / "models--nvidia--bigvgan_v2_24khz_100band_256x"
    bigvgan_model = bigvgan.BigVGAN.from_pretrained(
        str(bigvgan_path),
        use_cuda_kernel=False,
    )
    bigvgan_model.remove_weight_norm()
    bigvgan_model = bigvgan_model.eval()
    clean_hifigan_model()
    clean_sv_cn_model()
    if is_half == True:
        bigvgan_model = bigvgan_model.half().to(device)
    else:
        bigvgan_model = bigvgan_model.to(device)
    logger.debug("BigVGAN 声码器初始化完成")


def init_hifigan() -> None:
    """初始化 HiFi-GAN 声码器（用于 v4 模型）"""
    global hifigan_model, bigvgan_model, sv_cn_model
    hifigan_model = Generator(
        initial_channel=100,
        resblock="1",
        resblock_kernel_sizes=[3, 7, 11],
        resblock_dilation_sizes=[[1, 3, 5], [1, 3, 5], [1, 3, 5]],
        upsample_rates=[10, 6, 2, 2, 2],
        upsample_initial_channel=512,
        upsample_kernel_sizes=[20, 12, 4, 4, 4],
        gin_channels=0,
        is_bias=True,
    )
    hifigan_model.eval()
    hifigan_model.remove_weight_norm()
    vocoder_path = now_dir / "GPT_SoVITS" / "pretrained_models" / "gsv-v4-pretrained" / "vocoder.pth"
    state_dict_g = torch.load(
        str(vocoder_path),
        map_location="cpu",
        weights_only=False,
    )
    hifigan_model.load_state_dict(state_dict_g)
    clean_bigvgan_model()
    clean_sv_cn_model()
    if is_half == True:
        hifigan_model = hifigan_model.half().to(device)
    else:
        hifigan_model = hifigan_model.to(device)
    logger.debug("HiFi-GAN 声码器初始化完成")


try:
    from sv import SV
except ImportError:
    SV = None


def init_sv_cn() -> None:
    """初始化说话人验证模型（用于 v2Pro/v2ProPlus 模型）"""
    global hifigan_model, bigvgan_model, sv_cn_model
    sv_cn_model = SV(device, is_half)
    clean_bigvgan_model()
    clean_hifigan_model()
    logger.debug("说话人验证模型初始化完成")


bigvgan_model = hifigan_model = sv_cn_model = None
if model_version == "v3":
    init_bigvgan()
if model_version == "v4":
    init_hifigan()
if model_version in {"v2Pro", "v2ProPlus"}:
    init_sv_cn()

resample_transform_dict = {}


def resample(audio_tensor: torch.Tensor, sr0: int, sr1: int, device: str) -> torch.Tensor:
    """
    音频重采样
    
    将音频从 sr0 采样率转换为 sr1 采样率。
    
    Args:
        audio_tensor: 音频张量
        sr0: 原始采样率
        sr1: 目标采样率
        device: 计算设备
        
    Returns:
        重采样后的音频张量
    """
    global resample_transform_dict
    key = "%s-%s-%s" % (sr0, sr1, str(device))
    if key not in resample_transform_dict:
        resample_transform_dict[key] = torchaudio.transforms.Resample(sr0, sr1).to(device)
    return resample_transform_dict[key](audio_tensor)


def get_spepc(hps, filename: str, dtype, device: str, is_v2pro: bool = False) -> tuple:
    """
    获取音频频谱特征
    
    从音频文件中提取频谱特征。
    
    Args:
        hps: 超参数配置
        filename: 音频文件路径
        dtype: 数据类型
        device: 计算设备
        is_v2pro: 是否为 v2Pro 模型
        
    Returns:
        元组 (频谱特征, 音频张量)
    """
    sr1 = int(hps.data.sampling_rate)
    audio, sr0 = torchaudio.load(filename)
    if sr0 != sr1:
        audio = audio.to(device)
        if audio.shape[0] == 2:
            audio = audio.mean(0).unsqueeze(0)
        audio = resample(audio, sr0, sr1, device)
    else:
        audio = audio.to(device)
        if audio.shape[0] == 2:
            audio = audio.mean(0).unsqueeze(0)

    maxx = audio.abs().max()
    if maxx > 1:
        audio /= min(2, maxx)
    spec = spectrogram_torch(
        audio,
        hps.data.filter_length,
        hps.data.sampling_rate,
        hps.data.hop_length,
        hps.data.win_length,
        center=False,
    )
    spec = spec.to(dtype)
    if is_v2pro == True:
        audio = resample(audio, sr1, 16000, device).to(dtype)
    return spec, audio


def clean_text_inf(text: str, language: str, version: str) -> tuple:
    """
    文本清洗和音素转换
    
    将文本转换为音素序列。
    
    Args:
        text: 输入文本
        language: 语言代码
        version: 模型版本
        
    Returns:
        元组 (音素列表, 词到音素映射, 归一化文本)
    """
    language = language.replace("all_", "")
    phones, word2ph, norm_text = clean_text(text, language, version)
    phones = cleaned_text_to_sequence(phones, version)
    return phones, word2ph, norm_text


dtype = torch.float16 if is_half == True else torch.float32


def get_bert_inf(phones: list, word2ph: list, norm_text: str, language: str) -> torch.Tensor:
    """
    获取 BERT 推理特征
    
    根据音素序列获取 BERT 特征。
    
    Args:
        phones: 音素列表
        word2ph: 词到音素映射
        norm_text: 归一化文本
        language: 语言代码
        
    Returns:
        BERT 特征张量
    """
    language = language.replace("all_", "")
    if language == "zh":
        bert = get_bert_feature(norm_text, word2ph).to(device)
    else:
        bert = torch.zeros(
            (1024, len(phones)),
            dtype=torch.float16 if is_half == True else torch.float32,
        ).to(device)

    return bert


splits = {
    "，",
    "。",
    "？",
    "！",
    ",",
    ".",
    "?",
    "!",
    "~",
    ":",
    "：",
    "—",
    "…",
}


def get_first(text: str) -> str:
    """
    获取第一个句子
    
    提取文本中第一个完整句子。
    
    Args:
        text: 输入文本
        
    Returns:
        第一个句子
    """
    pattern = "[" + "".join(re.escape(sep) for sep in splits) + "]"
    text = re.split(pattern, text)[0].strip()
    return text


try:
    from text import chinese
except ImportError:
    chinese = None


def get_phones_and_bert(text: str, language: str, version: str, final: bool = False) -> tuple:
    """
    获取音素和 BERT 特征
    
    处理文本，提取音素序列和对应的 BERT 特征。
    
    Args:
        text: 输入文本
        language: 语言代码
        version: 模型版本
        final: 是否为最终处理
        
    Returns:
        元组 (音素列表, BERT 特征, 归一化文本)
    """
    text = re.sub(r' {2,}', ' ', text)
    textlist = []
    langlist = []
    if language == "all_zh":
        for tmp in LangSegmenter.getTexts(text,"zh"):
            langlist.append(tmp["lang"])
            textlist.append(tmp["text"])
    elif language == "all_yue":
        for tmp in LangSegmenter.getTexts(text,"zh"):
            if tmp["lang"] == "zh":
                tmp["lang"] = "yue"
            langlist.append(tmp["lang"])
            textlist.append(tmp["text"])
    elif language == "all_ja":
        for tmp in LangSegmenter.getTexts(text,"ja"):
            langlist.append(tmp["lang"])
            textlist.append(tmp["text"])
    elif language == "all_ko":
        for tmp in LangSegmenter.getTexts(text,"ko"):
            langlist.append(tmp["lang"])
            textlist.append(tmp["text"])
    elif language == "en":
        langlist.append("en")
        textlist.append(text)
    elif language == "auto":
        for tmp in LangSegmenter.getTexts(text):
            langlist.append(tmp["lang"])
            textlist.append(tmp["text"])
    elif language == "auto_yue":
        for tmp in LangSegmenter.getTexts(text):
            if tmp["lang"] == "zh":
                tmp["lang"] = "yue"
            langlist.append(tmp["lang"])
            textlist.append(tmp["text"])
    else:
        for tmp in LangSegmenter.getTexts(text):
            if langlist:
                if (tmp["lang"] == "en" and langlist[-1] == "en") or (tmp["lang"] != "en" and langlist[-1] != "en"):
                    textlist[-1] += tmp["text"]
                    continue
            if tmp["lang"] == "en":
                langlist.append(tmp["lang"])
            else:
                langlist.append(language)
            textlist.append(tmp["text"])
    phones_list = []
    bert_list = []
    norm_text_list = []
    for i in range(len(textlist)):
        lang = langlist[i]
        phones, word2ph, norm_text = clean_text_inf(textlist[i], lang, version)
        bert = get_bert_inf(phones, word2ph, norm_text, lang)
        phones_list.append(phones)
        norm_text_list.append(norm_text)
        bert_list.append(bert)
    bert = torch.cat(bert_list, dim=1)
    phones = sum(phones_list, [])
    norm_text = "".join(norm_text_list)

    if not final and len(phones) < 6:
        return get_phones_and_bert("." + text, language, version, final=True)

    return phones, bert.to(dtype), norm_text


try:
    from module.mel_processing import mel_spectrogram_torch, spectrogram_torch
except ImportError:
    mel_spectrogram_torch = None
    spectrogram_torch = None

spec_min = -12
spec_max = 2


def norm_spec(x: torch.Tensor) -> torch.Tensor:
    """归一化频谱"""
    return (x - spec_min) / (spec_max - spec_min) * 2 - 1


def denorm_spec(x: torch.Tensor) -> torch.Tensor:
    """反归一化频谱"""
    return (x + 1) / 2 * (spec_max - spec_min) + spec_min


mel_fn = lambda x: mel_spectrogram_torch(
    x,
    **{
        "n_fft": 1024,
        "win_size": 1024,
        "hop_size": 256,
        "num_mels": 100,
        "sampling_rate": 24000,
        "fmin": 0,
        "fmax": None,
        "center": False,
    },
)
mel_fn_v4 = lambda x: mel_spectrogram_torch(
    x,
    **{
        "n_fft": 1280,
        "win_size": 1280,
        "hop_size": 320,
        "num_mels": 100,
        "sampling_rate": 32000,
        "fmin": 0,
        "fmax": None,
        "center": False,
    },
)


def merge_short_text_in_array(texts: list, threshold: int) -> list:
    """
    合并短文本
    
    将短于阈值的文本合并到前一个文本中。
    
    Args:
        texts: 文本列表
        threshold: 长度阈值
        
    Returns:
        合并后的文本列表
    """
    if (len(texts)) < 2:
        return texts
    result = []
    text = ""
    for ele in texts:
        text += ele
        if len(text) >= threshold:
            result.append(text)
            text = ""
    if len(text) > 0:
        if len(result) == 0:
            result.append(text)
        else:
            result[len(result) - 1] += text
    return result


sr_model = None


def audio_sr(audio: torch.Tensor, sr: int) -> tuple:
    """
    音频超分辨率
    
    使用超分辨率模型提升音频质量。
    
    Args:
        audio: 音频张量
        sr: 采样率
        
    Returns:
        元组 (超分后的音频, 采样率)
    """
    global sr_model
    if sr_model == None:
        from tools.audio_sr import AP_BWE

        try:
            sr_model = AP_BWE(device, DictToAttrRecursive)
        except FileNotFoundError:
            gr.Warning(i18n("你没有下载超分模型的参数，因此不进行超分。如想超分请先参照教程把文件下载好"))
            return audio.cpu().detach().numpy(), sr
    return sr_model(audio, sr)


cache = {}


def get_tts_wav(
    ref_wav_path: str,
    prompt_text: str,
    prompt_language: str,
    text: str,
    text_language: str,
    how_to_cut: str = i18n("不切"),
    top_k: int = 20,
    top_p: float = 0.6,
    temperature: float = 0.6,
    ref_free: bool = False,
    speed: float = 1,
    if_freeze: bool = False,
    inp_refs = None,
    sample_steps: int = 8,
    if_sr: bool = False,
    pause_second: float = 0.3,
):
    """
    文本转语音合成主函数
    
    使用 GPT-SoVITS 模型将文本转换为语音。
    
    Args:
        ref_wav_path: 参考音频路径
        prompt_text: 参考音频对应的文本
        prompt_language: 参考文本语种
        text: 要合成的文本
        text_language: 目标文本语种
        how_to_cut: 文本切分方式
        top_k: Top-K 采样参数
        top_p: Top-P 采样参数
        temperature: 温度参数
        ref_free: 是否启用无参考文本模式
        speed: 语速
        if_freeze: 是否冻结上次合成结果
        inp_refs: 额外参考音频列表
        sample_steps: 采样步数（v3/v4）
        if_sr: 是否启用超分辨率
        pause_second: 句间停顿秒数
        
    Yields:
        元组 (采样率, 音频数据)
    """
    global cache
    if ref_wav_path:
        pass
    else:
        gr.Warning(i18n("请上传参考音频"))
    if text:
        pass
    else:
        gr.Warning(i18n("请填入推理文本"))
    t = []
    if prompt_text is None or len(prompt_text) == 0:
        ref_free = True
    if model_version in v3v4set:
        ref_free = False
    else:
        if_sr = False
    if model_version not in {"v3", "v4", "v2Pro", "v2ProPlus"}:
        clean_bigvgan_model()
        clean_hifigan_model()
        clean_sv_cn_model()
    t0 = ttime()
    prompt_language = dict_language[prompt_language]
    text_language = dict_language[text_language]

    if not ref_free:
        prompt_text = prompt_text.strip("\n")
        if prompt_text[-1] not in splits:
            prompt_text += "。" if prompt_language != "en" else "."
    text = text.strip("\n")

    zero_wav = np.zeros(
        int(hps.data.sampling_rate * pause_second),
        dtype=np.float16 if is_half == True else np.float32,
    )
    zero_wav_torch = torch.from_numpy(zero_wav)
    if is_half == True:
        zero_wav_torch = zero_wav_torch.half().to(device)
    else:
        zero_wav_torch = zero_wav_torch.to(device)
    if not ref_free:
        with torch.no_grad():
            wav16k, sr = librosa.load(ref_wav_path, sr=16000)
            if wav16k.shape[0] > 160000 or wav16k.shape[0] < 48000:
                gr.Warning(i18n("参考音频在3~10秒范围外，请更换！"))
                raise OSError(i18n("参考音频在3~10秒范围外，请更换！"))
            wav16k = torch.from_numpy(wav16k)
            if is_half == True:
                wav16k = wav16k.half().to(device)
            else:
                wav16k = wav16k.to(device)
            wav16k = torch.cat([wav16k, zero_wav_torch])
            ssl_content = ssl_model.model(wav16k.unsqueeze(0))["last_hidden_state"].transpose(1, 2)
            codes = vq_model.extract_latent(ssl_content)
            prompt_semantic = codes[0, 0]
            prompt = prompt_semantic.unsqueeze(0).to(device)

    t1 = ttime()
    t.append(t1 - t0)

    if how_to_cut == i18n("凑四句一切"):
        text = cut1(text)
    elif how_to_cut == i18n("凑50字一切"):
        text = cut2(text)
    elif how_to_cut == i18n("按中文句号。切"):
        text = cut3(text)
    elif how_to_cut == i18n("按英文句号.切"):
        text = cut4(text)
    elif how_to_cut == i18n("按标点符号切"):
        text = cut5(text)
    while "\n\n" in text:
        text = text.replace("\n\n", "\n")
    texts = text.split("\n")
    texts = process_text(texts)
    texts = merge_short_text_in_array(texts, 5)
    audio_opt = []
    if not ref_free:
        phones1, bert1, norm_text1 = get_phones_and_bert(prompt_text, prompt_language, version)

    for i_text, text in enumerate(texts):
        if len(text.strip()) == 0:
            continue
        if text[-1] not in splits:
            text += "。" if text_language != "en" else "."
        phones2, bert2, norm_text2 = get_phones_and_bert(text, text_language, version)
        if not ref_free:
            bert = torch.cat([bert1, bert2], 1)
            all_phoneme_ids = torch.LongTensor(phones1 + phones2).to(device).unsqueeze(0)
        else:
            bert = bert2
            all_phoneme_ids = torch.LongTensor(phones2).to(device).unsqueeze(0)

        bert = bert.to(device).unsqueeze(0)
        all_phoneme_len = torch.tensor([all_phoneme_ids.shape[-1]]).to(device)

        t2 = ttime()
        if i_text in cache and if_freeze == True:
            pred_semantic = cache[i_text]
        else:
            with torch.no_grad():
                pred_semantic, idx = t2s_model.model.infer_panel(
                    all_phoneme_ids,
                    all_phoneme_len,
                    None if ref_free else prompt,
                    bert,
                    top_k=top_k,
                    top_p=top_p,
                    temperature=temperature,
                    early_stop_num=hz * max_sec,
                )
                pred_semantic = pred_semantic[:, -idx:].unsqueeze(0)
                cache[i_text] = pred_semantic
        t3 = ttime()
        is_v2pro = model_version in {"v2Pro", "v2ProPlus"}
        if model_version not in v3v4set:
            refers = []
            if is_v2pro:
                sv_emb = []
                if sv_cn_model == None:
                    init_sv_cn()
            if inp_refs:
                for path in inp_refs:
                    try:
                        refer, audio_tensor = get_spepc(hps, path.name, dtype, device, is_v2pro)
                        refers.append(refer)
                        if is_v2pro:
                            sv_emb.append(sv_cn_model.compute_embedding3(audio_tensor))
                    except Exception as e:
                        logger.warning(f"处理参考音频失败 {path}: {e}")
                        traceback.print_exc()
            if len(refers) == 0:
                refers, audio_tensor = get_spepc(hps, ref_wav_path, dtype, device, is_v2pro)
                refers = [refers]
                if is_v2pro:
                    sv_emb = [sv_cn_model.compute_embedding3(audio_tensor)]
            if is_v2pro:
                audio = vq_model.decode(
                    pred_semantic, torch.LongTensor(phones2).to(device).unsqueeze(0), refers, speed=speed, sv_emb=sv_emb
                )[0][0]
            else:
                audio = vq_model.decode(
                    pred_semantic, torch.LongTensor(phones2).to(device).unsqueeze(0), refers, speed=speed
                )[0][0]
        else:
            refer, audio_tensor = get_spepc(hps, ref_wav_path, dtype, device)
            phoneme_ids0 = torch.LongTensor(phones1).to(device).unsqueeze(0)
            phoneme_ids1 = torch.LongTensor(phones2).to(device).unsqueeze(0)
            fea_ref, ge = vq_model.decode_encp(prompt.unsqueeze(0), phoneme_ids0, refer)
            ref_audio, sr = torchaudio.load(ref_wav_path)
            ref_audio = ref_audio.to(device).float()
            if ref_audio.shape[0] == 2:
                ref_audio = ref_audio.mean(0).unsqueeze(0)
            tgt_sr = 24000 if model_version == "v3" else 32000
            if sr != tgt_sr:
                ref_audio = resample(ref_audio, sr, tgt_sr, device)
            mel2 = mel_fn(ref_audio) if model_version == "v3" else mel_fn_v4(ref_audio)
            mel2 = norm_spec(mel2)
            T_min = min(mel2.shape[2], fea_ref.shape[2])
            mel2 = mel2[:, :, :T_min]
            fea_ref = fea_ref[:, :, :T_min]
            Tref = 468 if model_version == "v3" else 500
            Tchunk = 934 if model_version == "v3" else 1000
            if T_min > Tref:
                mel2 = mel2[:, :, -Tref:]
                fea_ref = fea_ref[:, :, -Tref:]
                T_min = Tref
            chunk_len = Tchunk - T_min
            mel2 = mel2.to(dtype)
            fea_todo, ge = vq_model.decode_encp(pred_semantic, phoneme_ids1, refer, ge, speed)
            cfm_resss = []
            idx = 0
            while 1:
                fea_todo_chunk = fea_todo[:, :, idx : idx + chunk_len]
                if fea_todo_chunk.shape[-1] == 0:
                    break
                idx += chunk_len
                fea = torch.cat([fea_ref, fea_todo_chunk], 2).transpose(2, 1)
                cfm_res = vq_model.cfm.inference(
                    fea, torch.LongTensor([fea.size(1)]).to(fea.device), mel2, sample_steps, inference_cfg_rate=0
                )
                cfm_res = cfm_res[:, :, mel2.shape[2] :]
                mel2 = cfm_res[:, :, -T_min:]
                fea_ref = fea_todo_chunk[:, :, -T_min:]
                cfm_resss.append(cfm_res)
            cfm_res = torch.cat(cfm_resss, 2)
            cfm_res = denorm_spec(cfm_res)
            if model_version == "v3":
                if bigvgan_model == None:
                    init_bigvgan()
            else:
                if hifigan_model == None:
                    init_hifigan()
            vocoder_model = bigvgan_model if model_version == "v3" else hifigan_model
            with torch.inference_mode():
                wav_gen = vocoder_model(cfm_res)
                audio = wav_gen[0][0]
        max_audio = torch.abs(audio).max()
        if max_audio > 1:
            audio = audio / max_audio
        audio_opt.append(audio)
        audio_opt.append(zero_wav_torch)
        t4 = ttime()
        t.extend([t2 - t1, t3 - t2, t4 - t3])
        t1 = ttime()
    audio_opt = torch.cat(audio_opt, 0)
    if model_version in {"v1", "v2", "v2Pro", "v2ProPlus"}:
        opt_sr = 32000
    elif model_version == "v3":
        opt_sr = 24000
    else:
        opt_sr = 48000
    if if_sr == True and opt_sr == 24000:
        audio_opt, opt_sr = audio_sr(audio_opt.unsqueeze(0), opt_sr)
        max_audio = np.abs(audio_opt).max()
        if max_audio > 1:
            audio_opt /= max_audio
    else:
        audio_opt = audio_opt.cpu().detach().numpy()
    yield opt_sr, (audio_opt * 32767).astype(np.int16)


def split(todo_text: str) -> list:
    """
    按标点分割文本
    
    Args:
        todo_text: 输入文本
        
    Returns:
        分割后的文本片段列表
    """
    todo_text = todo_text.replace("……", "。").replace("——", "，")
    if todo_text[-1] not in splits:
        todo_text += "。"
    i_split_head = i_split_tail = 0
    len_text = len(todo_text)
    todo_texts = []
    while 1:
        if i_split_head >= len_text:
            break
        if todo_text[i_split_head] in splits:
            i_split_head += 1
            todo_texts.append(todo_text[i_split_tail:i_split_head])
            i_split_tail = i_split_head
        else:
            i_split_head += 1
    return todo_texts


def cut1(inp: str) -> str:
    """
    凑四句一切
    
    按四个句子一组切分文本。
    
    Args:
        inp: 输入文本
        
    Returns:
        切分后的文本
    """
    inp = inp.strip("\n")
    inps = split(inp)
    split_idx = list(range(0, len(inps), 4))
    split_idx[-1] = None
    if len(split_idx) > 1:
        opts = []
        for idx in range(len(split_idx) - 1):
            opts.append("".join(inps[split_idx[idx] : split_idx[idx + 1]]))
    else:
        opts = [inp]
    opts = [item for item in opts if not set(item).issubset(punctuation)]
    return "\n".join(opts)


def cut2(inp: str) -> str:
    """
    凑50字一切
    
    按每段约50字切分文本。
    
    Args:
        inp: 输入文本
        
    Returns:
        切分后的文本
    """
    inp = inp.strip("\n")
    inps = split(inp)
    if len(inps) < 2:
        return inp
    opts = []
    summ = 0
    tmp_str = ""
    for i in range(len(inps)):
        summ += len(inps[i])
        tmp_str += inps[i]
        if summ > 50:
            summ = 0
            opts.append(tmp_str)
            tmp_str = ""
    if tmp_str != "":
        opts.append(tmp_str)
    if len(opts) > 1 and len(opts[-1]) < 50:
        opts[-2] = opts[-2] + opts[-1]
        opts = opts[:-1]
    opts = [item for item in opts if not set(item).issubset(punctuation)]
    return "\n".join(opts)


def cut3(inp: str) -> str:
    """
    按中文句号切
    
    按中文句号切分文本。
    
    Args:
        inp: 输入文本
        
    Returns:
        切分后的文本
    """
    inp = inp.strip("\n")
    opts = ["%s" % item for item in inp.strip("。").split("。")]
    opts = [item for item in opts if not set(item).issubset(punctuation)]
    return "\n".join(opts)


def cut4(inp: str) -> str:
    """
    按英文句号切
    
    按英文句号切分文本。
    
    Args:
        inp: 输入文本
        
    Returns:
        切分后的文本
    """
    inp = inp.strip("\n")
    opts = re.split(r"(?<!\d)\.(?!\d)", inp.strip("."))
    opts = [item for item in opts if not set(item).issubset(punctuation)]
    return "\n".join(opts)


def cut5(inp: str) -> str:
    """
    按标点符号切
    
    按任意标点符号切分文本。
    
    Args:
        inp: 输入文本
        
    Returns:
        切分后的文本
    """
    inp = inp.strip("\n")
    punds = {",", ".", ";", "?", "!", "、", "，", "。", "？", "！", ";", "：", "…"}
    mergeitems = []
    items = []

    for i, char in enumerate(inp):
        if char in punds:
            if char == "." and i > 0 and i < len(inp) - 1 and inp[i - 1].isdigit() and inp[i + 1].isdigit():
                items.append(char)
            else:
                items.append(char)
                mergeitems.append("".join(items))
                items = []
        else:
            items.append(char)

    if items:
        mergeitems.append("".join(items))

    opt = [item for item in mergeitems if not set(item).issubset(punds)]
    return "\n".join(opt)


def custom_sort_key(s: str) -> list:
    """
    自定义排序键
    
    用于按数字顺序排序字符串。
    
    Args:
        s: 输入字符串
        
    Returns:
        排序键列表
    """
    parts = re.split("(\d+)", s)
    parts = [int(part) if part.isdigit() else part for part in parts]
    return parts


def process_text(texts: list) -> list:
    """
    处理文本列表
    
    过滤空文本。
    
    Args:
        texts: 文本列表
        
    Returns:
        处理后的文本列表
    """
    _text = []
    if all(text in [None, " ", "\n", ""] for text in texts):
        raise ValueError(i18n("请输入有效文本"))
    for text in texts:
        if text in [None, " ", ""]:
            pass
        else:
            _text.append(text)
    return _text


def html_center(text: str, label: str = "p") -> str:
    """
    生成居中 HTML
    
    Args:
        text: 文本内容
        label: HTML 标签
        
    Returns:
        HTML 字符串
    """
    return f"""<div style="text-align: center; margin: 100; padding: 50;">
                <{label} style="margin: 0; padding: 0;">{text}</{label}>
                </div>"""


def html_left(text: str, label: str = "p") -> str:
    """
    生成左对齐 HTML
    
    Args:
        text: 文本内容
        label: HTML 标签
        
    Returns:
        HTML 字符串
    """
    return f"""<div style="text-align: left; margin: 0; padding: 0;">
                <{label} style="margin: 0; padding: 0;">{text}</{label}>
                </div>"""


with gr.Blocks(title="GPT-SoVITS WebUI", analytics_enabled=False, js=js, css=css) as app:
    gr.HTML(
        top_html.format(
            i18n("本软件以MIT协议开源, 作者不对软件具备任何控制力, 使用软件者、传播软件导出的声音者自负全责.")
            + i18n("如不认可该条款, 则不能使用或引用软件包内任何代码和文件. 详见根目录LICENSE.")
        ),
        elem_classes="markdown",
    )
    with gr.Group():
        gr.Markdown(html_center(i18n("模型切换"), "h3"))
        with gr.Row():
            GPT_dropdown = gr.Dropdown(
                label=i18n("GPT模型列表"),
                choices=sorted(GPT_names, key=custom_sort_key),
                value=gpt_path,
                interactive=True,
                scale=14,
            )
            SoVITS_dropdown = gr.Dropdown(
                label=i18n("SoVITS模型列表"),
                choices=sorted(SoVITS_names, key=custom_sort_key),
                value=sovits_path,
                interactive=True,
                scale=14,
            )
            refresh_button = gr.Button(i18n("刷新模型路径"), variant="primary", scale=14)
            refresh_button.click(fn=change_choices, inputs=[], outputs=[SoVITS_dropdown, GPT_dropdown])
        gr.Markdown(html_center(i18n("*请上传并填写参考信息"), "h3"))
        with gr.Row():
            inp_ref = gr.Audio(label=i18n("请上传3~10秒内参考音频，超过会报错！"), type="filepath", scale=13)
            with gr.Column(scale=13):
                ref_text_free = gr.Checkbox(
                    label=i18n("开启无参考文本模式。不填参考文本亦相当于开启。")
                    + i18n("v3暂不支持该模式，使用了会报错。"),
                    value=False,
                    interactive=True if model_version not in v3v4set else False,
                    show_label=True,
                    scale=1,
                )
                gr.Markdown(
                    html_left(
                        i18n("使用无参考文本模式时建议使用微调的GPT")
                        + "<br>"
                        + i18n("听不清参考音频说的啥(不晓得写啥)可以开。开启后无视填写的参考文本。")
                    )
                )
                prompt_text = gr.Textbox(label=i18n("参考音频的文本"), value="", lines=5, max_lines=5, scale=1)
            with gr.Column(scale=14):
                prompt_language = gr.Dropdown(
                    label=i18n("参考音频的语种"),
                    choices=list(dict_language.keys()),
                    value=i18n("中文"),
                )
                inp_refs = (
                    gr.File(
                        label=i18n(
                            "可选项：通过拖拽多个文件上传多个参考音频（建议同性），平均融合他们的音色。如不填写此项，音色由左侧单个参考音频控制。如是微调模型，建议参考音频全部在微调训练集音色内，底模不用管。"
                        ),
                        file_count="multiple",
                    )
                    if model_version not in v3v4set
                    else gr.File(
                        label=i18n(
                            "可选项：通过拖拽多个文件上传多个参考音频（建议同性），平均融合他们的音色。如不填写此项，音色由左侧单个参考音频控制。如是微调模型，建议参考音频全部在微调训练集音色内，底模不用管。"
                        ),
                        file_count="multiple",
                        visible=False,
                    )
                )
                sample_steps = (
                    gr.Radio(
                        label=i18n("采样步数,如果觉得电,提高试试,如果觉得慢,降低试试"),
                        value=32 if model_version == "v3" else 8,
                        choices=[4, 8, 16, 32, 64, 128] if model_version == "v3" else [4, 8, 16, 32],
                        visible=True,
                    )
                    if model_version in v3v4set
                    else gr.Radio(
                        label=i18n("采样步数,如果觉得电,提高试试,如果觉得慢,降低试试"),
                        choices=[4, 8, 16, 32, 64, 128] if model_version == "v3" else [4, 8, 16, 32],
                        visible=False,
                        value=32 if model_version == "v3" else 8,
                    )
                )
                if_sr_Checkbox = gr.Checkbox(
                    label=i18n("v3输出如果觉得闷可以试试开超分"),
                    value=False,
                    interactive=True,
                    show_label=True,
                    visible=False if model_version != "v3" else True,
                )
        gr.Markdown(html_center(i18n("*请填写需要合成的目标文本和语种模式"), "h3"))
        with gr.Row():
            with gr.Column(scale=13):
                text = gr.Textbox(label=i18n("需要合成的文本"), value="", lines=26, max_lines=26)
            with gr.Column(scale=7):
                text_language = gr.Dropdown(
                    label=i18n("需要合成的语种") + i18n(".限制范围越小判别效果越好。"),
                    choices=list(dict_language.keys()),
                    value=i18n("中文"),
                    scale=1,
                )
                how_to_cut = gr.Dropdown(
                    label=i18n("怎么切"),
                    choices=[
                        i18n("不切"),
                        i18n("凑四句一切"),
                        i18n("凑50字一切"),
                        i18n("按中文句号。切"),
                        i18n("按英文句号.切"),
                        i18n("按标点符号切"),
                    ],
                    value=i18n("凑四句一切"),
                    interactive=True,
                    scale=1,
                )
                gr.Markdown(value=html_center(i18n("语速调整，高为更快")))
                if_freeze = gr.Checkbox(
                    label=i18n("是否直接对上次合成结果调整语速和音色。防止随机性。"),
                    value=False,
                    interactive=True,
                    show_label=True,
                    scale=1,
                )
                with gr.Row():
                    speed = gr.Slider(
                        minimum=0.6, maximum=1.65, step=0.05, label=i18n("语速"), value=1, interactive=True, scale=1
                    )
                    pause_second_slider = gr.Slider(
                        minimum=0.1,
                        maximum=0.5,
                        step=0.01,
                        label=i18n("句间停顿秒数"),
                        value=0.3,
                        interactive=True,
                        scale=1,
                    )
                gr.Markdown(html_center(i18n("GPT采样参数(无参考文本时不要太低。不懂就用默认)：")))
                top_k = gr.Slider(
                    minimum=1, maximum=100, step=1, label=i18n("top_k"), value=15, interactive=True, scale=1
                )
                top_p = gr.Slider(
                    minimum=0, maximum=1, step=0.05, label=i18n("top_p"), value=1, interactive=True, scale=1
                )
                temperature = gr.Slider(
                    minimum=0, maximum=1, step=0.05, label=i18n("temperature"), value=1, interactive=True, scale=1
                )
        with gr.Row():
            inference_button = gr.Button(value=i18n("合成语音"), variant="primary", size="lg", scale=25)
            output = gr.Audio(label=i18n("输出的语音"), scale=14)

        inference_button.click(
            get_tts_wav,
            [
                inp_ref,
                prompt_text,
                prompt_language,
                text,
                text_language,
                how_to_cut,
                top_k,
                top_p,
                temperature,
                ref_text_free,
                speed,
                if_freeze,
                inp_refs,
                sample_steps,
                if_sr_Checkbox,
                pause_second_slider,
            ],
            [output],
        )
        SoVITS_dropdown.change(
            change_sovits_weights,
            [SoVITS_dropdown, prompt_language, text_language],
            [
                prompt_language,
                text_language,
                prompt_text,
                prompt_language,
                text,
                text_language,
                sample_steps,
                inp_refs,
                ref_text_free,
                if_sr_Checkbox,
                inference_button,
            ],
        )
        GPT_dropdown.change(change_gpt_weights, [GPT_dropdown], [])

if __name__ == "__main__":
    app.queue().launch(
        server_name="0.0.0.0",
        inbrowser=True,
        share=is_share,
        server_port=infer_ttswebui,
    )
