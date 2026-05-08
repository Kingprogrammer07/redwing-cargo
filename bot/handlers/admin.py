"""
Admin handlers — admin panel operations.
"""
from __future__ import annotations

import logging
import os

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import ADMINS, UPLOADS_DIR
from bot.database import DatabaseManager
from bot.keyboards.inline import (
    get_admin_back_keyboard,
    get_admin_keyboard,
    get_cancel_keyboard,
    get_confirm_keyboard,
    get_flight_menu_keyboard,
    get_flights_list_keyboard,
    get_search_result_keyboard,
)
from bot.models import FlightConfig
from bot.services import (
    AdminServiceImpl,
    CargoServiceImpl,
    FlightConfigServiceImpl,
    ImportServiceImpl,
)
from bot.states import AdminState
from bot.utils.excel_parser import ExcelParser
from bot.utils.formatters import MessageFormatter

logger = logging.getLogger(__name__)

router = Router(name="admin")


def _is_admin(user_id: int) -> bool:
    return user_id in ADMINS


# ─── Upload: Start ─────────────────────────────────────────────────────────


@router.callback_query(F.data == "admin_upload")
async def on_admin_upload(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle 'Baza yuklash' — ask for Excel file."""
    if not _is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_file)
    await callback.answer()

    text = MessageFormatter.format_ask_excel()
    keyboard = get_cancel_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)


# ─── Upload: Receive File ──────────────────────────────────────────────────


@router.message(AdminState.waiting_for_file, F.document)
async def on_excel_file(message: Message, state: FSMContext) -> None:
    """Handle Excel file upload from admin."""
    if not message.document:
        await message.answer(
            "⚠️ Iltimos, fayl yuboring.",
            reply_markup=get_cancel_keyboard(),
        )
        return

    doc = message.document
    file_name = doc.file_name or ""
    if not file_name.lower().endswith((".xlsx", ".xls")):
        await message.answer(
            "⚠️ <b>Faqat .xlsx yoki .xls fayllar qabul qilinadi.</b>",
            reply_markup=get_cancel_keyboard(),
        )
        return

    # Download file
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    file_path = os.path.join(UPLOADS_DIR, doc.file_name or "upload.xlsx")

    try:
        await message.bot.download(file=doc.file_id, destination=file_path)
    except Exception as e:
        logger.error("File download error: %s", e)
        await message.answer(
            "❌ <b>Faylni yuklashda xatolik.</b>",
            reply_markup=get_admin_keyboard(),
        )
        await state.clear()
        return

    # Store file path, ask for flight name
    await state.update_data(uploaded_file=file_path)

    # Get current flight name if exists
    db = DatabaseManager()
    flight_service = FlightConfigServiceImpl(db)
    current = await flight_service.get_current_flight()
    current_name = current.name if current else ""

    await state.set_state(AdminState.waiting_for_flight_name)

    text = MessageFormatter.format_ask_flight_name(current_name)
    keyboard = get_cancel_keyboard()
    await message.answer(text, reply_markup=keyboard)


@router.message(AdminState.waiting_for_file)
async def on_non_file_in_upload(message: Message) -> None:
    await message.answer(
        "⚠️ Iltimos, Excel fayl yuboring.",
        reply_markup=get_cancel_keyboard(),
    )


# ─── Flight Name: Receive ──────────────────────────────────────────────────


@router.message(AdminState.waiting_for_flight_name)
async def on_flight_name_input(message: Message, state: FSMContext) -> None:
    """Handle flight name input after Excel upload."""
    if not message.text:
        await message.answer(
            "⚠️ Iltimos, reys nomini matn ko'rinishida kiriting.",
            reply_markup=get_cancel_keyboard(),
        )
        return

    flight_name = message.text.strip()
    if not flight_name:
        await message.answer(
            "⚠️ Reys nomi bo'sh bo'lishi mumkin emas.",
            reply_markup=get_cancel_keyboard(),
        )
        return

    # Get stored file path
    data = await state.get_data()
    file_path = data.get("uploaded_file", "")

    if not file_path or not os.path.exists(file_path):
        await message.answer(
            "❌ <b>Fayl topilmadi. Iltimos, qayta yuklang.</b>",
            reply_markup=get_admin_keyboard(),
        )
        await state.clear()
        return

    # Show processing
    processing_msg = await message.answer(
        f"⏳ <b>Fayl qayta ishlanmoqda...\n✈️ Reys: {flight_name}</b>"
    )

    # Import
    db = DatabaseManager()
    parser = ExcelParser()
    import_service = ImportServiceImpl(db, parser)

    try:
        result = await import_service.import_from_excel(file_path, flight_name)
    except FileNotFoundError:
        await processing_msg.edit_text(
            "❌ <b>Fayl topilmadi.</b>",
            reply_markup=get_admin_keyboard(),
        )
        await state.clear()
        return
    except Exception as e:
        logger.error("Import error: %s", e)
        await processing_msg.edit_text(
            f"❌ <b>Importda xatolik:</b>\n<code>{str(e)[:200]}</code>",
            reply_markup=get_admin_keyboard(),
        )
        await state.clear()
        return
    finally:
        await import_service.cleanup_file(file_path)

    # Save flight config
    flight_service = FlightConfigServiceImpl(db)
    await flight_service.set_flight(flight_name)

    # Show result
    text = MessageFormatter.format_import_result(result)
    keyboard = get_admin_keyboard()
    await processing_msg.edit_text(text, reply_markup=keyboard)
    await state.clear()


# ─── Flight Menu ───────────────────────────────────────────────────────────


@router.callback_query(F.data == "admin_flight")
async def on_admin_flight(callback: CallbackQuery) -> None:
    """Handle 'Reys nomi' button — show flight management menu."""
    if not _is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await callback.answer()

    db = DatabaseManager()
    flight_service = FlightConfigServiceImpl(db)
    config = await flight_service.get_current_flight()

    if config:
        text = MessageFormatter.format_current_flight(config)
    else:
        text = MessageFormatter.format_no_flight_set()

    keyboard = get_flight_menu_keyboard(config.name if config else "")
    await callback.message.edit_text(text, reply_markup=keyboard)


# ─── Edit Flight Name ──────────────────────────────────────────────────────


@router.callback_query(F.data == "admin_edit_flight")
async def on_admin_edit_flight(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Handle 'Reys nomini o'zgartirish' — ask for new flight name."""
    if not _is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_edit_flight_name)
    await callback.answer()

    db = DatabaseManager()
    flight_service = FlightConfigServiceImpl(db)
    current = await flight_service.get_current_flight()
    current_name = current.name if current else ""

    text = MessageFormatter.format_ask_flight_name(current_name)
    keyboard = get_cancel_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.message(AdminState.waiting_for_edit_flight_name)
