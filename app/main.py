from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.routers import controllers
from app.database import engine, Base
import os

# Create DB Tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Mount Static Folder
if not os.path.exists("app/static"):
    os.makedirs("app/static")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configuration
app.add_middleware(SessionMiddleware, secret_key="SUPER_SECRET_KEY")

# Templates Configuration
templates = Jinja2Templates(directory="app/templates")

# Register Routers
app.include_router(controllers.router)

# --- Global/Root Routes ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Landing page logic:
    - Admin -> /admin/dashboard
    - Coordinator -> /coordinator/dashboard
    - Tutor -> /tutor/dashboard
    - Student -> /dashboard
    """
    user = request.session.get("user")
    if user:
        role = user.get('role')
        if role == 'admin':
            return RedirectResponse("/admin/dashboard")
        elif role == 'coordinator':
            return RedirectResponse("/coordinator/dashboard")
        elif role == 'tutor':
            return RedirectResponse("/tutor/dashboard")
        else:
            # Default to student dashboard
            return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})
    
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Route specifically for Student Dashboard.
    If a tutor tries to access this, redirect them to their own dashboard.
    """
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/")
    
    role = user.get('role')
    if role == 'tutor':
        return RedirectResponse("/tutor/dashboard")
    if role == 'admin':
        return RedirectResponse("/admin/dashboard")
    if role == 'coordinator':
        return RedirectResponse("/coordinator/dashboard")
        
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.get("/my_tutors", response_class=HTMLResponse)
async def my_tutors_page(request: Request):
    """
    Trang "Tutor của tôi" – chỉ sinh viên được vào
    """
    user = request.session.get("user")
    if not user or user.get("role") != "student":
        return RedirectResponse("/")  # hoặc "/dashboard"
    
    return templates.TemplateResponse(
        "my_tutors.html",
        {"request": request, "user": user}
    )