from incident_analyzer import IncidentAnalyzer

analyzer = IncidentAnalyzer()

result = analyzer.analyze(

    container_name="ai_qdrant",

    event_type="container_restart",

    logs="""
connection timeout
memory allocation failed
container restarted automatically
"""

)

print(result)
