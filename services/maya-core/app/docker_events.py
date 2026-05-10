import docker
import logging

logger = logging.getLogger(__name__)

class DockerEvents:

    def __init__(self):

        self.client = docker.from_env()

    def stream(self):

        logger.info(
            "✅ Docker event stream active"
        )

        for event in self.client.events(
            decode=True
        ):

            try:

                if event.get("Type") != "container":

                    continue

                action = event.get(
                    "Action",
                    ""
                )

                actor = event.get(
                    "Actor",
                    {}
                )

                attrs = actor.get(
                    "Attributes",
                    {}
                )

                name = attrs.get(
                    "name",
                    "unknown"
                )

                yield {

                    "container": name,

                    "action": action

                }

            except Exception as e:

                logger.exception(
                    f"Event parse failed: {e}"
                )
