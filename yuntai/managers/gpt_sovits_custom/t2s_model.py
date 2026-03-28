"""
T2S 模型模块
============

本模块实现文本转语义(Text-to-Semantic)的神经网络模型架构。

主要组件:
    - Text2SemanticDecoder: 文本到语义 token 的解码器模型
    - T2STransformer: Transformer 编码器架构
    - T2SBlock: Transformer 块
    - T2SMLP: 多层感知机

模型特点:
    - 基于 Transformer 的自回归生成
    - 支持 KV Cache 优化推理
    - 支持流式输出模式

参考来源:
    - https://github.com/yangdongchao/SoundStorm
    - https://github.com/lifeiteng/vall-e
"""
import logging
import math

logger = logging.getLogger(__name__)


try:
    import torch
    from torch import nn
    from torch.nn import functional as F
except ImportError as e:
    raise ImportError(f"torch 导入失败: {e}")


try:
    from torchmetrics.classification import MulticlassAccuracy
except ImportError:
    MulticlassAccuracy = None
    logger.debug("torchmetrics.classification 导入失败")


try:
    from AR.models.utils import (
        dpo_loss,
        get_batch_logps,
        make_pad_mask,
        make_pad_mask_left,
        make_reject_y,
        sample,
        topk_sampling,
    )
except ImportError:
    dpo_loss = None
    get_batch_logps = None
    make_pad_mask = None
    make_pad_mask_left = None
    make_reject_y = None
    sample = None
    topk_sampling = None
    logger.debug("AR.models.utils 导入失败")

try:
    from AR.modules.embedding import SinePositionalEmbedding, TokenEmbedding
except ImportError:
    SinePositionalEmbedding = None
    TokenEmbedding = None
    logger.debug("AR.modules.embedding 导入失败")

try:
    from AR.modules.transformer import LayerNorm, TransformerEncoder, TransformerEncoderLayer
except ImportError:
    LayerNorm = None
    TransformerEncoder = None
    TransformerEncoderLayer = None
    logger.debug("AR.modules.transformer 导入失败")


default_config = {
    "embedding_dim": 512,
    "hidden_dim": 512,
    "num_head": 8,
    "num_layers": 12,
    "num_codebook": 8,
    "p_dropout": 0.0,
    "vocab_size": 1024 + 1,
    "phoneme_vocab_size": 512,
    "EOS": 1024,
}


def scaled_dot_product_attention(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    attn_mask: torch.Tensor | None = None,
    scale: torch.Tensor | None = None,
) -> torch.Tensor:
    """
    缩放点积注意力计算
    
    实现 Scaled Dot-Product Attention，支持注意力掩码。
    
    Args:
        query: 查询张量，形状为 (B, H, L, D)
        key: 键张量，形状为 (B, H, S, D)
        value: 值张量，形状为 (B, H, S, D)
        attn_mask: 注意力掩码，可选
        scale: 缩放因子，可选
        
    Returns:
        注意力输出张量，形状为 (B, H, L, D)
    """
    B, H, L, S = query.size(0), query.size(1), query.size(-2), key.size(-2)
    if scale is None:
        scale_factor = torch.tensor(1 / math.sqrt(query.size(-1)))
    else:
        scale_factor = scale
    attn_bias = torch.zeros(B, H, L, S, dtype=query.dtype, device=query.device)

    if attn_mask is not None:
        if attn_mask.dtype == torch.bool:
            attn_bias.masked_fill_(attn_mask, float("-inf"))
        else:
            attn_bias += attn_mask
    attn_weight = query @ key.transpose(-2, -1) * scale_factor
    attn_weight += attn_bias
    attn_weight = torch.softmax(attn_weight, dim=-1)

    if attn_mask is not None:
        if attn_mask.dtype == torch.bool:
            attn_weight.masked_fill_(attn_mask, 0)
        else:
            attn_mask[attn_mask != float("-inf")] = 0
            attn_mask[attn_mask == float("-inf")] = 1
            attn_weight.masked_fill_(attn_mask, 0)

    return attn_weight @ value


@torch.jit.script
class T2SMLP:
    """
    T2S 多层感知机
    
    简单的两层全连接网络，用于 Transformer 块中的前馈层。
    
    Attributes:
        w1: 第一层权重
        b1: 第一层偏置
        w2: 第二层权重
        b2: 第二层偏置
    """
    
    def __init__(self, w1, b1, w2, b2):
        self.w1 = w1
        self.b1 = b1
        self.w2 = w2
        self.b2 = b2

    def forward(self, x):
        """
        前向传播
        
        Args:
            x: 输入张量
            
        Returns:
            输出张量
        """
        x = F.relu(F.linear(x, self.w1, self.b1))
        x = F.linear(x, self.w2, self.b2)
        return x


