import docker

class ContainerMetrics:

    def __init__(self):

        self.client = docker.from_env()

    # ─────────────────────────
    # GET STATS
    # ─────────────────────────

    def get_container_stats(

        self,

        container_name

    ):

        try:

            container = \
                self.client.containers.get(
                    container_name
                )

            stats = container.stats(
                stream=False
            )

            # ─────────────────────────
            # CPU
            # ─────────────────────────

            cpu_delta = (

                stats["cpu_stats"][
                    "cpu_usage"
                ]["total_usage"]

                -

                stats["precpu_stats"][
                    "cpu_usage"
                ]["total_usage"]

            )

            system_delta = (

                stats["cpu_stats"][
                    "system_cpu_usage"
                ]

                -

                stats["precpu_stats"][
                    "system_cpu_usage"
                ]

            )

            cpu_percent = 0.0

            if system_delta > 0:

                cpu_percent = (

                    cpu_delta /
                    system_delta

                ) * 100.0

            # ─────────────────────────
            # RAM
            # ─────────────────────────

            memory_usage = stats[
                "memory_stats"
            ]["usage"]

            memory_limit = stats[
                "memory_stats"
            ]["limit"]

            memory_percent = (

                memory_usage /
                memory_limit

            ) * 100

            return {

                "cpu_percent":
                    round(cpu_percent, 2),

                "memory_percent":
                    round(memory_percent, 2)

            }

        except Exception as e:

            return {

                "error": str(e)

            }
