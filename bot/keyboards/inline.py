"""
Inline keyboard builders for the bot.
"""
from __future__ import annotations

from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import ADMIN_CONTACT_URL, ADMIN_USERNAME


# ─── User Keyboards ────────────────────────────────────────────────────────


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard for regular users."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔍 Track kod tekshirish",
                    callback_data="check_track",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👨‍💼 Admin",
                    callback_data="admin_contact",
                ),
            ],
        ],
    )


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Cancel keyboard to abort current operation."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="cancel",
                ),
            ],
        ],
    )


def get_admin_contact_keyboard() -> InlineKeyboardMarkup:
    """Admin contact keyboard with URL button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"@{ADMIN_USERNAME}",
                    url=ADMIN_CONTACT_URL,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Orqaga",
                    callback_data="back_to_main",
                ),
            ],
        ],
    )


# ─── Admin Keyboards ───────────────────────────────────────────────────────


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Admin panel main keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📁 Baza yuklash",
                    callback_data="admin_upload",
                ),
                InlineKeyboardButton(
                    text="✈️ Reys nomi",
                    callback_data="admin_flight",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔍 Track qidirish",
                    callback_data="admin_search_track",
                ),
                InlineKeyboardButton(
                    text="👤 Client qidirish",
                    callback_data="admin_search_client",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗑️ Reys o'chirish",
                    callback_data="admin_delete_flight",
                ),
                InlineKeyboardButton(
                    text="🧹 Baza tozalash",
                    callback_data="admin_clear_db",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Asosiy menyu",
                    callback_data="back_to_main",
                ),
            ],
        ],
    )


def get_flight_menu_keyboard(current_name: str = "") -> InlineKeyboardMarkup:
    """Flight management keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                text="📝 Reys nomini o'zgartirish",
                callback_data="admin_edit_flight",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📋 Mavjud reyslar",
                callback_data="admin_list_flights",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Orqaga",
                callback_data="admin_back",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Orqaga",
                    callback_data="back_to_main",
                ),
            ],
        ],
    )


def get_admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Admin panel",
                    callback_data="admin_back",
                ),
            ],
        ],
    )


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirmation keyboard (Yes/No)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ha",
                    callback_data="confirm_yes",
                ),
                InlineKeyboardButton(
                    text="❌ Yo'q",
                    callback_data="confirm_no",
                ),
            ],
        ],
    )


def get_search_result_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Keyboard shown after search results."""
    buttons = [
        [
            InlineKeyboardButton(
                text="❌ Bekor qilish",
                callback_data="cancel",
            ),
        ],
    ]
    if is_admin:
        buttons[0].append(
            InlineKeyboardButton(
                text="🔙 Admin panel",
                callback_data="admin_back",
            ),
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_flights_list_keyboard(flights: List[str]) -> InlineKeyboardMarkup:
    """Keyboard with flight names as buttons for deletion."""
    buttons = []
    for flight in flights:
        buttons.append([
            InlineKeyboardButton(
                text=f"✈️ {flight}",
                callback_data=f"del_flight:{flight}",
            ),
        ])
    buttons.append([
        InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data="admin_back",
        ),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
