from typing import List, Literal

from pydantic import BaseModel, Field


StepType = Literal[
    "incoming",
    "tts",
    "sound",
    "if",
    "forward",
    "record",
    "url",
    "pause",
    "end",
]


class FlowStep(BaseModel):
    id: str = Field(..., description="Уникальный идентификатор шага")
    type: StepType = Field(..., description="Тип шага")
    title: str = Field(..., description="Название шага")
    description: str = Field(..., description="Краткое описание шага")


class FlowData(BaseModel):
    flow_name: str = Field(..., description="Название сценария")
    is_published: bool = Field(default=False, description="Опубликован ли сценарий")
    steps: List[FlowStep] = Field(default_factory=list, description="Список шагов")
