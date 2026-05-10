class RemediationEngine:

    def plan(
        self,
        root_cause
    ):

        rc = root_cause.lower()

        # ─────────────────────────
        # OOM
        # ─────────────────────────

        if (
            "memory" in rc
            or "oom" in rc
        ):

            return {
                "action": "restart",
                "cleanup": True,
                "safe": True,
                "reason": "OOM detected"
            }

        # ─────────────────────────
        # CONNECTION
        # ─────────────────────────

        if "connection" in rc:

            return {
                "action": "restart_dependencies",
                "cleanup": False,
                "safe": True,
                "reason": "Connection issue"
            }

        # ─────────────────────────
        # PORT
        # ─────────────────────────

        if "port" in rc:

            return {
                "action": "escalate",
                "cleanup": False,
                "safe": False,
                "reason": "Port conflict"
            }

        # ─────────────────────────
        # PERMISSIONS
        # ─────────────────────────

        if "permission" in rc:

            return {
                "action": "escalate",
                "cleanup": False,
                "safe": False,
                "reason": "Permission issue"
            }

        # ─────────────────────────
        # DEFAULT
        # ─────────────────────────

        return {
            "action": "restart",
            "cleanup": False,
            "safe": True,
            "reason": "Generic recovery"
        }
