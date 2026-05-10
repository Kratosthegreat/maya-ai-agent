from collections import defaultdict
from datetime import datetime

class MetricsStore:

    def __init__(self):

        self.metrics = defaultdict(list)

    # ─────────────────────────
    # SAVE
    # ─────────────────────────

    def add_metric(
        self,
        metric_name,
        value
    ):

        self.metrics[
            metric_name
        ].append({
            "value": value,
            "ts": datetime.utcnow()
        })

        # KEEP LAST 100

        self.metrics[
            metric_name
        ] = self.metrics[
            metric_name
        ][-100:]

    # ─────────────────────────
    # GET VALUES
    # ─────────────────────────

    def get_values(
        self,
        metric_name
    ):

        data = self.metrics.get(
            metric_name,
            []
        )

        return [
            x["value"]
            for x in data
        ]

    # ─────────────────────────
    # TREND
    # ─────────────────────────

    def is_increasing(
        self,
        metric_name,
        samples=5
    ):

        values = self.get_values(
            metric_name
        )

        if len(values) < samples:

            return False

        recent = values[-samples:]

        return all(
            recent[i] < recent[i+1]
            for i in range(
                len(recent)-1
            )
        )
