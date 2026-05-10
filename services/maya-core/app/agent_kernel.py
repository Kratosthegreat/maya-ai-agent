import asyncio

from async_ai import (
    AsyncAI
)

from tools import MayaTools

from tasks import TaskEngine

from memory import Memory

from actions import MayaActions

from knowledge import KnowledgeGraph

from health import (
    HealthEngine
)

from semantic_memory import (
    SemanticMemory
)


class MayaKernel:

    def __init__(self):

        self.ai = AsyncAI()

        self.tools = MayaTools()

        self.tasks = TaskEngine()

        self.memory = Memory()

        self.actions = MayaActions()

        self.knowledge = KnowledgeGraph()

        self.health = HealthEngine()

        self.semantic = SemanticMemory()

    ####################################
    # INTENTS
    ####################################

    def detect_intent(self, text):

        lower = text.lower()

        intents = []

        if lower.startswith("/task"):

            intents.append("task")

        if lower == "/tasks":

            intents.append("tasks")

        if "docker ps" in lower:

            intents.append("docker")

        if "restart" in lower:

            intents.append("restart")

        if "logs" in lower:

            intents.append("logs")

        if any(x in lower for x in [

            "cpu",
            "memory",
            "disk",
            "ram"

        ]):

            intents.append("health")

        if not intents:

            intents.append("chat")

        return intents

    ####################################
    # EXECUTE
    ####################################

    async def execute(self, text):

        intents = self.detect_intent(
            text
        )

        ################################
        # TASK
        ################################

        if "task" in intents:

            task = text.replace(
                "/task",
                ""
            ).strip()

            self.tasks.add_task(task)

            return f"✅ Task added:\n{task}"

        ################################
        # TASKS
        ################################

        if "tasks" in intents:

            tasks = self.tasks.list_tasks()

            if not tasks:

                return "No tasks."

            output = "📋 Tasks:\n\n"

            for i, t in enumerate(tasks, 1):

                output += (

                    f"{i}. "

                    f"{t['task']} "

                    f"[{t['status']}]\n"

                )

            return output

        ################################
        # DOCKER
        ################################

        if "docker" in intents:

            containers = self.actions.list_containers()

            output = "🐳 Containers:\n\n"

            for c in containers:

                output += (

                    f"{c['name']} "

                    f"[{c['status']}]\n"

                )

            return output

        ################################
        # RESTART
        ################################

        if "restart" in intents:

            container = text.split()[-1]

            return self.actions.restart_container(
                container
            )

        ################################
        # LOGS
        ################################

        if "logs" in intents:

            container = text.split()[-1]

            logs = self.actions.container_logs(
                container
            )

            prompt = f"""

Analyze logs:

{logs[:2500]}

"""

            return await self.ai.generate(
                prompt
            )

        ################################
        # HEALTH
        ################################

        if "health" in intents:

            health = self.health.system_health()

            return (

                f"🖥 System Health\n\n"

                f"CPU: {health['cpu']}%\n"

                f"RAM: {health['memory_percent']}%\n"

                f"Disk: {health['disk_percent']:.1f}%"

            )

        ################################
        # SEMANTIC SEARCH
        ################################

        semantic_context = []

        ################################
        # RESOURCE AWARE
        ################################

        if not self.health.high_memory():

            semantic_context = self.semantic.search(
                text
            )

        ################################
        # CHAT
        ################################

        context = self.memory.get_context()

        prompt = f"""

Current time:
{self.tools.get_time()}

Location:
{self.tools.get_location()}

Weather:
{self.tools.get_weather()}

Semantic memory:
{semantic_context}

Conversation:
{context}

User:
{text}

Respond as Maya.

"""

        response = await self.ai.generate(
            prompt
        )

        ################################
        # STORE MEMORY
        ################################

        self.memory.add_memory(
            "user",
            text
        )

        self.memory.add_memory(
            "maya",
            response
        )

        ################################
        # BACKGROUND SEMANTIC STORE
        ################################

        if not self.health.high_memory():

            self.semantic.store(
                "user",
                text
            )

            self.semantic.store(
                "maya",
                response
            )

        return response

    ####################################
    # AUTONOMOUS LOOP
    ####################################

    async def autonomous_loop(self):

        while True:

            try:

                health = self.health.system_health()

                ################################
                # MEMORY PRESSURE
                ################################

                if health["memory_percent"] > 85:

                    print(

                        "[MAYA] "

                        "Memory pressure detected"

                    )

                ################################
                # DISK PRESSURE
                ################################

                if health["disk_percent"] > 90:

                    print(

                        "[MAYA] "

                        "Disk pressure detected"

                    )

            except Exception as e:

                print(e)

            await asyncio.sleep(300)
