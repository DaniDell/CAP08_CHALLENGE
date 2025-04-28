from abc import ABC, abstractmethod
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter


class Splitter(ABC):
    @abstractmethod
    async def split(self, text: str) -> list[str]:
        pass


class LangChainSplitter(Splitter):
    def __init__(self, chunk_size, chunk_overlap, length_function) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function

    async def split(self, text: str) -> list[str]:
        text_splitter = RecursiveCharacterTextSplitter(
            # Set a really small chunk size, just to show.
            separators=["\n\n", "\n", " ", ""],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=self.length_function,
            # is_separator_regex=False,
        )
        chunks = text_splitter.split_text(text)

        return chunks
