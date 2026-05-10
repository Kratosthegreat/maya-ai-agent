import os
import logging
import requests

from dotenv import load_dotenv

from personality import (
    SYSTEM_PERSONALITY
)

load_dotenv('/app/.env')

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
).strip()

MODEL = "gemini-2.5-flash"


class AIGateway:

    def __init__(self):

        self.base_url = (
            "https://generativelanguage.googleapis.com/v1beta"
        )

    def generate(

        self,

        prompt,

        temperature=0.4

    ):

        try:

            full_prompt = f"""

{SYSTEM_PERSONALITY}

{prompt}

"""

            url = (

                f"{self.base_url}"

                f"/models/{MODEL}:generateContent"

                f"?key={GEMINI_API_KEY}"

            )

            payload = {

                "contents": [

                    {

                        "parts": [

                            {

                                "text": full_prompt

                            }

                        ]

                    }

                ],

                "generationConfig": {

                    "temperature": temperature

                }

            }

            response = requests.post(

                url,

                json=payload,

                timeout=120

            )

            response.raise_for_status()

            data = response.json()

            return (

                data["candidates"][0]

                ["content"]["parts"][0]

                ["text"]

            )

        except Exception as e:

            logger.exception(e)

            return f"AI Error: {e}"
