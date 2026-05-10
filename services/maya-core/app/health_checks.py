import requests

class HealthChecks:

    def check(

        self,

        container_name

    ):

        try:

            # ─────────────────────────
            # QDRANT
            # ─────────────────────────

            if container_name == "ai_qdrant":

                r = requests.get(

                    "http://ai_qdrant:6333",

                    timeout=5

                )

                return r.status_code == 200

            # ─────────────────────────
            # OPENWEBUI
            # ─────────────────────────

            if container_name == "ai_openwebui":

                r = requests.get(

                    "http://ai_openwebui:8080",

                    timeout=5

                )

                return r.status_code == 200

            # ─────────────────────────
            # OLLAMA
            # ─────────────────────────

            if container_name == "ai_ollama":

                r = requests.get(

                    "http://ai_ollama:11434",

                    timeout=5

                )

                return r.status_code == 200

            return True

        except Exception:

            return False
