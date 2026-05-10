import time

class StabilityEngine:

    def __init__(self):

        self.history = {}

    # ─────────────────────────
    # RECORD EVENT
    # ─────────────────────────

    def record(

        self,

        container,

        event

    ):

        if container not in self.history:

            self.history[container] = []

        self.history[container].append({

            "time": time.time(),

            "event": event

        })

        # keep last 100

        self.history[container] = \
            self.history[container][-100:]

    # ─────────────────────────
    # ANALYZE
    # ─────────────────────────

    def analyze(

        self,

        container

    ):

        if container not in self.history:

            return {

                "score": 100,

                "restarts": 0,

                "risk": "LOW",

                "message": "Stable"

            }

        recent = [

            e for e in self.history[container]

            if time.time() - e["time"] < 3600

        ]

        restarts = len(recent)

        # ─────────────────────────
        # SCORE
        # ─────────────────────────

        score = max(

            0,

            100 - (restarts * 10)

        )

        # ─────────────────────────
        # RISK
        # ─────────────────────────

        if restarts >= 6:

            risk = "HIGH"

            message = \
                "Container extremely unstable"

        elif restarts >= 3:

            risk = "MEDIUM"

            message = \
                "Container instability detected"

        else:

            risk = "LOW"

            message = "Stable"

        return {

            "score": score,

            "restarts": restarts,

            "risk": risk,

            "message": message

        }
