import json
import os
from datetime import datetime

AUDIT_DB = "/app/data/audit/actions.json"


class SecurityManager:

    def __init__(self):

        os.makedirs(
            "/app/data/audit",
            exist_ok=True
        )

        if not os.path.exists(AUDIT_DB):

            with open(AUDIT_DB, "w") as f:

                json.dump([], f)

        self.allowed_commands = [

            "df -h",
            "free -h",
            "uptime",
            "docker ps",
            "docker stats --no-stream",
            "ip addr",
            "uname -a"

        ]

        self.allowed_restart_prefixes = [

            "ai_",
            "maya",
            "agent",
            "qdrant",
            "ollama"

        ]

    ####################################
    # AUDIT
    ####################################

    def log_action(

        self,

        action,

        result

    ):

        with open(AUDIT_DB, "r") as f:

            data = json.load(f)

        data.append({

            "timestamp": datetime.utcnow().isoformat(),

            "action": action,

            "result": result

        })

        data = data[-500:]

        with open(AUDIT_DB, "w") as f:

            json.dump(
                data,
                f,
                indent=2
            )

    ####################################
    # VALIDATION
    ####################################

    def validate_command(

        self,

        command

    ):

        return command in self.allowed_commands

    def validate_restart(

        self,

        container

    ):

        return any(

            container.startswith(x)

            for x in self.allowed_restart_prefixes

        )
