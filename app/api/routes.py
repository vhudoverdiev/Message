from fastapi import APIRouter

from schemas.flow import FlowData
from services.flow_service import flow_service

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    """Проверка, что сервер работает."""
    return {"status": "ok"}


@router.get("/flow", response_model=FlowData)
def get_flow() -> FlowData:
    """Получить текущий сценарий."""
    return flow_service.get_flow()


@router.post("/flow", response_model=FlowData)
def save_flow(flow_data: FlowData) -> FlowData:
    """Сохранить сценарий."""
    return flow_service.save_flow(flow_data)


@router.post("/flow/reset", response_model=FlowData)
def reset_flow() -> FlowData:
    """Сбросить сценарий к начальному шаблону."""
    return flow_service.reset_flow()


@router.post("/flow/publish", response_model=FlowData)
def publish_flow() -> FlowData:
    """Опубликовать сценарий."""
    return flow_service.publish_flow()
