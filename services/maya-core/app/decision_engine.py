class DecisionEngine:

    def decide(

        self,

        analysis,

        stability_score,

        restart_count,

        similar_incidents=None

    ):

        failure_type = analysis.get(
            "type",
            "UNKNOWN"
        )

        similar_incidents = \
            similar_incidents or []

        # ─────────────────────────
        # MEMORY ANALYSIS
        # ─────────────────────────

        recurring_failures = len(
            similar_incidents
        )

        successful_recoveries = len([

            i for i in similar_incidents

            if i.get("recovery") is True

        ])

        recovery_rate = 0

        if recurring_failures > 0:

            recovery_rate = int(

                (
                    successful_recoveries /
                    recurring_failures
                ) * 100

            )

        # ─────────────────────────
        # MANUAL STOP
        # ─────────────────────────

        if failure_type == "MANUAL_STOP":

            return {

                "action": "IGNORE",

                "reason":
                    "Intentional stop detected.",

                "memory":
                    f"{recurring_failures} similar incidents"

            }

        # ─────────────────────────
        # OOM
        # ─────────────────────────

        if failure_type == "OOM_KILLED":

            return {

                "action": "COOLDOWN",

                "reason":
                    "OOM detected. Preventing restart loop.",

                "memory":
                    f"{recurring_failures} similar incidents"

            }

        # ─────────────────────────
        # RESTART LOOP
        # ─────────────────────────

        if restart_count >= 5:

            return {

                "action": "ESCALATE",

                "reason":
                    "Restart loop detected.",

                "memory":
                    f"{recurring_failures} similar incidents"

            }

        # ─────────────────────────
        # LOW RECOVERY RATE
        # ─────────────────────────

        if recurring_failures >= 3:

            if recovery_rate < 50:

                return {

                    "action": "ESCALATE",

                    "reason":

                        f"Historical recovery rate low "
                        f"({recovery_rate}%).",

                    "memory":

                        f"{recurring_failures} similar incidents"

                }

        # ─────────────────────────
        # LOW STABILITY
        # ─────────────────────────

        if stability_score < 50:

            return {

                "action": "ESCALATE",

                "reason":
                    "Container unstable.",

                "memory":
                    f"{recurring_failures} similar incidents"

            }

        # ─────────────────────────
        # DEFAULT
        # ─────────────────────────

        return {

            "action": "RECOVER",

            "reason":
                "Standard recovery flow.",

            "memory":
                f"{recurring_failures} similar incidents"

        }
