"""
Common handlers — /start command and shared callbacks.
"""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import ADMINS
from bot.database import DatabaseManager
from bot.keyboards.inline import (
    get_admin_contact_keyboard,
    get_admin_keyboard,
    get_main_keyboard,
)
from bot.services import FlightConfigServiceImpl
from bot.states import AdminState, UserState
from bot.utils.formatters import MessageFormatter

logger = logging.getLogger(__name__)

router = Router(name="common")


def _is_admin(user_id: int) -> bool:
    """Check if user ID is in the admins list."""
    return user_id in ADMINS


# ─── /start Command ────────────────────────────────────────────────────────


@router.message(CommandStart())
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Handle /start command. Shows different keyboard for admin vs user."""
    await state.clear()

    user_id = message.from_user.id if message.from_user else 0
    full_name = message.from_user.full_name if message.from_user else "Foydalanuvchi"

    if _is_admin(user_id):
        text = MessageFormatter.format_admin_welcome(full_name)
        keyboard = get_admin_keyboard()
    else:
        text = MessageFormatter.format_welcome(full_name)
        keyboard = get_main_keyboard()

    await message.answer(text, reply_markup=keyboard)


# ─── Cancel Callback ───────────────────────────────────────────────────────


@router.callback_query(F.data == "cancel")
async def on_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle cancel button — clear state and show main menu."""
    await state.clear()
    await callback.answer("Bekor qilindi", show_alert=False)

    user_id = callback.from_user.id if callback.from_user else 0
    text = MessageFormatter.format_cancelled()
    keyboard = get_admin_keyboard() if _is_admin(user_id) else get_main_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)


# ─── Back to Main Callback ─────────────────────────────────────────────────


@router.callback_query(F.data == "back_to_main")
async def on_back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle back button — show main menu based on user type."""
    await state.clear()

    user_id = callback.from_user.id if callback.from_user else 0

    if _is_admin(user_id):
        keyboard = get_admin_keyboard()
        text = "👇 Kerakli amalni tanlang:"
    else:
        keyboard = get_main_keyboard()
        text = "👇 Kerakli bo'limni tanlang:"

    await callback.message.edit_text(text, reply_markup=keyboard)


# ─── Admin Contact Callback ────────────────────────────────────────────────


@router.callback_query(F.data == "admin_contact")
async def on_admin_contact(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle admin contact button — show admin contact info."""
    await state.clear()
    await callback.answer()

    text = (
        "👨‍💼 <b>Admin bilan bog'lanish</b>\n\n"
        "Savol va takliflar uchun admin bilan bog'laning:\n\n"
        "👉 Tugmani bosib, to'g'ridan-to'g'ri yozing."
    )
    keyboard = get_admin_contact_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)


# ─── Admin Back Callback ───────────────────────────────────────────────────


@router.callback_query(F.data == "admin_back")
async def on_admin_back(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle admin panel back button."""
    await state.clear()
    await callback.answer()

    text = "👇 Kerakli amalni tanlang:"
    keyboard = get_admin_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)