async def on_edit_flight_name_input(
    message: Message, state: FSMContext
) -> None:
    """Handle new flight name input."""
    if not message.text:
        await message.answer(
            "⚠️ Iltimos, reys nomini kiriting.",
            reply_markup=get_cancel_keyboard(),
        )
        return

    flight_name = message.text.strip()
    if not flight_name:
        await message.answer(
            "⚠️ Reys nomi bo'sh bo'lishi mumkin emas.",
            reply_markup=get_cancel_keyboard(),
        )
        return

    db = DatabaseManager()
    flight_service = FlightConfigServiceImpl(db)
    await flight_service.set_flight(flight_name)

    text = MessageFormatter.format_flight_updated(flight_name)
    keyboard = get_admin_keyboard()
    await message.answer(text, reply_markup=keyboard)
    await state.clear()


# ─── List Flights ──────────────────────────────────────────────────────────


@router.callback_query(F.data == "admin_list_flights")
async def on_admin_list_flights(callback: CallbackQuery) -> None:
    """Handle 'Mavjud reyslar' — list all flights in database."""
    if not _is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await callback.answer()

    db = DatabaseManager()
    flights = await db.get_all_flights()

    if not flights:
        text = "📭 <b>Hozircha hech qanday reys ma'lumoti yo'q.</b>"
        keyboard = get_admin_back_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard)
        return

    lines = ["✈️ <b>Mavjud reyslar:</b>\n"]
    for i, flight in enumerate(flights, 1):
        stats = await db.get_flight_stats(flight)
        lines.append(f"{i}. <code>{flight}</code> — {stats['total']} ta yuk")

    text = "\n".join(lines)
    keyboard = get_admin_back_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)


