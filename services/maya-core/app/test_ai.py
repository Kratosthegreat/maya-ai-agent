from ai_gateway import AIGateway

ai = AIGateway()

result = ai.generate(

    """

    You are Maya AI.

    Explain your role in one sentence.

    """

)

print(result)
