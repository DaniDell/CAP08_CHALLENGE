from abc import ABC, abstractmethod
import json
import aiohttp

import openai


class Embeddings(ABC):
    """Abstraction of embeddings client."""

    @abstractmethod
    async def run(self, chunks: list[str]) -> list[list[float]]:
        pass


class OpenAIEmbeddings(Embeddings):
    """OpenAI embeddings client wrapper"""

    vector_dimension = 1536

    async def run(
        self, chunks: list[str], model="text-embedding-ada-002"
    ) -> list[list[float]]:
        response = await openai.Embedding.acreate(input=chunks, model=model)
        vectors = map(lambda x: x["embedding"], response["data"])  # type: ignore
        return list(vectors)
