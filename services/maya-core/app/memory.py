import json
import os

MEMORY_DB = "/app/data/memory.json"


class Memory:

    def __init__(self):

        os.makedirs(
            "/app/data",
            exist_ok=True
        )

        if not os.path.exists(
            MEMORY_DB
        ):

            with open(
                MEMORY_DB,
                "w"
            ) as f:

                json.dump([], f)

    def load(self):

        with open(
            MEMORY_DB,
            "r"
        ) as f:

            return json.load(f)

    def save(self, data):

        with open(
            MEMORY_DB,
            "w"
        ) as f:

            json.dump(
                data,
                f,
                indent=2
            )

    def add_memory(

        self,

        role,

        content

    ):

        data = self.load()

        data.append({

            "role": role,

            "content": content

        })

        data = data[-50:]

        self.save(data)

    def get_context(self):

        data = self.load()

        result = []

        for item in data[-15:]:

            result.append(

                f"{item['role']}: "

                f"{item['content']}"

            )

        return "\n".join(result)
