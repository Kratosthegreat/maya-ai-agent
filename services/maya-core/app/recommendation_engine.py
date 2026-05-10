class RecommendationEngine:

    def recommend(

        self,

        reason,

        container

    ):

        reason = reason.lower()

        # ─────────────────────────
        # MEMORY
        # ─────────────────────────

        if "oom" in reason \
        or "memory" in reason:

            return (

                "🧠 Likely Cause:\n"

                "Memory pressure / OOM.\n\n"

                "💡 Recommendation:\n"

                "- לבדוק RAM\n"

                "- לבדוק memory leak\n"

                "- לבדוק vector indexing\n"

                "- לבדוק batch sizes"

            )

        # ─────────────────────────
        # NETWORK
        # ─────────────────────────

        if "connection" in reason \
        or "timeout" in reason:

            return (

                "🧠 Likely Cause:\n"

                "Network instability.\n\n"

                "💡 Recommendation:\n"

                "- לבדוק docker network\n"

                "- לבדוק DNS\n"

                "- לבדוק dependencies"

            )

        # ─────────────────────────
        # CPU
        # ─────────────────────────

        if "cpu" in reason:

            return (

                "🧠 Likely Cause:\n"

                "CPU saturation.\n\n"

                "💡 Recommendation:\n"

                "- לבדוק loops\n"

                "- לבדוק overload\n"

                "- לבדוק runaway process"

            )

        # ─────────────────────────
        # DEFAULT
        # ─────────────────────────

        return (

            "🧠 Root cause unclear.\n\n"

            "💡 Recommendation:\n"

            "- לבדוק logs\n"

            "- לבדוק metrics\n"

            "- לבדוק dependencies"

        )
