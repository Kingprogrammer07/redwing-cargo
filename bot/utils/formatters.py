"""
Telegram message formatters for cargo tracking results.
"""
from __future__ import annotations

from typing import List

from bot.config import ADMIN_CONTACT_URL, ADMIN_USERNAME
from bot.models import CargoItem, FlightConfig, ImportResult


_SEPARATOR: str = "\n━━━━━━━━━━━━━━━━━━━━\n"


def _escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _format_date(date_value) -> str:
    """Format a date value for display."""
    if hasattr(date_value, "strftime"):
        return date_value.strftime("%Y-%m-%d %H:%M:%S")
    return str(date_value)


def _flight_badge(flight_name: str) -> str:
    """Return flight badge or empty string."""
    if flight_name:
        return f"✈️ <b>Reys:</b> {_escape_html(flight_name)}\n"
    return ""


class MessageFormatter:
    """Format cargo items and other messages for Telegram."""

    # ─── User Messages ─────────────────────────────────────────────────────

    @staticmethod
    def format_user_result(item: CargoItem) -> str:
        """Format a single cargo item for regular users (without client code)."""
        flight = _flight_badge(item.flight_name)
        lines = [
            "🇨🇳 XITOY OMBORIDA",
            "",
            f"🔍 <b>Track kod:</b> <code>{_escape_html(item.track_code)}</code>",
            flight,
            f"📅 <b>Qabul qilingan:</b> {_format_date(item.received_date)}",
            f"📦 <b>Mahsulot (RU):</b> {_escape_html(item.product_name_ru)}",
            f"📦 <b>Mahsulot (CN):</b> {_escape_html(item.product_name_cn)}",
            f"⚖️ <b>Vazn:</b> {item.weight} kg",
            f"🔢 <b>Miqdor:</b> {item.quantity}",
            f"📦 <b>Quti raqami:</b> {_escape_html(item.box_number)}",
            "",
            "💡 Boshqa yukni tekshirish uchun keyingi track kodni yuboring.",
            "Jarayonni to'xtatish uchun ❌ <b>Bekor qilish</b> tugmasini bosing.",
        ]
        return "\n".join(lines)

    @staticmethod
    def format_admin_result(item: CargoItem) -> str:
        """Format a single cargo item for admin (with client code and flight)."""
        flight = _flight_badge(item.flight_name)
        lines = [
            "🇨🇳 XITOY OMBORIDA",
            "",
            f"🔍 <b>Track kod:</b> <code>{_escape_html(item.track_code)}</code>",
            f"👤 <b>Mijoz ID:</b> <code>{_escape_html(item.client_code)}</code>",
            flight,
            f"📅 <b>Qabul qilingan:</b> {_format_date(item.received_date)}",
            f"📦 <b>Mahsulot (RU):</b> {_escape_html(item.product_name_ru)}",
            f"📦 <b>Mahsulot (CN):</b> {_escape_html(item.product_name_cn)}",
            f"⚖️ <b>Vazn:</b> {item.weight} kg",
            f"🔢 <b>Miqdor:</b> {item.quantity}",
            f"📦 <b>Quti raqami:</b> {_escape_html(item.box_number)}",
            "",
            "💡 Boshqa yukni tekshirish uchun keyingi track kodni yuboring.",
        ]
        return "\n".join(lines)

    @staticmethod
    def format_multiple_results(
        items: List[CargoItem], is_admin: bool = False
    ) -> str:
        """Format multiple cargo items with separators."""
        if not items:
            return MessageFormatter.format_not_found()

        if len(items) == 1:
            if is_admin:
                return MessageFormatter.format_admin_result(items[0])
            return MessageFormatter.format_user_result(items[0])

        formatter = (
            MessageFormatter.format_admin_result
            if is_admin
            else MessageFormatter.format_user_result
        )
        parts = [formatter(item) for item in items]
        return _SEPARATOR.join(parts)

    @staticmethod
    def format_not_found() -> str:
        """Format 'not found' message."""
        return (
            "❌ <b>Ma'lumot topilmadi</b>\n\n"
            "Kiritilgan track kod bo'yicha hech qanday ma'lumot mavjud emas.\n\n"
            f"Muammoga duch kelsangiz, iltimos "
            f"<a href=\"{ADMIN_CONTACT_URL}\">@{ADMIN_USERNAME}</a> ga yozing."
        )

    @staticmethod
    def format_track_too_short() -> str:
        return (
            "⚠️ <b>Xato format</b>\n\n"
            "Track kod kamida 3 ta belgidan iborat bo'lishi kerak.\n"
            "Iltimos, to'g'ri track kodni kiriting."
        )

    @staticmethod
    def format_track_too_long() -> str:
        return (
            "⚠️ <b>Xato format</b>\n\n"
            "Track kod 100 ta belgidan oshmasligi kerak.\n"
            "Iltimos, to'g'ri track kodni kiriting."
        )

    @staticmethod
    def format_client_too_short() -> str:
        return (
            "⚠️ <b>Xato format</b>\n\n"
            "Client kod kamida 2 ta belgidan iborat bo'lishi kerak.\n"
            "Iltimos, to'g'ri client kodni kiriting."
        )

    # ─── Welcome Messages ──────────────────────────────────────────────────

    @staticmethod
    def format_welcome(full_name: str) -> str:
        return (
            f"👋 <b>Assalomu alaykum, {full_name}!</b>\n\n"
            "📦 <b>Redwing Cargo</b> botiga xush kelibsiz!\n\n"
            "🚚 <i>Bu yerda siz o'zingizning yuklaringiz haqida ma'lumot olishingiz mumkin.</i>\n\n"
            "👇 Kerakli bo'limni tanlang:"
        )

    @staticmethod
    def format_admin_welcome(full_name: str) -> str:
        return (
            f"👋 <b>Assalomu alaykum, Admin {full_name}!</b>\n\n"
            "🔧 <b>Admin paneliga xush kelibsiz!</b>\n\n"
            "👇 Kerakli amalni tanlang:"
        )

    # ─── Import Result ─────────────────────────────────────────────────────

    @staticmethod
    def format_import_result(result: ImportResult) -> str:
        lines = [
            "✅ <b>Import muvaffaqiyatli yakunlandi!</b>",
            "",
            f"📊 <b>Jami qatorlar:</b> {result.total_rows}",
            f"✅ <b>Import qilindi:</b> {result.imported}",
            f"⏭️ <b>O'tkazib yuborildi:</b> {result.skipped}",
        ]
        if result.flight_name:
            lines.append(f"✈️ <b>Reys:</b> <code>{_escape_html(result.flight_name)}</code>")
        if result.errors:
            lines.extend(["", f"⚠️ <b>Xatolar ({len(result.errors)}):</b>"])
            for i, err in enumerate(result.errors[:5], 1):
                lines.append(f"  {i}. {err[:100]}")
            if len(result.errors) > 5:
                lines.append(f"  ... va yana {len(result.errors) - 5} ta")
        return "\n".join(lines)

    @staticmethod
    def format_ask_flight_name(current: str = "") -> str:
        """Message asking admin to enter a flight name."""
        text = (
            "✈️ <b>Reys nomini kiriting</b>\n\n"
            "Yuklangan ma'lumotlarga qaysi reys nomini biriktirmoqchisiz?\n"
            "Masalan: <code>M2 JET</code>, <code>M205</code>\n\n"
        )
        if current:
            text += f"📝 <b>Joriy reys:</b> <code>{_escape_html(current)}</code>\n\n"
        text += "✏️ Yangi reys nomini kiriting:"
        return text

    @staticmethod
    def format_flight_updated(name: str) -> str:
        return (
            f"✅ <b>Reys nomi yangilandi!</b>\n\n"
            f"✈️ Joriy reys: <code>{_escape_html(name)}</code>"
        )

    @staticmethod
    def format_ask_track_code() -> str:
        return (
            "🔍 <b>Track kodini kiriting</b>\n\n"
            "Iltimos, tekshirish uchun track kodni yuboring:\n"
            "(kamida 3 ta belgi)"
        )

    @staticmethod
    def format_ask_client_code() -> str:
        return (
            "👤 <b>Client kodini kiriting</b>\n\n"
            "Iltimos, qidirish uchun client kodini yuboring:\n"
            "(kamida 2 ta belgi)"
        )

    @staticmethod
    def format_ask_excel() -> str:
        return (
            "📁 <b>Excel faylni yuklang</b>\n\n"
            "Iltimos, .xlsx formatidagi Excel faylni yuboring.\n"
        )

    @staticmethod
    def format_ask_delete_flight() -> str:
        return (
            "🗑️ <b>Reys bo'yicha o'chirish</b>\n\n"
            "O'chirish uchun reys nomini kiriting:\n"
            "Masalan: <code>M2 JET</code>\n\n"
            "⚠️ Bu reysga tegishli barcha ma'lumotlar o'chiriladi!"
        )

    @staticmethod
    def format_confirm_delete_flight(flight_name: str, count: int) -> str:
        return (
            "⚠️ <b>Tasdiqlash</b>\n\n"
            f"Reys: <code>{_escape_html(flight_name)}</code>\n"
            f"Yuklar soni: <b>{count}</b> ta\n\n"
            "Shu reysga tegishli barcha ma'lumotlar o'chiriladi!\n"
            "Ishonchingiz komilmi?"
        )

    @staticmethod
    def format_clear_confirm(total: int = 0) -> str:
        return (
            "⚠️ <b>Ogohlantirish!</b>\n\n"
            f"Bazada <b>{total}</b> ta yuk ma'lumoti bor.\n"
            "Barcha ma'lumotlar o'chiriladi!\n\n"
            "Ishonchingiz komilmi?"
        )

    @staticmethod
    def format_db_cleared(deleted: int = 0) -> str:
        return (
            "🗑️ <b>Baza tozalandi!</b>\n\n"
            f"O'chirilgan yuklar: <b>{deleted}</b>"
        )

    @staticmethod
    def format_flight_deleted(flight_name: str, count: int) -> str:
        return (
            "✅ <b>Reys ma'lumotlari o'chirildi!</b>\n\n"
            f"✈️ Reys: <code>{_escape_html(flight_name)}</code>\n"
            f"🗑️ O'chirilgan: <b>{count}</b> ta yuk"
        )

    @staticmethod
    def format_cancelled() -> str:
        return "❌ <b>Amal bekor qilindi.</b>"

    # ─── Admin Info ────────────────────────────────────────────────────────

    @staticmethod
    def format_current_flight(config: FlightConfig) -> str:
        updated = ""
        if config.updated_at:
            updated = f"\n🕐 <b>Yangilangan:</b> {_format_date(config.updated_at)}"
        return (
            f"✈️ <b>Joriy reys ma'lumoti</b>{updated}\n\n"
            f"Reys nomi: <code>{_escape_html(config.name)}</code>"
        )

    @staticmethod
    def format_no_flight_set() -> str:
        return (
            "⚠️ <b>Reys nomi sozlanmagan</b>\n\n"
            "Hozircha reys nomi kiritilmagan.\n"
            "Iltimos, avval reys nomini kiriting."
        )

    @staticmethod
    def format_admins_list(admins: List[int]) -> str:
        lines = ["👨‍💼 <b>Adminlar ro'yxati</b>\n"]
        for i, admin_id in enumerate(admins, 1):
            lines.append(f"{i}. <code>{admin_id}</code>")
        return "\n".join(lines)
