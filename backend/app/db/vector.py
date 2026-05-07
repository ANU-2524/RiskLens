from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from sentence_transformers import SentenceTransformer
import structlog
from app.core.config import settings

logger = structlog.get_logger(__name__)

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(url=settings.qdrant_url)
        self.model = SentenceTransformer(settings.embedding_model)
        self.collection_name = settings.qdrant_collection_name
        self._ensure_collection()

    def _ensure_collection(self):
        """Creates the collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                logger.info("creating_qdrant_collection", collection=self.collection_name)
                # MiniLM-L6-v2 produces 384-dimensional vectors
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=rest.VectorParams(
                        size=384, 
                        distance=rest.Distance.COSINE
                    ),
                )
        except Exception as e:
            logger.error("qdrant_connection_error", error=str(e))

    def embed_text(self, text: str):
        """Converts text into a vector embedding."""
        return self.model.encode(text).tolist()

    async def upsert_signal(self, signal_id: int, text: str, metadata: dict):
        """Stores a signal's vector and metadata in Qdrant."""
        vector = self.embed_text(text)
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                rest.PointStruct(
                    id=signal_id,
                    vector=vector,
                    payload=metadata
                )
            ]
        )

    async def search_similar(self, query: str, limit: int = 10):
        """Performs semantic search."""
        query_vector = self.embed_text(query)
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )

# Global instance
vector_store = VectorStore()
