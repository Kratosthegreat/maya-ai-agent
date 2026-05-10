from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import uuid

class VectorMemory:
    def __init__(self):
        self.client = QdrantClient(
            host="ai_qdrant",
            port=6333,
            timeout=5.0
        )

        self.model = None
        self.collection = "maya_memory"

        self._ensure_collection()

    def _ensure_collection(self):
        collections = self.client.get_collections().collections
        names = [c.name for c in collections]

        if self.collection not in names:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config={"size": 384, "distance": "Cosine"}
            )

    def _get_model(self):
        if self.model is None:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
        return self.model

    def add(self, user_id: int, text: str):
        try:
            model = self._get_model()
            vec = model.encode(text).tolist()

            self.client.upsert(
                collection_name=self.collection,
                points=[{
                    "id": str(uuid.uuid4()),
                    "vector": vec,
                    "payload": {
                        "user_id": user_id,
                        "text": text
                    }
                }]
            )
        except Exception:
            pass  # לא להפיל את הבוט

    def search(self, user_id: int, query: str, limit: int = 5):
        try:
            model = self._get_model()
            vec = model.encode(query).tolist()

            hits = self.client.search(
                collection_name=self.collection,
                query_vector=vec,
                limit=limit
            )

            return [
                h.payload["text"]
                for h in hits
                if h.payload.get("user_id") == user_id
            ]
        except Exception:
            return []
