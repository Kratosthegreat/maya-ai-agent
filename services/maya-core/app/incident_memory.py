import json
import os

from datetime import datetime

DB_FILE = "/app/data/incidents.json"


class IncidentMemory:

    def __init__(self):

        os.makedirs(
            "/app/data",
            exist_ok=True
        )

        if not os.path.exists(DB_FILE):

            with open(DB_FILE, "w") as f:

                json.dump([], f)

    def load(self):

        with open(DB_FILE, "r") as f:

            return json.load(f)

    def save(self, data):

        with open(DB_FILE, "w") as f:

            json.dump(
                data,
                f,
                indent=2
            )

    def add_incident(

        self,

        container,

        event

    ):

        data = self.load()

        data.append({

            "container": container,

            "event": event,

            "timestamp": datetime.utcnow().isoformat()

        })

        self.save(data)

    def stability_score(

        self,

        container

    ):

        data = self.load()

        failures = len([

            i for i in data

            if i["container"] == container

        ])

        return max(
            0,
            100 - failures * 5
        )
