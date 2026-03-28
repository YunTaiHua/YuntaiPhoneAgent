"""
T2S Lightning 模块
==================

本模块提供基于 PyTorch Lightning 的文本转语义(Text-to-Semantic)训练框架。

主要组件:
    - Text2SemanticLightningModule: Lightning 模块，封装训练、验证逻辑

参考来源:
    - https://github.com/yangdongchao/SoundStorm
    - https://github.com/lifeiteng/vall-e
"""
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

now_dir = Path.cwd()
sys.path.append(str(now_dir))


try:
    import torch
except ImportError as e:
    raise ImportError(f"torch 导入失败: {e}")


try:
    from pytorch_lightning import LightningModule
except ImportError:
    LightningModule = object


try:
    from .t2s_model import Text2SemanticDecoder
except ImportError:
    Text2SemanticDecoder = None
    logger.warning("Text2SemanticDecoder 导入失败")


try:
    from AR.modules.lr_schedulers import WarmupCosineLRSchedule
except ImportError:
    WarmupCosineLRSchedule = None
    logger.debug("WarmupCosineLRSchedule 导入失败")

try:
    from AR.modules.optim import ScaledAdam
except ImportError:
    ScaledAdam = None
    logger.debug("ScaledAdam 导入失败")


class Text2SemanticLightningModule(LightningModule):
    """
    文本转语义 Lightning 模块
    
    基于 PyTorch Lightning 框架实现的文本到语义 token 的转换模型训练器。
    
    Attributes:
        config: 模型配置字典
        top_k: Top-K 采样参数
        model: Text2SemanticDecoder 模型实例
        
    Args:
        config: 模型配置字典，包含模型结构和训练参数
        output_dir: 输出目录路径
        is_train: 是否为训练模式，默认为 True
    """
    
    def __init__(self, config: dict, output_dir: Path, is_train: bool = True) -> None:
        super().__init__()
        self.config = config
        self.top_k = 3
        self.model = Text2SemanticDecoder(config=config, top_k=self.top_k)
        pretrained_s1 = config.get("pretrained_s1")
        if pretrained_s1 and is_train:
            print(
                self.load_state_dict(
                    torch.load(
                        pretrained_s1,
                        map_location="cpu",
                        weights_only=False,
                    )["weight"],
                )
            )
            logger.info(f"加载预训练权重: {pretrained_s1}")
        if is_train:
            self.automatic_optimization = False
            self.save_hyperparameters()
            self.eval_dir = output_dir / "eval"
            self.eval_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"创建评估目录: {self.eval_dir}")

    def training_step(self, batch: dict, batch_idx: int) -> None:
        """
        训练步骤
        
        执行单个训练批次的前向传播、反向传播和参数更新。
        
        Args:
            batch: 训练批次数据，包含 phoneme_ids, semantic_ids, bert_feature 等
            batch_idx: 批次索引
        """
        opt = self.optimizers()
        scheduler = self.lr_schedulers()
        forward = self.model.forward if self.config["train"].get("if_dpo", False) == True else self.model.forward_old
        loss, acc = forward(
            batch["phoneme_ids"],
            batch["phoneme_ids_len"],
            batch["semantic_ids"],
            batch["semantic_ids_len"],
            batch["bert_feature"],
        )
        self.manual_backward(loss)
        if batch_idx > 0 and batch_idx % 4 == 0:
            opt.step()
            opt.zero_grad()
            scheduler.step()

        self.log(
            "total_loss",
            loss,
            on_step=True,
            on_epoch=True,
            prog_bar=True,
            sync_dist=True,
        )
        self.log(
            "lr",
            scheduler.get_last_lr()[0],
            on_epoch=True,
            prog_bar=True,
            sync_dist=True,
        )
        self.log(
            f"top_{self.top_k}_acc",
            acc,
            on_step=True,
            on_epoch=True,
            prog_bar=True,
            sync_dist=True,
        )

    def validation_step(self, batch: dict, batch_idx: int) -> None:
        """
        验证步骤
        
        当前版本暂未实现验证逻辑。
        
        Args:
            batch: 验证批次数据
            batch_idx: 批次索引
        """
        return

    def configure_optimizers(self) -> dict:
        """
        配置优化器和学习率调度器
        
        Returns:
            包含优化器和学习率调度器配置的字典
        """
        model_parameters = self.model.parameters()
        parameters_names = []
        parameters_names.append([name_param_pair[0] for name_param_pair in self.model.named_parameters()])
        lm_opt = ScaledAdam(
            model_parameters,
            lr=0.01,
            betas=(0.9, 0.95),
            clipping_scale=2.0,
            parameters_names=parameters_names,
            show_dominant_parameters=False,
            clipping_update_period=1000,
        )

        return {
            "optimizer": lm_opt,
            "lr_scheduler": {
                "scheduler": WarmupCosineLRSchedule(
                    lm_opt,
                    init_lr=self.config["optimizer"]["lr_init"],
                    peak_lr=self.config["optimizer"]["lr"],
                    end_lr=self.config["optimizer"]["lr_end"],
                    warmup_steps=self.config["optimizer"]["warmup_steps"],
                    total_steps=self.config["optimizer"]["decay_steps"],
                )
            },
        }
