import time

class RootCauseEngine:

    def __init__(self):

        self.events = []

    # ─────────────────────────
    # STORE EVENT
    # ─────────────────────────

    def add_event(

        self,

        container,

        event_type

    ):

        self.events.append({

            "time": time.time(),

            "container": container,

            "event": event_type

        })

        # keep last 100

        self.events = self.events[-100:]

    # ─────────────────────────
    # ANALYZE
    # ─────────────────────────

    def analyze(self):

        recent = [

            e for e in self.events

            if time.time() - e["time"] < 300

        ]

        containers = set(

            e["container"]

            for e in recent

        )

        # ─────────────────────────
        # MULTI-CONTAINER FAILURE
        # ─────────────────────────

        if len(containers) >= 3:

            return {

                "risk": "HIGH",

                "cause": (

                    "Possible host-level "

                    "resource exhaustion"

                )

            }

        # ─────────────────────────
        # QDRANT + OLLAMA
        # ─────────────────────────

        names = [

            e["container"]

            for e in recent

        ]

        if (

            "ai_ollama" in names

            and "ai_qdrant" in names

        ):

            return {

                "risk": "MEDIUM",

                "cause": (

                    "AI stack instability"

                )

            }

        return {

            "risk": "LOW",

            "cause": "No correlation"

        }