# ─── Admin Track Search ────────────────────────────────────────────────────


@router.callback_query(F.data == "admin_search_track")
async def on_admin_search_track(
    callback: CallbackQuery, state: FSMContext
) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_track_search)
    await callback.answer()

    text = MessageFormatter.format_ask_track_code()
    keyboard = get_cancel_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.message(AdminState.waiting_for_track_search)
async def on_admin_track_input(message: Message, state: FSMContext) -> None:
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
        logger.error("Admin track search error: %s", e)
        await message.answer(
            "❌ <b>Xatolik yuz berdi.</b>",
            reply_markup=get_admin_keyboard(),
        )
        await state.clear()
        return

    if result.total_count == 0:
        text = MessageFormatter.format_not_found()
    else:
        text = MessageFormatter.format_multiple_results(
            result.items, is_admin=True
        )

    keyboard = get_search_result_keyboard(is_admin=True)
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(AdminState.waiting_for_track_search)


# ─── Admin Client Search ───────────────────────────────────────────────────


@router.callback_query(F.data == "admin_search_client")
async def on_admin_search_client(
    callback: CallbackQuery, state: FSMContext
) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_client_search)
    await callback.answer()

    text = MessageFormatter.format_ask_client_code()
    keyboard = get_cancel_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.message(AdminState.waiting_for_client_search)
async def on_admin_client_input(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer(
            "⚠️ Iltimos, matn ko'rinishida client kodini yuboring.",
            reply_markup=get_cancel_keyboard(),
        )
        return

    client_code = message.text.strip()
    if len(client_code) < 2:
        await message.answer(
            MessageFormatter.format_client_too_short(),
            reply_markup=get_cancel_keyboard(),
        )
        return

    db = DatabaseManager()
    service = CargoServiceImpl(db)

    try:
        result = await service.search_by_client(client_code)
    except ValueError as e:
        await message.answer(
            f"⚠️ <b>Xatolik:</b> {str(e)}",
            reply_markup=get_cancel_keyboard(),
        )
        return
    except Exception as e:
        logger.error("Admin client search error: %s", e)
        await message.answer(
            "❌ <b>Xatolik yuz berdi.</b>",
            reply_markup=get_admin_keyboard(),
        )
        await state.clear()
        return

    if result.total_count == 0:
        text = MessageFormatter.format_not_found()
    else:
        text = MessageFormatter.format_multiple_results(
            result.items, is_admin=True
        )

    keyboard = get_search_result_keyboard(is_admin=True)
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(AdminState.waiting_for_client_search)


# ─── Delete by Flight ──────────────────────────────────────────────────────


@router.callback_query(F.data == "admin_delete_flight")
async def on_admin_delete_flight(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Handle 'Reys o'chirish' — show flights list or ask for name."""
    if not _is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await callback.answer()

    db = DatabaseManager()
    flights = await db.get_all_flights()

    if not flights:
        text = (
            "📭 <b>Hozircha hech qanday reys ma'lumoti yo'q.</b>\n\n"
            "O'chirish uchun avval ma'lumot yuklang."
        )
        keyboard = get_admin_back_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard)
        return

    if len(flights) <= 10:
        # Show flights as inline buttons
        text = "🗑️ <b>O'chirish uchun reysni tanlang:</b>"
        keyboard = get_flights_list_keyboard(flights)
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        # Too many flights, ask to type
        await state.set_state(AdminState.waiting_for_delete_by_flight)
        text = MessageFormatter.format_ask_delete_flight()
        keyboard = get_cancel_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("del_flight:"))
