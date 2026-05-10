import docker
import logging
import time

from health_checks import HealthChecks

logger = logging.getLogger(__name__)

PROTECTED_CONTAINERS = [
    "maya-v2"
]

class ActionEngine:

    def __init__(self):

        self.client = docker.from_env()

        self.health = HealthChecks()

    # ─────────────────────────
    # GET LOGS
    # ─────────────────────────

    def get_logs(

        self,

        container_name,

        tail=50

    ):

        try:

            container = \
                self.client.containers.get(
                    container_name
                )

            logs = container.logs(
                tail=tail
            ).decode(
                errors="ignore"
            )

            return logs

        except Exception as e:

            logger.exception(
                f"Log fetch failed: {e}"
            )

            return str(e)

    # ─────────────────────────
    # CHECK STATUS
    # ─────────────────────────

    def is_running(

        self,

        container_name

    ):

        try:

            container = \
                self.client.containers.get(
                    container_name
                )

            container.reload()

            return (
                container.status == "running"
            )

        except Exception:

            return False

    # ─────────────────────────
    # SAFE RESTART
    # ─────────────────────────

    def restart_container(

        self,

        container_name

    ):

        if container_name in PROTECTED_CONTAINERS:

            return (
                False,
                "Protected container"
            )

        try:

            logger.warning(
                f"Restarting {container_name}"
            )

            container = \
                self.client.containers.get(
                    container_name
                )

            container.restart(
                timeout=10
            )

            # ─────────────────────────
            # WAIT HEALTH
            # ─────────────────────────

            for _ in range(20):

                if not self.is_running(
                    container_name
                ):

                    time.sleep(2)

                    continue

                # ─────────────────────────
                # REAL HEALTHCHECK
                # ─────────────────────────

                healthy = \
                    self.health.check(
                        container_name
                    )

                if healthy:

                    logger.info(
                        f"{container_name} recovered"
                    )

                    return (
                        True,
                        f"✅ {container_name} חזר תקין"
                    )

                time.sleep(3)

            return (

                False,

                f"{container_name} healthcheck failed"

            )

        except Exception as e:

            logger.exception(
                f"Restart failed: {e}"
            )

            return (
                False,
                str(e)
            )

    # ─────────────────────────
    # RECOVERY
    # ─────────────────────────

    def recover_with_dependencies(

        self,

        container_name

    ):

        if container_name in PROTECTED_CONTAINERS:

            return (
                False,
                "Protected container"
            )

        dependency_map = {

            "ai_openwebui": [
                "ai_qdrant",
                "ai_ollama"
            ]

        }

        dependencies = dependency_map.get(
            container_name,
            []
        )

        for dep in dependencies:

            if dep in PROTECTED_CONTAINERS:

                continue

            self.restart_container(dep)

        return self.restart_container(
            container_name
        )
