class RecoveryPolicy:

    def decide(

        self,

        stability,

        analysis

    ):

        restarts = stability.get(
            "restarts",
            0
        )

        risk = stability.get(
            "risk",
            "LOW"
        )

        failure = analysis.get(
            "type",
            "UNKNOWN"
        )

        # ─────────────────────────
        # NORMAL EXIT
        # ─────────────────────────

        if failure == "NORMAL_EXIT":

            return {

                "action": "IGNORE",

                "reason": (

                    "Container exited normally"

                )

            }

        # ─────────────────────────
        # HIGH INSTABILITY
        # ─────────────────────────

        if risk == "HIGH":

            return {

                "action": "ESCALATE",

                "reason": (

                    "Container highly unstable"

                )

            }

        # ─────────────────────────
        # MEDIUM INSTABILITY
        # ─────────────────────────

        if risk == "MEDIUM":

            return {

                "action": "COOLDOWN",

                "reason": (

                    "Repeated failures detected"

                )

            }

        # ─────────────────────────
        # OOM
        # ─────────────────────────

        if failure == "OOM":

            return {

                "action": "ESCALATE",

                "reason": (

                    "Out of memory condition"

                )

            }

        # ─────────────────────────
        # DEFAULT
        # ─────────────────────────

        return {

            "action": "RECOVER",

            "reason": (

                "Automatic recovery approved"

            )

        }
