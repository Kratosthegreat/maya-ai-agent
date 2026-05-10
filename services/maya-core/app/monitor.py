import asyncio
import docker
import logging

logger = logging.getLogger(__name__)


class SystemMonitor:

    def __init__(

        self,

        control_plane=None

    ):

        self.client = docker.from_env()

        self.control_plane = control_plane

    async def start(self):

        logger.info(
            "✅ Monitor started"
        )

        while True:

            try:

                containers = self.client.containers.list(
                    all=True
                )

                for c in containers:

                    ################################
                    # DOWN EVENTS
                    ################################

                    if c.status != "running":

                        logger.warning(

                            f"EVENT: "

                            f"{c.name} "

                            f"-> "

                            f"{c.status}"

                        )

                        if self.control_plane:

                            self.control_plane.bus.emit(

                                "container_down",

                                {

                                    "container": c.name,

                                    "status": c.status

                                }

                            )

            except Exception as e:

                logger.warning(e)

            await asyncio.sleep(60)
