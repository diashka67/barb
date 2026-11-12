"""python -m uvicorn file:app --reload"""
import csv
import hashlib
import logging
import os
import re
import secrets

from fastapi import Depends, FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware


#логер
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('sessions.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

SECRET_FILE = '.secret_key'


def get_or_create_secret() -> str:
    if os.path.exists(SECRET_FILE):
        with open(SECRET_FILE, 'r', encoding='utf-8') as f:
            key = f.read().strip()
            if key:
                return key
    new_key = secrets.token_hex(32)
    with open(SECRET_FILE, 'w', encoding='utf-8') as f:
        f.write(new_key)
    logger.info('Сгенерирован новый секретный ключ и сохранён в %s', SECRET_FILE)
    return new_key


SECRET_KEY = get_or_create_secret()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=1500, same_site='lax')

app.mount('/static', StaticFiles(directory='static'), name='static')
app.mount('/sources', StaticFiles(directory='sources'), name='sources')
templates = Jinja2Templates(directory='templates')

white_urls = ['/', '/home', '/login', '/logout', '/register', '/main', '/404', '/403', '/back']

File = 'user.csv'

ERROR_TEMPLATES = {
    403: '403.html',
    404: '404.html',
}

MIN_PASSWORD = 8
MAX_PASSWORD = 64
MIN_NAME = 2
MAX_NAME = 50


