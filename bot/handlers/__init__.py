"""
Handler router registration.
"""
from __future__ import annotations

from aiogram import Dispatcher

from bot.handlers.admin import router as admin_router
from bot.handlers.common import router as common_router
from bot.handlers.user import router as user_router


def register_handlers(dp: Dispatcher) -> None:
    """Register all routers with the dispatcher.
    
    Order: common first, then user, then admin.
    """
    dp.include_router(common_router)
    dp.include_router(user_router)
    dp.include_router(admin_router)
