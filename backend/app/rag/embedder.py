"""本地向量化：fastembed + BGE 中文小模型，无需额外 API Key。

首次使用会自动从 HuggingFace 下载模型（约 100MB）；
国内网络默认走 hf-mirror 镜像，如已配置 HF_ENDPOINT 则尊重用户设置。
"""
import os

# 必须在导入 huggingface_hub（fastembed 依赖）之前设置
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from fastembed import TextEmbedding  # noqa: E402

QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："

_model: TextEmbedding | None = None


def get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(model_name="BAAI/bge-small-zh-v1.5")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量向量化（用于文档切片），统一转成 Python float 便于 JSON 存储。"""
    return [[float(x) for x in v] for v in get_model().embed(texts)]


def embed_query(query: str) -> list[float]:
    """向量化查询（BGE 中文模型要求查询语句带指令前缀）。"""
    vec = next(iter(get_model().embed([QUERY_PREFIX + query])))
    return [float(x) for x in vec]
