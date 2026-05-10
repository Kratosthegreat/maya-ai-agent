import uuid
import requests
import logging
import queue
import threading
import time

from qdrant_client import (
    QdrantClient
)

from qdrant_client.models import (

    Distance,
    VectorParams,
    PointStruct

)

logger = logging.getLogger(__name__)


class SemanticMemory:

    def __init__(self):

        self.enabled = False

        self.collection = "maya_memory"

        self.queue = queue.Queue()

        self.embedding_cache = {}

        ################################
        # CONNECT
        ################################

        try:

            self.qdrant = QdrantClient(

                host="ai_qdrant",

                port=6333,

                timeout=5

            )

            collections = [

                c.name

                for c in self.qdrant
                .get_collections()
                .collections

            ]

            if self.collection not in collections:

                self.qdrant.create_collection(

                    collection_name=self.collection,

                    vectors_config=VectorParams(

                        size=768,

                        distance=Distance.COSINE

                    )

                )

            self.enabled = True

            logger.info(
                "✅ Semantic memory enabled"
            )

        except Exception as e:

            logger.warning(

                f"Semantic disabled: {e}"

            )

            self.enabled = False

        ################################
        # BACKGROUND WRITER
        ################################

        threading.Thread(

            target=self.worker,

            daemon=True

        ).start()

    ####################################
    # PRIORITY FILTER
    ####################################

    def should_store(

        self,

        text

    ):

        lower = text.lower()

        important = [

            "server",
            "docker",
            "incident",
            "memory",
            "restart",
            "error",
            "issue",
            "project",
            "network",
            "qdrant",
            "ollama",
            "בעיה",
            "שרת",
            "זיכרון"

        ]

        return any(

            x in lower

            for x in important

        )

    ####################################
    # EMBEDDINGS
    ####################################

    def embed(self, text):

        if not self.enabled:

            return None

        ################################
        # CACHE
        ################################

        if text in self.embedding_cache:

            return self.embedding_cache[text]

        try:

            r = requests.post(

                "http://agentos:8000/embed",

                json={

                    "text": text

                },

                timeout=10

            )

            vector = r.json()["embedding"]

            ################################
            # CACHE LIMIT
            ################################

            if len(self.embedding_cache) > 500:

                self.embedding_cache.clear()

            self.embedding_cache[text] = vector

            return vector

        except Exception as e:

            logger.warning(e)

            return None

    ####################################
    # QUEUE STORE
    ####################################

    def store(

        self,

        role,

        text

    ):

        if not self.enabled:

            return

        ################################
        # PRIORITY
        ################################

        if not self.should_store(text):

            return

        self.queue.put({

            "role": role,

            "text": text

        })

    ####################################
    # BACKGROUND WORKER
    ####################################

    def worker(self):

        while True:

            try:

                item = self.queue.get()

                role = item["role"]

                text = item["text"]

                vector = self.embed(text)

                if not vector:

                    continue

                self.qdrant.upsert(

                    collection_name=self.collection,

                    points=[

                        PointStruct(

                            id=str(uuid.uuid4()),

                            vector=vector,

                            payload={

                                "role": role,

                                "text": text

                            }

                        )

                    ]

                )

                time.sleep(0.5)

            except Exception as e:

                logger.warning(e)

                time.sleep(2)

    ####################################
    # SEARCH
    ####################################

    def search(

        self,

        query,

        limit=5

    ):

        if not self.enabled:

            return []

        try:

            vector = self.embed(query)

            if not vector:

                return []

            results = self.qdrant.search(

                collection_name=self.collection,

                query_vector=vector,

                limit=limit

            )

            memories = []

            for r in results:

                payload = r.payload

                memories.append(

                    payload.get(
                        "text",
                        ""
                    )

                )

            return memories

        except Exception as e:

            logger.warning(e)

            return []
