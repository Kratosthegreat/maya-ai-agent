from super_agent import SuperAgentPlanner, PlanStep


def test_build_request_plan_has_default_steps():
    planner = SuperAgentPlanner()
    steps = planner.build_request_plan("help me organize tomorrow")
    assert len(steps) >= 4
    assert steps[0].title == "Clarify objective"


def test_daily_briefing_formats_values_and_timezone():
    planner = SuperAgentPlanner("Asia/Jerusalem")
    text = planner.build_daily_briefing({"pending": 3, "urgent": 1, "overdue": 0, "completed": 5})
    assert "Pending: 3" in text
    assert "Urgent: 1" in text
    assert "UTC" not in text


def test_format_plan_markdown_renders_steps():
    planner = SuperAgentPlanner()
    text = planner.format_plan_markdown([
        PlanStep("Step A", "Reason A", 3),
        PlanStep("Step B", "Reason B", 5),
    ])
    assert "Super-Agent Plan" in text
    assert "1. **Step A**" in text
    assert "2. **Step B**" in text


def test_should_show_plan_only_for_complex_messages():
    planner = SuperAgentPlanner()
    assert planner.should_show_plan("תכנני לי פגישה וגם מעקב לשבוע הבא") is True
    assert planner.should_show_plan("מה השעה?") is False
