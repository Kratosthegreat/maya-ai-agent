import docker
import subprocess

from security import (
    SecurityManager
)


class MayaActions:

    def __init__(self):

        self.client = docker.from_env()

        self.security = SecurityManager()

    ####################################
    # DOCKER
    ####################################

    def list_containers(self):

        try:

            containers = self.client.containers.list(
                all=True
            )

            result = []

            for c in containers:

                result.append({

                    "name": c.name,

                    "status": c.status

                })

            return result

        except Exception as e:

            return str(e)

    ####################################
    # RESTART
    ####################################

    def restart_container(

        self,

        name

    ):

        if not self.security.validate_restart(
            name
        ):

            return "❌ Restart blocked by RBAC"

        try:

            container = self.client.containers.get(
                name
            )

            container.restart()

            self.security.log_action(

                f"restart:{name}",

                "success"

            )

            return (

                f"✅ Restarted:\n"

                f"{name}"

            )

        except Exception as e:

            self.security.log_action(

                f"restart:{name}",

                str(e)

            )

            return str(e)

    ####################################
    # LOGS
    ####################################

    def container_logs(

        self,

        name

    ):

        try:

            container = self.client.containers.get(
                name
            )

            logs = container.logs(
                tail=100
            ).decode(
                errors="ignore"
            )

            return logs

        except Exception as e:

            return str(e)

    ####################################
    # SAFE COMMANDS
    ####################################

    def run_safe_command(

        self,

        command

    ):

        if not self.security.validate_command(
            command
        ):

            return "❌ Command blocked"

        try:

            result = subprocess.check_output(

                command,

                shell=True,

                text=True,

                timeout=20

            )

            self.security.log_action(

                command,

                "success"

            )

            return result

        except Exception as e:

            self.security.log_action(

                command,

                str(e)

            )

            return str(e)
