import json
import os

TASK_DB = "/app/data/tasks.json"


class TaskEngine:

    def __init__(self):

        os.makedirs(
            "/app/data",
            exist_ok=True
        )

        if not os.path.exists(TASK_DB):

            with open(TASK_DB, "w") as f:

                json.dump([], f)

    def load(self):

        with open(TASK_DB, "r") as f:

            return json.load(f)

    def save(self, data):

        with open(TASK_DB, "w") as f:

            json.dump(
                data,
                f,
                indent=2
            )

    def add_task(self, text):

        data = self.load()

        data.append({

            "task": text,

            "status": "open"

        })

        self.save(data)

    def list_tasks(self):

        return self.load()
