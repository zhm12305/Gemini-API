from app.api.routes import router, init_router
from app.api.dashboard import dashboard_router, init_dashboard_router
from app.api.user_auth import user_router

__all__ = [
    'router',
    'init_router',
    'dashboard_router',
    'init_dashboard_router',
    'user_router',
]
