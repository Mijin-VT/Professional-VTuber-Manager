"""UI widgets package — CustomTkinter version."""

from app.widgets.model_selection import ModelSelectionPage
from app.widgets.chat_widget import ChatPage
from app.widgets.tasks_widget import TasksPage
from app.widgets.calendar_widget import CalendarPage
from app.widgets.stream_planning import PlanningPage
from app.widgets.metrics_widget import MetricsPage
from app.widgets.settings_widget import SettingsPage

__all__ = [
    "ModelSelectionPage",
    "ChatPage",
    "TasksPage",
    "CalendarPage",
    "PlanningPage",
    "MetricsPage",
    "SettingsPage",
]
