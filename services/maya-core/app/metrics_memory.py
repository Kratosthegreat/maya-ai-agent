import time
from collections import defaultdict

class MetricsMemory:

    def __init__(self):

        self.history = defaultdict(list)

    # ─────────────────────────
    # STORE METRICS
    # ─────────────────────────

    def add(

        self,

        container,

        cpu,

        ram

    ):

        self.history[container].append({

            "time": time.time(),

            "cpu": cpu,

            "ram": ram

        })

        # KEEP LAST 100
        self.history[container] = \
            self.history[container][-100:]

    # ─────────────────────────
    # TREND ANALYSIS
    # ─────────────────────────

    def analyze(

        self,

        container

    ):

        data = self.history.get(
            container,
            []
        )

        if len(data) < 5:

            return {

                "trend": "UNKNOWN",

                "confidence": 0

            }

        ram_values = [

            x["ram"]

            for x in data[-5:]
        ]

        cpu_values = [

            x["cpu"]

            for x in data[-5:]
        ]

        # ─────────────────────────
        # MEMORY LEAK
        # ─────────────────────────

        if ram_values == sorted(ram_values):

            if ram_values[-1] - ram_values[0] > 10:

                return {

                    "trend":
                        "MEMORY_LEAK",

                    "confidence":
                        85

                }

        # ─────────────────────────
        # CPU RUNAWAY
        # ─────────────────────────

        if cpu_values == sorted(cpu_values):

            if cpu_values[-1] - cpu_values[0] > 15:

                return {

                    "trend":
                        "CPU_RUNAWAY",

                    "confidence":
                        80

                }

        return {

            "trend": "STABLE",

            "confidence": 100

        }
