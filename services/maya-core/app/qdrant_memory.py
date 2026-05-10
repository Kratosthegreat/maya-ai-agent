from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

import uuid
import hashlib

class QdrantMemory:

    def __init__(self):

        self.client = QdrantClient(

            host="ai_qdrant",

            port=6333,

            timeout=30

        )

        self.collection = "maya_incidents"

        self.ensure_collection()

    # ─────────────────────────
    # COLLECTION
    # ─────────────────────────

    def ensure_collection(self):

        collections = \
            self.client.get_collections()

        names = [

            c.name

            for c in collections.collections
        ]

        if self.collection not in names:

            self.client.create_collection(

                collection_name=self.collection,

                vectors_config=VectorParams(

                    size=32,

                    distance=Distance.COSINE

                )

            )

    # ─────────────────────────
    # SIMPLE VECTOR
    # ─────────────────────────

    def text_to_vector(

        self,

        text

    ):

        digest = hashlib.md5(
            text.encode()
        ).digest()

        vector = [

            b / 255.0

            for b in digest
        ]

        while len(vector) < 32:

            vector.extend(vector)

        return vector[:32]

    # ─────────────────────────
    # STORE INCIDENT
    # ─────────────────────────

    def store_incident(

        self,

        container,

        failure_type,

        analysis,

        recovery

    ):

        text = (

            f"{container} "
            f"{failure_type} "
            f"{analysis}"

        )

        vector = self.text_to_vector(
            text
        )

        self.client.upsert(

            collection_name=self.collection,

            points=[

                PointStruct(

                    id=str(uuid.uuid4()),

                    vector=vector,

                    payload={

                        "container":
                            container,

                        "failure_type":
                            failure_type,

                        "analysis":
                            analysis,

                        "recovery":
                            recovery

                    }

                )

            ]

        )

    # ─────────────────────────
    # SEARCH
    # ─────────────────────────

    def search_similar(

        self,

        query

    ):

        vector = self.text_to_vector(
            query
        )

        results = self.client.search(

            collection_name=self.collection,

            query_vector=vector,

            limit=3

        )

        return [

            r.payload

            for r in results
        ]
