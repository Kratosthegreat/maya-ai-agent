class LogAnalyzer:

    def analyze(
        self,
        logs: str
    ):

        lower = logs.lower()

        # ─────────────────────────
        # OOM
        # ─────────────────────────

        if any(x in lower for x in [
            "out of memory",
            "oom",
            "killed"
        ]):

            return (
                "🔍 Root Cause:\n"
                "Out Of Memory (OOM)"
            )

        # ─────────────────────────
        # PORT
        # ─────────────────────────

        if any(x in lower for x in [
            "address already in use",
            "port is already allocated",
            "bind failed"
        ]):

            return (
                "🔍 Root Cause:\n"
                "Port conflict"
            )

        # ─────────────────────────
        # CONNECTION
        # ─────────────────────────

        if any(x in lower for x in [
            "connection refused",
            "failed to connect",
            "timeout"
        ]):

            return (
                "🔍 Root Cause:\n"
                "Connection failure"
            )

        # ─────────────────────────
        # PERMISSION
        # ─────────────────────────

        if any(x in lower for x in [
            "permission denied",
            "access denied"
        ]):

            return (
                "🔍 Root Cause:\n"
                "Permission issue"
            )

        # ─────────────────────────
        # DEFAULT
        # ─────────────────────────

        return (
            "🔍 Root Cause:\n"
            "Unknown"
        )
