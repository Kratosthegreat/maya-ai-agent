import json
import os

GRAPH_DB = "/app/data/knowledge.json"


class KnowledgeGraph:

    def __init__(self):

        os.makedirs(
            "/app/data",
            exist_ok=True
        )

        if not os.path.exists(GRAPH_DB):

            with open(GRAPH_DB, "w") as f:

                json.dump({}, f)

    def load(self):

        with open(GRAPH_DB, "r") as f:

            return json.load(f)

    def save(self, data):

        with open(GRAPH_DB, "w") as f:

            json.dump(
                data,
                f,
                indent=2
            )

    def remember(

        self,

        key,

        value

    ):

        data = self.load()

        data[key] = value

        self.save(data)

    def recall(self, key):

        data = self.load()

        return data.get(
            key,
            "unknown"
        )