@torch.jit.script
class T2SBlock:
    """
    T2S Transformer 块
    
    单个 Transformer 编码器块，包含自注意力和前馈网络。
    支持 KV Cache 用于高效推理。
    
    Attributes:
        num_heads: 注意力头数
        mlp: 多层感知机
        hidden_dim: 隐藏层维度
        qkv_w: QKV 投影权重
        qkv_b: QKV 投影偏置
        out_w: 输出投影权重
        out_b: 输出投影偏置
        norm_w1: 第一个 LayerNorm 权重
        norm_b1: 第一个 LayerNorm 偏置
        norm_eps1: 第一个 LayerNorm epsilon
        norm_w2: 第二个 LayerNorm 权重
        norm_b2: 第二个 LayerNorm 偏置
        norm_eps2: 第二个 LayerNorm epsilon
    """
    
    def __init__(
        self,
        num_heads,
        hidden_dim: int,
        mlp: T2SMLP,
        qkv_w,
        qkv_b,
        out_w,
        out_b,
        norm_w1,
        norm_b1,
        norm_eps1,
        norm_w2,
        norm_b2,
        norm_eps2,
    ):
        self.num_heads = num_heads
        self.mlp = mlp
        self.hidden_dim: int = hidden_dim
        self.qkv_w = qkv_w
        self.qkv_b = qkv_b
        self.out_w = out_w
        self.out_b = out_b
        self.norm_w1 = norm_w1
        self.norm_b1 = norm_b1
        self.norm_eps1 = norm_eps1
        self.norm_w2 = norm_w2
        self.norm_b2 = norm_b2
        self.norm_eps2 = norm_eps2

        self.false = torch.tensor(False, dtype=torch.bool)

    @torch.jit.ignore
    def to_mask(
        self,
        x: torch.Tensor,
        padding_mask: torch.Tensor | None,
    ) -> torch.Tensor:
        """
        应用填充掩码
        
        Args:
            x: 输入张量
            padding_mask: 填充掩码
            
        Returns:
            掩码后的张量
        """
        if padding_mask is None:
            return x

        if padding_mask.dtype == torch.bool:
            return x.masked_fill(padding_mask, 0)
        else:
            return x * padding_mask

    def process_prompt(
        self,
        x: torch.Tensor,
        attn_mask: torch.Tensor,
        padding_mask: torch.Tensor | None = None,
        torch_sdpa: bool = True,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        处理提示词阶段
        
        处理完整的提示词序列，初始化 KV Cache。
        
        Args:
            x: 输入张量
            attn_mask: 注意力掩码
            padding_mask: 填充掩码，可选
            torch_sdpa: 是否使用 PyTorch 内置 SDPA，默认为 True
            
        Returns:
            元组 (输出张量, K Cache, V Cache)
        """
        q, k, v = F.linear(self.to_mask(x, padding_mask), self.qkv_w, self.qkv_b).chunk(3, dim=-1)

        batch_size = q.shape[0]
        q_len = q.shape[1]
        kv_len = k.shape[1]

        q = self.to_mask(q, padding_mask)
        k_cache = self.to_mask(k, padding_mask)
        v_cache = self.to_mask(v, padding_mask)

        q = q.view(batch_size, q_len, self.num_heads, -1).transpose(1, 2)
        k = k_cache.view(batch_size, kv_len, self.num_heads, -1).transpose(1, 2)
        v = v_cache.view(batch_size, kv_len, self.num_heads, -1).transpose(1, 2)

        if torch_sdpa:
            attn = F.scaled_dot_product_attention(q, k, v, ~attn_mask)
        else:
            attn = scaled_dot_product_attention(q, k, v, attn_mask)

        attn = attn.transpose(1, 2).reshape(batch_size, q_len, -1)
        attn = F.linear(self.to_mask(attn, padding_mask), self.out_w, self.out_b)

        x = x + attn
        x = F.layer_norm(x, [self.hidden_dim], self.norm_w1, self.norm_b1, self.norm_eps1)
        x = x + self.mlp.forward(x)
        x = F.layer_norm(
            x,
            [self.hidden_dim],
            self.norm_w2,
            self.norm_b2,
            self.norm_eps2,
        )
        return x, k_cache, v_cache

    def decode_next_token(
        self,
        x: torch.Tensor,
        k_cache: torch.Tensor,
        v_cache: torch.Tensor,
        attn_mask: torch.Tensor | None = None,
        torch_sdpa: bool = True,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        解码下一个 token
        
        使用 KV Cache 高效解码下一个 token。
        
        Args:
            x: 当前 token 的输入张量
            k_cache: K Cache
            v_cache: V Cache
            attn_mask: 注意力掩码，可选
            torch_sdpa: 是否使用 PyTorch 内置 SDPA，默认为 True
            
        Returns:
            元组 (输出张量, 更新后的 K Cache, 更新后的 V Cache)
        """
        q, k, v = F.linear(x, self.qkv_w, self.qkv_b).chunk(3, dim=-1)

        k_cache = torch.cat([k_cache, k], dim=1)
        v_cache = torch.cat([v_cache, v], dim=1)

        batch_size = q.shape[0]
        q_len = q.shape[1]
        kv_len = k_cache.shape[1]

        q = q.view(batch_size, q_len, self.num_heads, -1).transpose(1, 2)
        k = k_cache.view(batch_size, kv_len, self.num_heads, -1).transpose(1, 2)
        v = v_cache.view(batch_size, kv_len, self.num_heads, -1).transpose(1, 2)

        if torch_sdpa:
            attn = F.scaled_dot_product_attention(q, k, v, (~attn_mask) if attn_mask is not None else None)
        else:
            attn = scaled_dot_product_attention(q, k, v, attn_mask)

        attn = attn.transpose(1, 2).reshape(batch_size, q_len, -1)
        attn = F.linear(attn, self.out_w, self.out_b)

        x = x + attn
        x = F.layer_norm(
            x,
            [self.hidden_dim],
            self.norm_w1,
            self.norm_b1,
            self.norm_eps1,
        )
        x = x + self.mlp.forward(x)
        x = F.layer_norm(
            x,
            [self.hidden_dim],
            self.norm_w2,
            self.norm_b2,
            self.norm_eps2,
        )
        return x, k_cache, v_cache


@torch.jit.script
class T2STransformer:
    """
    T2S Transformer 编码器
    
    由多个 T2SBlock 组成的 Transformer 编码器，
    支持提示词处理和增量解码。
    
    Attributes:
        num_blocks: Transformer 块数量
        blocks: Transformer 块列表
    """
    
    def __init__(self, num_blocks: int, blocks: list[T2SBlock]):
        self.num_blocks: int = num_blocks
        self.blocks = blocks

    def process_prompt(
        self,
        x: torch.Tensor,
        attn_mask: torch.Tensor,
        padding_mask: torch.Tensor | None = None,
        torch_sdpa: bool = True,
    ) -> tuple[torch.Tensor, list[torch.Tensor], list[torch.Tensor]]:
        """
        处理提示词阶段
        
        Args:
            x: 输入张量
            attn_mask: 注意力掩码
            padding_mask: 填充掩码，可选
            torch_sdpa: 是否使用 PyTorch 内置 SDPA
            
        Returns:
            元组 (输出张量, K Cache 列表, V Cache 列表)
        """
        k_cache: list[torch.Tensor] = []
        v_cache: list[torch.Tensor] = []
        for i in range(self.num_blocks):
            x, k_cache_, v_cache_ = self.blocks[i].process_prompt(x, attn_mask, padding_mask, torch_sdpa)
            k_cache.append(k_cache_)
            v_cache.append(v_cache_)
        return x, k_cache, v_cache

    def decode_next_token(
        self,
        x: torch.Tensor,
        k_cache: list[torch.Tensor],
        v_cache: list[torch.Tensor],
        attn_mask: torch.Tensor | None = None,
        torch_sdpa: bool = True,
    ) -> tuple[torch.Tensor, list[torch.Tensor], list[torch.Tensor]]:
        """
        解码下一个 token
        
        Args:
            x: 当前 token 的输入张量
            k_cache: K Cache 列表
            v_cache: V Cache 列表
            attn_mask: 注意力掩码，可选
            torch_sdpa: 是否使用 PyTorch 内置 SDPA
            
        Returns:
            元组 (输出张量, 更新后的 K Cache 列表, 更新后的 V Cache 列表)
        """
        for i in range(self.num_blocks):
            x, k_cache[i], v_cache[i] = self.blocks[i].decode_next_token(
                x, k_cache[i], v_cache[i], attn_mask, torch_sdpa
            )
        return x, k_cache, v_cache


class Text2SemanticDecoder(nn.Module):
    """
    文本转语义解码器
    
    将文本音素序列转换为语义 token 序列的自回归模型。
    支持 DPO 训练和多种推理模式。
    
    Attributes:
        model_dim: 模型维度
        embedding_dim: 嵌入维度
        num_head: 注意力头数
        num_layers: Transformer 层数
        norm_first: 是否前置归一化
        vocab_size: 词汇表大小
        phoneme_vocab_size: 音素词汇表大小
        p_dropout: Dropout 概率
        EOS: 结束符 ID
        bert_proj: BERT 特征投影层
        ar_text_embedding: 文本嵌入层
        ar_text_position: 文本位置编码
        ar_audio_embedding: 音频嵌入层
        ar_audio_position: 音频位置编码
        h: Transformer 编码器
        ar_predict_layer: 预测层
        loss_fct: 损失函数
        ar_accuracy_metric: 准确率度量
        t2s_transformer: T2S Transformer
    """
    
    def __init__(self, config, norm_first: bool = False, top_k: int = 3):
        """
        初始化解码器
        
        Args:
            config: 模型配置字典
            norm_first: 是否使用前置归一化，默认为 False
            top_k: Top-K 准确率计算的 K 值，默认为 3
        """
        super(Text2SemanticDecoder, self).__init__()
        self.model_dim = config["model"]["hidden_dim"]
        self.embedding_dim = config["model"]["embedding_dim"]
        self.num_head = config["model"]["head"]
        self.num_layers = config["model"]["n_layer"]
        self.norm_first = norm_first
        self.vocab_size = config["model"]["vocab_size"]
        self.phoneme_vocab_size = config["model"]["phoneme_vocab_size"]
        self.p_dropout = config["model"]["dropout"]
        self.EOS = config["model"]["EOS"]
        self.norm_first = norm_first
        assert self.EOS == self.vocab_size - 1
        
        self.bert_proj = nn.Linear(1024, self.embedding_dim)
        self.ar_text_embedding = TokenEmbedding(
            self.embedding_dim,
            self.phoneme_vocab_size,
            self.p_dropout,
        )
        self.ar_text_position = SinePositionalEmbedding(
            self.embedding_dim,
            dropout=0.1,
            scale=False,
            alpha=True,
        )
        self.ar_audio_embedding = TokenEmbedding(
            self.embedding_dim,
            self.vocab_size,
            self.p_dropout,
        )
        self.ar_audio_position = SinePositionalEmbedding(
            self.embedding_dim,
            dropout=0.1,
            scale=False,
            alpha=True,
        )

        self.h = TransformerEncoder(
            TransformerEncoderLayer(
                d_model=self.model_dim,
                nhead=self.num_head,
                dim_feedforward=self.model_dim * 4,
                dropout=0.1,
                batch_first=True,
                norm_first=norm_first,
            ),
            num_layers=self.num_layers,
            norm=LayerNorm(self.model_dim) if norm_first else None,
        )

        self.ar_predict_layer = nn.Linear(self.model_dim, self.vocab_size, bias=False)
        self.loss_fct = nn.CrossEntropyLoss(reduction="sum")

        self.ar_accuracy_metric = MulticlassAccuracy(
            self.vocab_size,
            top_k=top_k,
            average="micro",
            multidim_average="global",
            ignore_index=self.EOS,
        )

        blocks = []

        for i in range(self.num_layers):
            layer = self.h.layers[i]
            t2smlp = T2SMLP(
                layer.linear1.weight,
                layer.linear1.bias,
                layer.linear2.weight,
                layer.linear2.bias,
            )

            block = T2SBlock(
                self.num_head,
                self.model_dim,
                t2smlp,
                layer.self_attn.in_proj_weight,
                layer.self_attn.in_proj_bias,
                layer.self_attn.out_proj.weight,
                layer.self_attn.out_proj.bias,
                layer.norm1.weight,
                layer.norm1.bias,
                layer.norm1.eps,
                layer.norm2.weight,
                layer.norm2.bias,
                layer.norm2.eps,
            )

            blocks.append(block)

        self.t2s_transformer = T2STransformer(self.num_layers, blocks)

    def make_input_data(self, x, x_lens, y, y_lens, bert_feature):
        """
        构建输入数据
        
        将音素和语义序列组合成模型输入格式。
        
        Args:
            x: 音素 ID 序列
            x_lens: 音素序列长度
            y: 语义 ID 序列
            y_lens: 语义序列长度
            bert_feature: BERT 特征
            
        Returns:
            元组 (位置编码后的输入, 注意力掩码, 目标序列)
        """
        x = self.ar_text_embedding(x)
        x = x + self.bert_proj(bert_feature.transpose(1, 2))
        x = self.ar_text_position(x)
        x_mask = make_pad_mask_left(x_lens)

        y_mask = make_pad_mask(y_lens)
        y_mask_int = y_mask.type(torch.int64)
        codes = y.type(torch.int64) * (1 - y_mask_int)

        y, targets = self.pad_y_eos(codes, y_mask_int, eos_id=self.EOS)
        x_len = x_lens.max()
        y_len = y_lens.max()
        y_emb = self.ar_audio_embedding(y)
        y_pos = self.ar_audio_position(y_emb)

        xy_padding_mask = torch.concat([x_mask, y_mask], dim=1)

        ar_xy_padding_mask = xy_padding_mask

        x_attn_mask = F.pad(
            torch.zeros((x_len, x_len), dtype=torch.bool, device=x.device),
            (0, y_len),
            value=True,
        )
        y_attn_mask = F.pad(
            torch.triu(
                torch.ones(y_len, y_len, dtype=torch.bool, device=x.device),
                diagonal=1,
            ),
            (x_len, 0),
            value=False,
        )

        xy_attn_mask = torch.concat([x_attn_mask, y_attn_mask], dim=0)
        bsz, src_len = x.shape[0], x_len + y_len
        _xy_padding_mask = (
            ar_xy_padding_mask.view(bsz, 1, 1, src_len)
            .expand(-1, self.num_head, -1, -1)
            .reshape(bsz * self.num_head, 1, src_len)
        )
        xy_attn_mask = xy_attn_mask.logical_or(_xy_padding_mask)
        new_attn_mask = torch.zeros_like(xy_attn_mask, dtype=x.dtype)
        new_attn_mask.masked_fill_(xy_attn_mask, float("-inf"))
        xy_attn_mask = new_attn_mask
        xy_pos = torch.concat([x, y_pos], dim=1)

        return xy_pos, xy_attn_mask, targets

    def forward(self, x, x_lens, y, y_lens, bert_feature):
        """
        前向传播（带 DPO）
        
        执行带 DPO（Direct Preference Optimization）损失的前向传播。
        
        Args:
            x: 音素 ID 序列
            x_lens: 音素序列长度
            y: 语义 ID 序列
            y_lens: 语义序列长度
            bert_feature: BERT 特征
            
        Returns:
            元组 (总损失, 准确率)
        """
        reject_y, reject_y_lens = make_reject_y(y, y_lens)

        xy_pos, xy_attn_mask, targets = self.make_input_data(x, x_lens, y, y_lens, bert_feature)

        xy_dec, _ = self.h(
            (xy_pos, None),
            mask=xy_attn_mask,
        )
        x_len = x_lens.max()
        logits = self.ar_predict_layer(xy_dec[:, x_len-1:])

        reject_xy_pos, reject_xy_attn_mask, reject_targets = self.make_input_data(
            x, x_lens, reject_y, reject_y_lens, bert_feature
        )

        reject_xy_dec, _ = self.h(
            (reject_xy_pos, None),
            mask=reject_xy_attn_mask,
        )
        x_len = x_lens.max()
        reject_logits = self.ar_predict_layer(reject_xy_dec[:, x_len-1:])

        loss_1 = F.cross_entropy(logits.permute(0, 2, 1), targets, reduction="sum")
        acc = self.ar_accuracy_metric(logits.permute(0, 2, 1).detach(), targets).item()

        A_logits, R_logits = get_batch_logps(logits, reject_logits, targets, reject_targets)
        loss_2, _, _ = dpo_loss(A_logits, R_logits, 0, 0, 0.2, reference_free=True)

        loss = loss_1 + loss_2

        return loss, acc

    def forward_old(self, x, x_lens, y, y_lens, bert_feature):
        """
        前向传播（旧版）
        
        执行不带 DPO 损失的标准前向传播。
        
        Args:
            x: 音素 ID 序列
            x_lens: 音素序列长度
            y: 语义 ID 序列
            y_lens: 语义序列长度
            bert_feature: BERT 特征
            
        Returns:
            元组 (损失, 准确率)
        """
        x = self.ar_text_embedding(x)
        x = x + self.bert_proj(bert_feature.transpose(1, 2))
        x = self.ar_text_position(x)
        x_mask = make_pad_mask_left(x_lens)

        y_mask = make_pad_mask(y_lens)
        y_mask_int = y_mask.type(torch.int64)
        codes = y.type(torch.int64) * (1 - y_mask_int)

        y, targets = self.pad_y_eos(codes, y_mask_int, eos_id=self.EOS)
        x_len = x_lens.max()
        y_len = y_lens.max()
        y_emb = self.ar_audio_embedding(y)
        y_pos = self.ar_audio_position(y_emb)

        xy_padding_mask = torch.concat([x_mask, y_mask], dim=1)
        ar_xy_padding_mask = xy_padding_mask

        x_attn_mask = F.pad(
            torch.zeros((x_len, x_len), dtype=torch.bool, device=x.device),
            (0, y_len),
            value=True,
        )
        y_attn_mask = F.pad(
            torch.triu(
                torch.ones(y_len, y_len, dtype=torch.bool, device=x.device),
                diagonal=1,
            ),
            (x_len, 0),
            value=False,
        )
        xy_attn_mask = torch.concat([x_attn_mask, y_attn_mask], dim=0)
        bsz, src_len = x.shape[0], x_len + y_len
        _xy_padding_mask = (
            ar_xy_padding_mask.view(bsz, 1, 1, src_len)
            .expand(-1, self.num_head, -1, -1)
            .reshape(bsz * self.num_head, 1, src_len)
        )
        xy_attn_mask = xy_attn_mask.logical_or(_xy_padding_mask)
        new_attn_mask = torch.zeros_like(xy_attn_mask, dtype=x.dtype)
        new_attn_mask.masked_fill_(xy_attn_mask, float("-inf"))
        xy_attn_mask = new_attn_mask
        xy_pos = torch.concat([x, y_pos], dim=1)
        xy_dec, _ = self.h(
            (xy_pos, None),
            mask=xy_attn_mask,
        )
        logits = self.ar_predict_layer(xy_dec[:, x_len-1:]).permute(0, 2, 1)
        loss = F.cross_entropy(logits, targets, reduction="sum")
        acc = self.ar_accuracy_metric(logits.detach(), targets).item()
        return loss, acc

    def infer(
        self,
        x,
        x_lens,
        prompts,
        bert_feature,
        top_k: int = -100,
        early_stop_num: int = -1,
        temperature: float = 1.0,
    ):
        """
        推理生成
        
        自回归生成语义 token 序列。
        
        Args:
            x: 音素 ID 序列
            x_lens: 音素序列长度
            prompts: 提示词语义 token
            bert_feature: BERT 特征
            top_k: Top-K 采样参数
            early_stop_num: 提前停止的 token 数量
            temperature: 温度参数
            
        Returns:
            生成的语义 token 序列
        """
        x = self.ar_text_embedding(x)
        x = x + self.bert_proj(bert_feature.transpose(1, 2))
        x = self.ar_text_position(x)

        y = prompts
        prefix_len = y.shape[1]
        x_len = x.shape[1]
        x_attn_mask = torch.zeros((x_len, x_len), dtype=torch.bool)
        stop = False
        for _ in range(1500):
            y_emb = self.ar_audio_embedding(y)
            y_pos = self.ar_audio_position(y_emb)
            xy_pos = torch.concat([x, y_pos], dim=1)
            y_len = y.shape[1]
            x_attn_mask_pad = F.pad(
                x_attn_mask,
                (0, y_len),
                value=True,
            )
            y_attn_mask = F.pad(
                torch.triu(torch.ones(y_len, y_len, dtype=torch.bool), diagonal=1),
                (x_len, 0),
                value=False,
            )
            xy_attn_mask = torch.concat([x_attn_mask_pad, y_attn_mask], dim=0).to(y.device)

            xy_dec, _ = self.h(
                (xy_pos, None),
                mask=xy_attn_mask,
            )
            logits = self.ar_predict_layer(xy_dec[:, -1])
            samples = topk_sampling(logits, top_k=top_k, top_p=1.0, temperature=temperature)

            if early_stop_num != -1 and (y.shape[1] - prefix_len) > early_stop_num:
                print("use early stop num:", early_stop_num)
                stop = True

            if torch.argmax(logits, dim=-1)[0] == self.EOS or samples[0, 0] == self.EOS:
                stop = True
            if stop:
                if prompts.shape[1] == y.shape[1]:
                    y = torch.concat([y, torch.zeros_like(samples)], dim=1)
                    print("bad zero prediction")
                print(f"T2S Decoding EOS [{prefix_len} -> {y.shape[1]}]")
                break
            y = torch.concat([y, samples], dim=1)
        return y

    def pad_y_eos(self, y, y_mask_int, eos_id):
        """
        填充并添加 EOS token
        
        Args:
            y: 输入序列
            y_mask_int: 掩码
            eos_id: EOS token ID
            
        Returns:
            元组 (填充后的输入, 目标序列)
        """
        targets = F.pad(y, (0, 1), value=0) + eos_id * F.pad(y_mask_int, (0, 1), value=1)
        return targets[:, :-1], targets

    def infer_panel_batch_infer(
        self,
        x: list[torch.LongTensor],
        x_lens: torch.LongTensor,
        prompts: torch.LongTensor,
        bert_feature: list[torch.LongTensor],
        top_k: int = -100,
        top_p: int = 100,
        early_stop_num: int = -1,
        temperature: float = 1.0,
        repetition_penalty: float = 1.35,
        **kwargs,
    ) -> tuple[list[torch.LongTensor], list[int]]:
        """
        批量推理生成
        
        对多个文本序列进行批量推理生成。
        
        Args:
            x: 文本 token 列表
            x_lens: 文本长度张量
            prompts: 参考音频 token
            bert_feature: BERT 特征列表
            top_k: Top-K 采样参数
            top_p: Top-P 采样参数
            early_stop_num: 提前停止的 token 数量
            temperature: 温度参数
            repetition_penalty: 重复惩罚系数
            
        Returns:
            元组 (生成的语义 token 列表, 索引列表)
        """
        if prompts is None:
            print("Warning: Prompt free is not supported batch_infer! switch to naive_infer")
            return self.infer_panel_naive_batched(
                x,
                x_lens,
                prompts,
                bert_feature,
                top_k=top_k,
                top_p=top_p,
                early_stop_num=early_stop_num,
                temperature=temperature,
                **kwargs,
            )

        max_len = kwargs.get("max_len", x_lens.max())
        x_list = []
        for x_item, bert_item in zip(x, bert_feature):
            x_item = self.ar_text_embedding(x_item.unsqueeze(0))
            x_item = x_item + self.bert_proj(bert_item.transpose(0, 1).unsqueeze(0))
            x_item = self.ar_text_position(x_item).squeeze(0)
            x_item = (
                F.pad(x_item, (0, 0, max_len - x_item.shape[0], 0), value=0) if x_item.shape[0] < max_len else x_item
            )
            x_list.append(x_item)
        x: torch.Tensor = torch.stack(x_list, dim=0)

        y = prompts

        x_len = x.shape[1]
        stop = False

        k_cache = None
        v_cache = None
        assert y is not None, "Error: Prompt free is not supported batch_infer!"
        ref_free = False

        y_emb = self.ar_audio_embedding(y)
        y_len = y_emb.shape[1]
        prefix_len = y.shape[1]
        y_lens = torch.LongTensor([y_emb.shape[1]] * y_emb.shape[0]).to(x.device)
        y_pos = self.ar_audio_position(y_emb)
        xy_pos = torch.concat([x, y_pos], dim=1)

        bsz = x.shape[0]
        src_len = x_len + y_len
        y_paddind_mask = make_pad_mask_left(y_lens, y_len)
        x_paddind_mask = make_pad_mask_left(x_lens, max_len)

        padding_mask = torch.concat([x_paddind_mask, y_paddind_mask], dim=1)

        x_mask = F.pad(
            torch.zeros(x_len, x_len, dtype=torch.bool, device=x.device),
            (0, y_len),
            value=True,
        )

        y_mask = F.pad(
            torch.triu(torch.ones(y_len, y_len, dtype=torch.bool, device=x.device), diagonal=1),
            (x_len, 0),
            value=False,
        )

        causal_mask = torch.concat([x_mask, y_mask], dim=0).view(1, src_len, src_len).repeat(bsz, 1, 1).to(x.device)

        padding_mask = padding_mask.view(bsz, 1, src_len).repeat(1, src_len, 1)

        attn_mask: torch.Tensor = causal_mask.logical_or(padding_mask)
        attn_mask = attn_mask.unsqueeze(1).expand(-1, self.num_head, -1, -1).bool()

        y_list = [None] * y.shape[0]
        batch_idx_map = list(range(y.shape[0]))
        idx_list = [None] * y.shape[0]
        for idx in range(1500):
            if idx == 0:
                xy_dec, k_cache, v_cache = self.t2s_transformer.process_prompt(xy_pos, attn_mask, None)
            else:
                xy_dec, k_cache, v_cache = self.t2s_transformer.decode_next_token(xy_pos, k_cache, v_cache, attn_mask)
            logits = self.ar_predict_layer(xy_dec[:, -1])

            if idx == 0:
                attn_mask = F.pad(attn_mask[:, :, -1].unsqueeze(-2), (0, 1), value=False)
            else:
                attn_mask = F.pad(attn_mask, (0, 1), value=False)

            if idx < 11:
                logits = logits[:, :-1] 

            samples = sample(
                logits, y, top_k=top_k, top_p=top_p, repetition_penalty=repetition_penalty, temperature=temperature
            )[0]

            y = torch.concat([y, samples], dim=1)

            tokens = torch.argmax(logits, dim=-1)
            reserved_idx_of_batch_for_y = None
            if (self.EOS in samples[:, 0]) or (self.EOS in tokens):
                l1 = samples[:, 0] == self.EOS
                l2 = tokens == self.EOS
                l = l1.logical_or(l2)
                removed_idx_of_batch_for_y = torch.where(l == True)[0].tolist()
                reserved_idx_of_batch_for_y = torch.where(l == False)[0]
                for i in removed_idx_of_batch_for_y:
                    batch_index = batch_idx_map[i]
                    idx_list[batch_index] = idx
                    y_list[batch_index] = y[i, :-1]

                batch_idx_map = [batch_idx_map[i] for i in reserved_idx_of_batch_for_y.tolist()]

            if reserved_idx_of_batch_for_y is not None:
                y = torch.index_select(y, dim=0, index=reserved_idx_of_batch_for_y)
                attn_mask = torch.index_select(attn_mask, dim=0, index=reserved_idx_of_batch_for_y)
                if k_cache is not None:
                    for i in range(len(k_cache)):
                        k_cache[i] = torch.index_select(k_cache[i], dim=0, index=reserved_idx_of_batch_for_y)
                        v_cache[i] = torch.index_select(v_cache[i], dim=0, index=reserved_idx_of_batch_for_y)

            if (early_stop_num != -1 and (y.shape[1] - prefix_len) > early_stop_num) or idx == 1499:
                print("use early stop num:", early_stop_num)
                stop = True
                for i, batch_index in enumerate(batch_idx_map):
                    batch_index = batch_idx_map[i]
                    idx_list[batch_index] = idx
                    y_list[batch_index] = y[i, :-1]

            if None not in idx_list:
                stop = True

            if stop:
                if y.shape[1] == 0:
                    y = torch.concat([y, torch.zeros_like(samples)], dim=1)
                    print("bad zero prediction")
                print(f"T2S Decoding EOS [{prefix_len} -> {y.shape[1]}]")
                break

            y_emb = self.ar_audio_embedding(y[:, -1:])
            xy_pos = y_emb * self.ar_audio_position.x_scale + self.ar_audio_position.alpha * self.ar_audio_position.pe[
                :, y_len + idx
            ].to(dtype=y_emb.dtype, device=y_emb.device)

        if None in idx_list:
            for i in range(x.shape[0]):
                if idx_list[i] is None:
                    idx_list[i] = 1500 - 1

        if ref_free:
            return y_list, [0] * x.shape[0]
        return y_list, idx_list

    def infer_panel_naive_batched(
        self,
        x: list[torch.LongTensor],
        x_lens: torch.LongTensor,
        prompts: torch.LongTensor,
        bert_feature: list[torch.LongTensor],
        top_k: int = -100,
        top_p: int = 100,
        early_stop_num: int = -1,
        temperature: float = 1.0,
        repetition_penalty: float = 1.35,
        **kwargs,
    ) -> tuple[list[torch.LongTensor], list[int]]:
        """
        朴素批量推理
        
        逐个序列进行推理，而非真正的批量并行。
        
        Args:
            x: 文本 token 列表
            x_lens: 文本长度张量
            prompts: 参考音频 token
            bert_feature: BERT 特征列表
            top_k: Top-K 采样参数
            top_p: Top-P 采样参数
            early_stop_num: 提前停止的 token 数量
            temperature: 温度参数
            repetition_penalty: 重复惩罚系数
            
        Returns:
            元组 (生成的语义 token 列表, 索引列表)
        """
        y_list = []
        idx_list = []
        for i in range(len(x)):
            y, idx = next(self.infer_panel_naive(
                x[i].unsqueeze(0),
                x_lens[i],
                prompts[i].unsqueeze(0) if prompts is not None else None,
                bert_feature[i].unsqueeze(0),
                top_k,
                top_p,
                early_stop_num,
                temperature,
                repetition_penalty,
                **kwargs,
            ))
            y_list.append(y[0])
            idx_list.append(idx)

        return y_list, idx_list

    def infer_panel_naive(
        self,
        x: torch.LongTensor,
        x_lens: torch.LongTensor,
        prompts: torch.LongTensor,
        bert_feature: torch.LongTensor,
        top_k: int = -100,
        top_p: int = 100,
        early_stop_num: int = -1,
        temperature: float = 1.0,
        repetition_penalty: float = 1.35,
        streaming_mode: bool = False,
        chunk_length: int = 24,
        **kwargs,
    ):
        """
        朴素推理生成
        
        单序列推理生成，支持流式输出模式。
        
        Args:
            x: 文本 token
            x_lens: 文本长度
            prompts: 参考音频 token
            bert_feature: BERT 特征
            top_k: Top-K 采样参数
            top_p: Top-P 采样参数
            early_stop_num: 提前停止的 token 数量
            temperature: 温度参数
            repetition_penalty: 重复惩罚系数
            streaming_mode: 是否启用流式模式
            chunk_length: 流式输出的块长度
            
        Yields:
            元组 (生成的语义 token, 是否结束标志)
        """
        mute_emb_sim_matrix = kwargs.get("mute_emb_sim_matrix", None)
        chunk_split_thershold = kwargs.get("chunk_split_thershold", 0.3)
        check_token_num = 2


        x = self.ar_text_embedding(x)
        x = x + self.bert_proj(bert_feature.transpose(1, 2))
        x = self.ar_text_position(x)

        y = prompts

        x_len = x.shape[1]
        x_attn_mask = torch.zeros((x_len, x_len), dtype=torch.bool)
        stop = False

        k_cache = None
        v_cache = None
        if y is not None:
            y_emb = self.ar_audio_embedding(y)
            y_len = y_emb.shape[1]
            prefix_len = y.shape[1]
            y_pos = self.ar_audio_position(y_emb)
            xy_pos = torch.concat([x, y_pos], dim=1)
            ref_free = False
        else:
            y_emb = None
            y_len = 0
            prefix_len = 0
            y_pos = None
            xy_pos = x
            y = torch.zeros(x.shape[0], 0, dtype=torch.int, device=x.device)
            ref_free = True

        bsz = x.shape[0]
        src_len = x_len + y_len
        x_attn_mask_pad = F.pad(
            x_attn_mask,
            (0, y_len),
            value=True,
        )
        y_attn_mask = F.pad(
            torch.triu(torch.ones(y_len, y_len, dtype=torch.bool), diagonal=1),
            (x_len, 0),
            value=False,
        )
        xy_attn_mask = (
            torch.concat([x_attn_mask_pad, y_attn_mask], dim=0)
            .unsqueeze(0)
            .expand(bsz * self.num_head, -1, -1)
            .view(bsz, self.num_head, src_len, src_len)
            .to(device=x.device, dtype=torch.bool)
        )

        token_counter = 0
        curr_ptr = prefix_len
        for idx in range(1500):
            token_counter+=1
            if xy_attn_mask is not None:
                xy_dec, k_cache, v_cache = self.t2s_transformer.process_prompt(xy_pos, xy_attn_mask, None)
            else:
                xy_dec, k_cache, v_cache = self.t2s_transformer.decode_next_token(xy_pos, k_cache, v_cache)

            logits = self.ar_predict_layer(xy_dec[:, -1])

            if idx == 0:
                xy_attn_mask = None
            if idx < 11:
                logits = logits[:, :-1]

            samples = sample(
                logits, y, top_k=top_k, top_p=top_p, repetition_penalty=repetition_penalty, temperature=temperature
            )[0]

            y = torch.concat([y, samples], dim=1)

            if early_stop_num != -1 and (y.shape[1] - prefix_len) > early_stop_num:
                print("use early stop num:", early_stop_num)
                stop = True

            if torch.argmax(logits, dim=-1)[0] == self.EOS or samples[0, 0] == self.EOS:
                stop = True
                y=y[:, :-1]
                token_counter -= 1

            if idx == 1499:
                stop = True

            if stop:
                if y.shape[1] == 0:
                    y = torch.concat([y, torch.zeros_like(samples)], dim=1)
                    print("bad zero prediction")
                if streaming_mode:
                    yield y[:, curr_ptr:] if curr_ptr<y.shape[1] else None, True
                break


            if streaming_mode and (mute_emb_sim_matrix is not None) and (token_counter >= chunk_length+check_token_num):
                score = mute_emb_sim_matrix[y[0, curr_ptr:]] - chunk_split_thershold
                score[score<0]=-1
                score[:-1]=score[:-1]+score[1:]
                argmax_idx = score.argmax()

                if score[argmax_idx]>=0 and argmax_idx+1>=chunk_length: 
                    print(f"\n\ncurr_ptr:{curr_ptr}")
                    yield y[:, curr_ptr:], False
                    token_counter -= argmax_idx+1
                    curr_ptr += argmax_idx+1


            elif streaming_mode and (mute_emb_sim_matrix is None) and (token_counter >= chunk_length):
                yield y[:, -token_counter:], False
                curr_ptr+=token_counter
                token_counter = 0
                


            y_emb = self.ar_audio_embedding(y[:, -1:])
            xy_pos = y_emb * self.ar_audio_position.x_scale + self.ar_audio_position.alpha * self.ar_audio_position.pe[
                :, y_len + idx
            ].to(dtype=y_emb.dtype, device=y_emb.device)



        if not streaming_mode:
            if ref_free:
                yield y, 0
            yield y, idx



    def infer_panel(
        self,
        x: torch.LongTensor,
        x_lens: torch.LongTensor,
        prompts: torch.LongTensor,
        bert_feature: torch.LongTensor,
        top_k: int = -100,
        top_p: int = 100,
        early_stop_num: int = -1,
        temperature: float = 1.0,
        repetition_penalty: float = 1.35,
        **kwargs,
    ):
        """
        面板推理接口
        
        提供统一的推理接口，内部调用 infer_panel_naive。
        
        Args:
            x: 文本 token
            x_lens: 文本长度
            prompts: 参考音频 token
            bert_feature: BERT 特征
            top_k: Top-K 采样参数
            top_p: Top-P 采样参数
            early_stop_num: 提前停止的 token 数量
            temperature: 温度参数
            repetition_penalty: 重复惩罚系数
            
        Returns:
            元组 (生成的语义 token, 索引)
        """
        return next(self.infer_panel_naive(
            x, x_lens, prompts, bert_feature, top_k, top_p, early_stop_num, temperature, repetition_penalty, **kwargs
        ))
