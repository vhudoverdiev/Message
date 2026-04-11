from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import authenticate_user
from app.services.log_service import write_log

router = APIRouter()
templates = Jinja2Templates(directory='app/templates')


@router.get('/')
def login_page(request: Request):
    if request.session.get('user_id'):
        return RedirectResponse('/dashboard', status_code=303)
    return templates.TemplateResponse('login.html', {'request': request, 'error': None})


@router.post('/login')
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse('login.html', {'request': request, 'error': 'Неверный логин или пароль'})

    request.session['user_id'] = user.id
    write_log(db, action='LOGIN', details=f'Пользователь {user.username} выполнил вход', user_id=user.id)
    return RedirectResponse('/dashboard', status_code=303)


@router.post('/logout')
def logout(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get('user_id')
    request.session.clear()
    if user_id:
        write_log(db, action='LOGOUT', details='Пользователь вышел из системы', user_id=user_id)
    return RedirectResponse('/', status_code=303)
