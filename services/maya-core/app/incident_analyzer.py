from ai_gateway import AIGateway


class IncidentAnalyzer:

    def __init__(self):

        self.ai = AIGateway()

    def analyze(

        self,

        container_name,

        event_type,

        logs=""

    ):

        prompt = f"""

Analyze infrastructure incident.

Container:
{container_name}

Event:
{event_type}

Logs:
{logs}

Provide:
1. Root cause
2. Risk level
3. Recommended action
4. Is remediation safe

"""

        return self.ai.generate(
            prompt
        )