async def on_delete_flight_selected(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Handle flight selected for deletion from inline buttons."""
    if not _is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    flight_name = callback.data.split(":", 1)[1]

    db = DatabaseManager()
    stats = await db.get_flight_stats(flight_name)
    count = stats.get("total", 0)

    if count == 0:
        await callback.answer("Bu reysda ma'lumot yo'q", show_alert=True)
        return

    # Store for confirmation
    await state.set_state(AdminState.waiting_for_confirm_delete_flight)
    await state.update_data(delete_flight=flight_name, delete_count=count)
    await callback.answer()

    text = MessageFormatter.format_confirm_delete_flight(flight_name, count)
    keyboard = get_confirm_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.message(AdminState.waiting_for_delete_by_flight)
async def on_delete_flight_input(message: Message, state: FSMContext) -> None:
    """Handle flight name typed for deletion."""
    if not message.text:
        await message.answer(
            "⚠️ Iltimos, reys nomini kiriting.",
            reply_markup=get_cancel_keyboard(),
        )
        return

    flight_name = message.text.strip()
    if not flight_name:
        await message.answer(
            "⚠️ Reys nomi bo'sh bo'lishi mumkin emas.",
            reply_markup=get_cancel_keyboard(),
        )
        return

    db = DatabaseManager()
    stats = await db.get_flight_stats(flight_name)
    count = stats.get("total", 0)

    if count == 0:
        await message.answer(
            f"❌ <b>'{flight_name}'</b> reysida ma'lumot topilmadi.",
            reply_markup=get_admin_keyboard(),
        )
        await state.clear()
        return

    await state.set_state(AdminState.waiting_for_confirm_delete_flight)
    await state.update_data(delete_flight=flight_name, delete_count=count)

    text = MessageFormatter.format_confirm_delete_flight(flight_name, count)
    keyboard = get_confirm_keyboard()
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "confirm_yes")
async def on_confirm_yes(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle confirmation yes — perform deletion."""
    if not _is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    data = await state.get_data()
    flight_name = data.get("delete_flight", "")

    if not flight_name:
        await callback.answer("Ma'lumot topilmadi", show_alert=True)
        await state.clear()
        return

    db = DatabaseManager()
    admin_service = AdminServiceImpl(db)

    try:
        deleted = await admin_service.delete_by_flight(flight_name)
        await callback.answer(f"{deleted} ta o'chirildi", show_alert=False)
        text = MessageFormatter.format_flight_deleted(flight_name, deleted)
    except Exception as e:
        logger.error("Delete flight error: %s", e)
        text = f"❌ <b>Xatolik:</b> {str(e)[:200]}"

    keyboard = get_admin_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.clear()


@router.callback_query(F.data == "confirm_no")
async def on_confirm_no(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle confirmation no — cancel."""
    await callback.answer("Bekor qilindi", show_alert=False)

    text = MessageFormatter.format_cancelled()
    keyboard = get_admin_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.clear()


# ─── Clear All DB ──────────────────────────────────────────────────────────


@router.callback_query(F.data == "admin_clear_db")
async def on_admin_clear_db(
    callback: CallbackQuery, state: FSMContext
) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_confirm_clear)
    await callback.answer()

    db = DatabaseManager()
    try:
        stats = await db.get_stats()
    except Exception:
        stats = {"total": 0}

    text = MessageFormatter.format_clear_confirm(stats.get("total", 0))
    keyboard = get_confirm_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)