# Файлы
def read_users():
    if not os.path.exists(File):
        return []
    with open(File, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def add_user(name, email, password):
    new_file = not os.path.exists(File)
    with open(File, 'a', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(['name', 'email', 'password'])
        writer.writerow([name, email, hash_password(password)])


def find_user(email):
    for user in read_users():
        if user['email'] == email:
            return user
    return None


# Пароли
def make_hash(password, salt):
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()


def hash_password(password):
    salt = secrets.token_hex(8)
    return salt + '$' + make_hash(password, salt)


def check_password(password, saved):
    salt = saved.split('$')[0]
    return saved == salt + '$' + make_hash(password, salt)


def check_name(name):
    if len(name) < MIN_NAME:
        return f'Введите имя (минимум {MIN_NAME} символа)'
    if len(name) > MAX_NAME:
        return f'Имя слишком длинное (максимум {MAX_NAME} символов)'
    return None


def check_email(email):
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        return 'Некорректный email'
    return None


def check_password_strength(password):
    if len(password) < MIN_PASSWORD:
        return f'Пароль должен быть не короче {MIN_PASSWORD} символов'
    if len(password) > MAX_PASSWORD:
        return f'Пароль слишком длинный (не больше {MAX_PASSWORD} символов)'
    if not re.search(r'[A-Za-zА-Яа-яЁё]', password):
        return 'В пароле должна быть хотя бы одна буква'
    if not re.search(r'[0-9]', password):
        return 'В пароле должна быть хотя бы одна цифра'
    return None


# Сессии
active_sessions = set()


def start_session(request: Request, email):
    end_session(request)
    sid = secrets.token_hex(16)
    active_sessions.add(sid)
    request.session['sid'] = sid
    request.session['user_email'] = email
    logger.info('Сессия создана | email=%s | sid=%s...', email, sid[:8])


def end_session(request: Request):
    sid = request.session.get('sid')
    email = request.session.get('user_email')
    active_sessions.discard(sid)
    request.session.clear()
    if email:
        logger.info('Сессия завершена | email=%s | sid=%s', email, sid[:8] if sid else 'none')


def session_email(request: Request):
    sid = request.session.get('sid')
    email = request.session.get('user_email')
    if sid and sid not in active_sessions and email:
        logger.warning('Попытка использовать истекшую сессию | email=%s | sid=%s...', email, sid[:8])
    if sid in active_sessions and email:
        return email
    return None


def get_current_user(request: Request):
    email = session_email(request)
    if not email:
        logger.warning('Отказано в доступе | причина=нет_сессии | ip=%s', request.client.host)
        raise StarletteHTTPException(status_code=403, detail='Доступ запрещён')

    user = find_user(email)
    if user is None:
        logger.warning('Отказано в доступе | email=%s | причина=пользователь_удален', email)
        end_session(request)
        raise StarletteHTTPException(status_code=403, detail='Доступ запрещён')

    return user


def current_name(request: Request) -> str:
    email = session_email(request)
    if email:
        user = find_user(email)
        if user:
            return user['name']
    return 'красотка'


@app.middleware('http')
async def no_cache_for_pages(request: Request, call_next):
    response = await call_next(request)
    if response.headers.get('content-type', '').startswith('text/html'):
        response.headers['Cache-Control'] = 'no-store'
    return response


# Страницы
@app.get('/', response_class=HTMLResponse)
def main_page(request: Request):
    return templates.TemplateResponse(
        request=request, name='home.html',
        context={'username': current_name(request)}
    )


@app.get('/home', response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse(
        request=request, name='home.html',
        context={'username': current_name(request)}
    )


@app.get('/login', response_class=HTMLResponse)
def login_page(request: Request, registered: str = None, loggedout: str = None):
    notice = None
    if registered:
        notice = "Аккаунт создан, нужно войти"
    elif loggedout:
        notice = "Ты нажала «Назад», поэтому сессия закрыта. Войди снова "
    return templates.TemplateResponse(
        request=request, name='login.html',
        context={'notice': notice}
    )


@app.get('/register', response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name='register.html')


@app.get('/main', response_class=HTMLResponse)
def cabinet_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(
        request=request, name='main.html',
        context={'username': user['name']}
    )


@app.get('/logout')
def logout(request: Request):
    end_session(request)
    return RedirectResponse(url='/login', status_code=303)


@app.post('/back')
def pressed_back(request: Request):
    was_logged_in = session_email(request) is not None
    email = session_email(request)
    end_session(request)
    if was_logged_in:
        logger.info('Сессия закрыта по кнопке "Назад" | email=%s', email)
    return {'logged_out': was_logged_in}


@app.get('/404', response_class=HTMLResponse)
def oshibka_page(request: Request):
    return templates.TemplateResponse(
        request=request, name='404.html', status_code=404
    )


@app.get('/403', response_class=HTMLResponse)
def forbidden_page(request: Request):
    return templates.TemplateResponse(
        request=request, name='403.html', status_code=403
    )


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    template_name = ERROR_TEMPLATES.get(exc.status_code)

    if template_name:
        return templates.TemplateResponse(
            request=request,
            name=template_name,
            status_code=exc.status_code
        )

    return await http_exception_handler(request, exc)


# Регистрация и вход
@app.post('/register')
def register(request: Request,
            name: str = Form(...),
            email: str = Form(...),
            password: str = Form(...),
            confirm: str = Form(...)):
    name = name.strip()
    email = email.strip().lower()

    error = (check_name(name)
            or check_email(email)
            or check_password_strength(password)
            or (None if password == confirm else 'Пароли не совпадают')
            or ('Такой email уже зареган' if find_user(email) else None))

    if error:
        return templates.TemplateResponse(
            request=request, name='register.html',
            context={'error': error, 'name': name, 'email': email},
            status_code=400
        )

    add_user(name, email, password)
    logger.info('Новый пользователь зарегистрирован | email=%s | name=%s', email, name)
    return RedirectResponse(url='/login?registered=1', status_code=303)


@app.post('/login')
def login(request: Request,
        username: str = Form(...),
        password: str = Form(...)):
    user = find_user(username.strip().lower())

    if user is None or not check_password(password, user['password']):
        logger.warning('Неудачная попытка входа | email=%s | ip=%s', username, request.client.host)
        return templates.TemplateResponse(
            request=request, name='login.html',
            context={'error': 'Неверный email или пароль'}
        )

    logger.info('Успешный вход | email=%s', user['email'])
    start_session(request, user['email'])
    return RedirectResponse(url='/main', status_code=303)
