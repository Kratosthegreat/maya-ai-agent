import docker

class DockerIntelligence:

    def __init__(self):

        self.client = docker.from_env()

    # ─────────────────────────
    # INSPECT
    # ─────────────────────────

    def inspect_container(

        self,

        container_name

    ):

        try:

            container = \
                self.client.containers.get(
                    container_name
                )

            attrs = container.attrs

            state = attrs.get(
                "State",
                {}
            )

            return {

                "status":
                    state.get("Status"),

                "exit_code":
                    state.get("ExitCode"),

                "oom_killed":
                    state.get("OOMKilled"),

                "error":
                    state.get("Error"),

                "started_at":
                    state.get("StartedAt"),

                "finished_at":
                    state.get("FinishedAt"),

                "restart_count":
                    attrs.get(
                        "RestartCount",
                        0
                    )

            }

        except Exception as e:

            return {

                "error": str(e)

            }

    # ─────────────────────────
    # ANALYZE
    # ─────────────────────────

    def analyze_failure(

        self,

        container_name

    ):

        info = self.inspect_container(
            container_name
        )

        exit_code = info.get(
            "exit_code"
        )

        oom = info.get(
            "oom_killed"
        )

        # ─────────────────────────
        # OOM
        # ─────────────────────────

        if oom:

            return {

                "type": "OOM_KILLED",

                "message":
                    "Container killed by OOM Killer.",

                "recommendation":
                    "Check RAM / memory leak."
            }

        # ─────────────────────────
        # MANUAL STOP
        # ─────────────────────────

        if exit_code in [137, 143]:

            return {

                "type": "MANUAL_STOP",

                "message":
                    "Container stopped gracefully by user/orchestrator.",

                "recommendation":
                    "No infrastructure issue detected."
            }

        # ─────────────────────────
        # NORMAL EXIT
        # ─────────────────────────

        if exit_code == 0:

            return {

                "type": "NORMAL_EXIT",

                "message":
                    "Container exited normally.",

                "recommendation":
                    "No action required."
            }

        # ─────────────────────────
        # CRASH
        # ─────────────────────────

        if exit_code not in [
            0,
            None
        ]:

            return {

                "type": "CRASH",

                "message":
                    f"Container crashed with exit code {exit_code}.",

                "recommendation":
                    "Check application logs."
            }

        # ─────────────────────────
        # UNKNOWN
        # ─────────────────────────

        return {

            "type": "UNKNOWN",

            "message":
                "Unknown failure reason.",

            "recommendation":
                "Check logs and metrics."
        }
