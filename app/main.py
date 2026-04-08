from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.routers import controllers
import os

app = FastAPI()

# =========================
# CONFIG
# =========================

SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    https_only=False, 
    same_site="lax"
)

# =========================
# STATIC FILES
# =========================

if not os.path.exists("app/static"):
    os.makedirs("app/static")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# =========================
# TEMPLATES
# =========================

templates = Jinja2Templates(directory="app/templates")

# =========================
# ROUTERS
# =========================

app.include_router(controllers.router)

# =========================
# ROLE REDIRECT MAP
# =========================

ROLE_REDIRECT = {
    "admin": "/admin/dashboard",
    "coordinator": "/coordinator/dashboard",
    "tutor": "/tutor/dashboard",
}

# =========================
# DEPENDENCY
# =========================

def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user

# =========================
# ROOT
# =========================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = request.session.get("user")

    if user:
        role = user.get("role")

        if role in ROLE_REDIRECT:
            return RedirectResponse(
                ROLE_REDIRECT[role],
                status_code=302
            )

        # student mặc định
        return templates.TemplateResponse(
            "dashboard.html",
            {"request": request, "user": user}
        )

    return templates.TemplateResponse(
        "index.html",   
        {"request": request, "user": user}
    )

# =========================
# STUDENT DASHBOARD
# =========================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user=Depends(get_current_user)
):
    role = user.get("role")

    if role in ROLE_REDIRECT:
        return RedirectResponse(
            ROLE_REDIRECT[role],
            status_code=302
        )

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user}
    )

# =========================
# MY TUTORS PAGE
# =========================

@app.get("/my_tutors", response_class=HTMLResponse)
async def my_tutors_page(
    request: Request,
    user=Depends(get_current_user)
):
    if user.get("role") != "student":
        return RedirectResponse("/", status_code=302)

    return templates.TemplateResponse(
        "my_tutors.html",
        {"request": request, "user": user}
    )
