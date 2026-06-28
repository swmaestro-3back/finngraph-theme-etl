from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

class EmbeddingModel:
    def __init__(self, model_name:str="text-embedding-3-small"):
        self.client = OpenAI()
        self.model_name = model_name

    def get_embedding(self, text: str) -> list[float]:
        """
        단일 텍스트용
        """
        if not text:
            raise RuntimeError("embedding text is empty.")
        
        # 여기에 한국어 형태소 전처리 kiwipipey 사용하는거 있어야함
        cleaned_text = text.replace("\n", " ")

        response = self.client.embeddings.create(
            input=[cleaned_text],
            model=self.model_name
        )

        return response.data[0].embedding
    
    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        텍스트 묶음을 받아 배치 처리용
        """
        if not texts:
            raise RuntimeError("embedding text is empty.")

        cleaned_texts = [t.replace("\n", " ") for t in texts]
        
        response = self.client.embeddings.create(
            input=cleaned_texts,
            model=self.model_name
        )
        return [item.embedding for item in response.data]
    
embedding_model = EmbeddingModel()