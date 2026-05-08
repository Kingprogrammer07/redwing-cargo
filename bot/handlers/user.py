"""
User handlers — track code search flow.
"""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import ADMINS
from bot.database import DatabaseManager
from bot.keyboards.inline import (
    get_cancel_keyboard,
    get_main_keyboard,
    get_search_result_keyboard,
)
from bot.services import CargoServiceImpl
from bot.states import UserState
from bot.utils.formatters import MessageFormatter

logger = logging.getLogger(__name__)

router = Router(name="user")


# ─── Track Code Check Callback ─────────────────────────────────────────────


@router.callback_query(F.data == "check_track")
async def on_check_track(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle 'Track kod tekshirish' button — enter search state."""
    await state.set_state(UserState.waiting_for_track)
    await callback.answer()

    text = MessageFormatter.format_ask_track_code()
    keyboard = get_cancel_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)


# ─── Track Code Input ──────────────────────────────────────────────────────


@router.message(UserState.waiting_for_track)
async def on_track_input(message: Message, state: FSMContext) -> None:
    """Handle track code input from user."""
    if not message.text:
        await message.answer(
            "⚠️ Iltimos, matn ko'rinishida track kodni yuboring.",
            reply_markup=get_cancel_keyboard(),
        )
        return

    track_code = message.text.strip()
    from bot.config import MAX_TRACK_LENGTH, MIN_TRACK_LENGTH

    if len(track_code) < MIN_TRACK_LENGTH:
        await message.answer(
            MessageFormatter.format_track_too_short(),
            reply_markup=get_cancel_keyboard(),
        )
        return

    if len(track_code) > MAX_TRACK_LENGTH:
        await message.answer(
            MessageFormatter.format_track_too_long(),
            reply_markup=get_cancel_keyboard(),
        )
        return

    # Search
    db = DatabaseManager()
    service = CargoServiceImpl(db)

    try:
        result = await service.search_by_track(track_code)
    except ValueError as e:
        await message.answer(
            f"⚠️ <b>Xatolik:</b> {str(e)}",
            reply_markup=get_cancel_keyboard(),
        )
        return
    except Exception as e:
        logger.error("Track search error: %s", e)
        await message.answer(
            "❌ <b>Xatolik yuz berdi.</b>\n\n"
            "Muammoga duch kelsangiz, iltimos @MUSTAFOYEV_ANVAR ga yozing.",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        return

    if result.total_count == 0:
        text = MessageFormatter.format_not_found()
        keyboard = get_cancel_keyboard()
    else:
        text = MessageFormatter.format_multiple_results(result.items, is_admin=False)
        keyboard = get_search_result_keyboard(is_admin=False)

    await message.answer(text, reply_markup=keyboard)
    await state.set_state(UserState.waiting_for_track)


# ─── Cancel in User State ──────────────────────────────────────────────────


@router.callback_query(F.data == "cancel", UserState.waiting_for_track)
async def on_cancel_user(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle cancel while in user track search state."""
    await state.clear()
    await callback.answer("Bekor qilindi", show_alert=False)

    text = MessageFormatter.format_cancelled()
    keyboard = get_main_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)
