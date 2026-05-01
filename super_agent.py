"""Super-agent planning utilities for Maya."""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List


@dataclass
class PlanStep:
    title: str
    reason: str
    eta_minutes: int


class SuperAgentPlanner:
    def __init__(self, timezone_name: str = "Asia/Jerusalem"):
        self.timezone_name = timezone_name

    """Build concise, actionable plans from user requests and tasks."""

    def should_show_plan(self, message: str) -> bool:
        msg = message.strip()
        if len(msg) > 90:
            return True
        keywords = ["and", "then", "also", "אחר כך", "וגם", "בנוסף", "דחוף", "שבוע", "פגישה"]
        return any(k in msg.lower() for k in keywords)

    def build_request_plan(self, message: str) -> List[PlanStep]:
        normalized = message.strip()
        steps = [
            PlanStep("Clarify objective", "Make sure success criteria are explicit", 2),
            PlanStep("Break into tasks", "Transform request into concrete subtasks", 5),
            PlanStep("Prioritize execution", "Do urgent/high-impact items first", 3),
            PlanStep("Follow-up summary", "Report done/pending/next step", 2),
        ]
        if any(k in normalized.lower() for k in ["meeting", "פגישה", "schedule", "תזמן"]):
            steps.insert(2, PlanStep("Prepare agenda", "Meeting requests need a focused agenda", 4))
        return steps

    def format_plan_markdown(self, steps: List[PlanStep]) -> str:
        lines = ["🧠 **Super-Agent Plan**"]
        for idx, step in enumerate(steps, 1):
            lines.append(f"{idx}. **{step.title}** — {step.reason} (~{step.eta_minutes}m)")
        return "\n".join(lines)

    def build_daily_briefing(self, summary: Dict) -> str:
        tz = ZoneInfo(self.timezone_name)
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M %Z")
        return (
            f"📅 **Daily Briefing ({now})**\n"
            f"• Pending: {summary.get('pending', 0)}\n"
            f"• Urgent: {summary.get('urgent', 0)}\n"
            f"• Overdue: {summary.get('overdue', 0)}\n"
            f"• Completed: {summary.get('completed', 0)}\n"
            "\n🎯 Next best action: complete one urgent item first."
        )
