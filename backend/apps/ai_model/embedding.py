import os.path
import threading
from typing import Optional

import httpx
from langchain_core.embeddings import Embeddings
from pydantic import BaseModel

from common.core.config import settings

os.environ["TOKENIZERS_PARALLELISM"] = "false"


class EmbeddingModelInfo(BaseModel):
    folder: str
    name: str
    device: str = 'cpu'


local_embedding_model = EmbeddingModelInfo(folder=settings.LOCAL_MODEL_PATH,
                                           name=os.path.join(settings.LOCAL_MODEL_PATH, 'embedding',
                                                             "shibing624_text2vec-base-chinese"))


class OpenAIEmbeddings(Embeddings):
    """OpenAI 兼容的 Embedding API 包装器"""

    def __init__(self, api_url: str, api_key: str = '', model: str = ''):
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self._client = httpx.Client(timeout=120, headers={'Authorization': f'Bearer {api_key}' if api_key else ''})

    def _call_api(self, input_texts: list[str]) -> list[list[float]]:
        payload = {"input": input_texts, "model": self.model}
        resp = self._client.post(self.api_url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return [item['embedding'] for item in data['data']]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._call_api(texts)

    def embed_query(self, text: str) -> list[float]:
        result = self._call_api([text])
        return result[0]


_lock = threading.Lock()
locks = {}

_embedding_model: dict[str, Optional[Embeddings]] = {}


class EmbeddingModelCache:

    @staticmethod
    def _new_instance(config: EmbeddingModelInfo = local_embedding_model):
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=config.name, cache_folder=config.folder,
                                     model_kwargs={'device': config.device},
                                     encode_kwargs={'normalize_embeddings': True}
                                     )

    @staticmethod
    def _get_lock(key: str = settings.DEFAULT_EMBEDDING_MODEL):
        lock = locks.get(key)
        if lock is None:
            with _lock:
                lock = locks.get(key)
                if lock is None:
                    lock = threading.Lock()
                    locks[key] = lock

        return lock

    @staticmethod
    def get_model(key: str = settings.DEFAULT_EMBEDDING_MODEL,
                  config: EmbeddingModelInfo = local_embedding_model) -> Embeddings:
        # 优先使用 OpenAI 兼容 API
        if settings.EMBEDDING_OPENAI_ENABLED:
            api_key = '_openai_'
            model_instance = _embedding_model.get(api_key)
            if model_instance is None:
                with _lock:
                    model_instance = _embedding_model.get(api_key)
                    if model_instance is None:
                        model_instance = OpenAIEmbeddings(
                            api_url=settings.EMBEDDING_OPENAI_API_URL,
                            api_key=settings.EMBEDDING_OPENAI_API_KEY,
                            model=settings.EMBEDDING_OPENAI_MODEL,
                        )
                        _embedding_model[api_key] = model_instance
            return model_instance

        # 回退到本地 HuggingFace 模型
        model_instance = _embedding_model.get(key)
        if model_instance is None:
            lock = EmbeddingModelCache._get_lock(key)
            with lock:
                model_instance = _embedding_model.get(key)
                if model_instance is None:
                    model_instance = EmbeddingModelCache._new_instance(config)
                    _embedding_model[key] = model_instance

        return model_instance
