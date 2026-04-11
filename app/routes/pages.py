from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates",
    context_processors=[]
)

stats = {
    "accounts": 8,
    "messages": 142,
    "clients": 54,
    "dialogs": 17
}

accounts = [
    {"name": "Main Shop", "status": "Активен", "token": "***"},
    {"name": "Support", "status": "Ошибка", "token": "***"},
]

clients = [
    {"name": "Иван", "vk": "vk.com/id1", "status": "Новый"},
    {"name": "Мария", "vk": "vk.com/id2", "status": "В работе"},
]

messages = [
    {"account": "Main Shop", "client": "Иван", "text": "Добрый день"},
    {"account": "Support", "client": "Мария", "text": "Спасибо"},
]

logs = [
    {"event": "Вход admin", "level": "INFO"},
    {"event": "Добавлен VK аккаунт", "level": "INFO"},
]


@router.get("/")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )


@router.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "admin":
        return RedirectResponse("/dashboard", status_code=303)
    return RedirectResponse("/", status_code=303)


@router.get("/dashboard")
def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"stats": stats}
    )


@router.get("/accounts")
def vk_accounts(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="accounts.html",
        context={"items": accounts}
    )


@router.get("/messages")
def inbox(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="messages.html",
        context={"items": messages}
    )


@router.get("/clients")
def customers(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="clients.html",
        context={"items": clients}
    )


@router.get("/logs")
def system_logs(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={"items": logs}
    )


@router.get("/settings")
def settings(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={}
    )
