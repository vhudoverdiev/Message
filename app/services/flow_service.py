import json
from copy import deepcopy
from pathlib import Path

from core.config import settings
from schemas.flow import FlowData


DEFAULT_FLOW = {
    "flow_name": "Call Center",
    "is_published": False,
    "steps": [
        {
            "id": "step-incoming",
            "type": "incoming",
            "title": "Incoming call",
            "description": "+31 6 12312345",
        },
        {
            "id": "step-tts",
            "type": "tts",
            "title": "Text-to-speech",
            "description": "Welcome to the Flow Builder. To continue, press 6.",
        },
        {
            "id": "step-sound",
            "type": "sound",
            "title": "Play Sound File",
            "description": "wait_muzak.wav",
        },
        {
            "id": "step-forward",
            "type": "forward",
            "title": "Forward Call",
            "description": "Forward call to selected number",
        },
        {
            "id": "step-if",
            "type": "if",
            "title": "If",
            "description": "If the caller presses 6 → Then ...",
        },
        {
            "id": "step-record",
            "type": "record",
            "title": "Record Call Audio",
            "description": "Record the user's message",
        },
        {
            "id": "step-url",
            "type": "url",
            "title": "Fetch call flow from URL",
            "description": "https://www.messagebird.com/flow",
        },
        {
            "id": "step-pause",
            "type": "pause",
            "title": "Pause",
            "description": "10 seconds",
        },
        {
            "id": "step-end",
            "type": "end",
            "title": "End Call",
            "description": "Scenario completed",
        },
    ],
}


class FlowService:
    """Сервис для чтения и сохранения сценария."""

    def __init__(self, flow_file: Path) -> None:
        self.flow_file = flow_file
        self._ensure_data_file_exists()

    def _ensure_data_file_exists(self) -> None:
        """Создаем файл сценария, если его еще нет."""
        settings.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.flow_file.exists():
            self.reset_flow()

    def get_flow(self) -> FlowData:
        """Возвращаем текущий сценарий из JSON-файла."""
        with self.flow_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return FlowData(**data)

    def save_flow(self, flow_data: FlowData) -> FlowData:
        """Сохраняем новый сценарий в JSON-файл."""
        with self.flow_file.open("w", encoding="utf-8") as file:
            json.dump(flow_data.model_dump(), file, ensure_ascii=False, indent=2)

        return flow_data

    def reset_flow(self) -> FlowData:
        """Сбрасываем сценарий к начальному шаблону."""
        default_data = FlowData(**deepcopy(DEFAULT_FLOW))
        return self.save_flow(default_data)

    def publish_flow(self) -> FlowData:
        """Отмечаем сценарий как опубликованный."""
        current_flow = self.get_flow()
        current_flow.is_published = True
        return self.save_flow(current_flow)


flow_service = FlowService(settings.flow_file)
