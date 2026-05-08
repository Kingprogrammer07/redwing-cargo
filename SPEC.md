# SPEC.md — Cargo Tracker Telegram Bot

## Overview
A professional Telegram bot for cargo tracking using aiogram 3.x, aiosqlite, and openpyxl.
Admin ID: `777967425`

## Architecture
```
bot/
├── __init__.py
├── config.py              # Settings, env vars, constants
├── models.py              # Pydantic models for cargo items
├── database.py            # Async SQLite operations + migrations
├── services.py            # Business logic layer (SOLID)
├── states.py              # aiogram FSM states
├── handlers/
│   ├── __init__.py        # Router registration
│   ├── common.py          # /start, cancel
│   ├── user.py            # Track search for users
│   └── admin.py           # Upload Excel, admin search
├── keyboards/
│   ├── __init__.py
│   └── inline.py          # All inline keyboards
├── utils/
│   ├── __init__.py
│   ├── excel_parser.py    # Parse uploaded Excel files
│   └── formatters.py      # Message formatting
├── main.py                # Bot entry point
data/
├── cargo.db               # SQLite database
uploads/                   # Temporary Excel uploads
requirements.txt
.env
```

## 1. config.py
- `BOT_TOKEN`: from env `BOT_TOKEN` (required)
- `ADMIN_ID`: `777967425` (int)
- `DATABASE_PATH`: `"data/cargo.db"`
- `UPLOADS_DIR`: `"uploads"`
- `MIN_TRACK_LENGTH`: `3`
- `MAX_TRACK_LENGTH`: `100`

## 2. models.py — Pydantic models
```python
class CargoItem(BaseModel):
    id: Optional[int] = None
    received_date: datetime
    track_code: str
    product_name_cn: str
    product_name_ru: str
    quantity: int
    weight: float
    client_code: str
    box_number: str

    class Config:
        from_attributes = True

class TrackSearchResult(BaseModel):
    items: List[CargoItem]
    total_count: int

class ClientSearchResult(BaseModel):
    items: List[CargoItem]
    total_count: int
```

## 3. database.py
`class DatabaseManager:`
- `async def init_db()` — Create tables, indexes
- `async def migrate()` — Run migrations if needed
- `async def insert_cargo_items(items: List[CargoItem])` — Batch insert with `INSERT OR REPLACE` (track_code is UNIQUE)
- `async def find_by_track_code(track_code: str) -> List[CargoItem]`
- `async def find_by_client_code(client_code: str) -> List[CargoItem]`
- `async def delete_all_items()` — Clear all cargo_items
- `async def get_stats() -> dict` — total count

### SQL Schema
```sql
CREATE TABLE IF NOT EXISTS cargo_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    received_date TEXT NOT NULL,
    track_code TEXT NOT NULL UNIQUE,
    product_name_cn TEXT NOT NULL,
    product_name_ru TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    weight REAL NOT NULL DEFAULT 0,
    client_code TEXT NOT NULL,
    box_number TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_track_code ON cargo_items(track_code);
CREATE INDEX IF NOT EXISTS idx_client_code ON cargo_items(client_code);
```

## 4. states.py — FSM States
```python
class UserState(StatesGroup):
    waiting_for_track = State()

class AdminState(StatesGroup):
    waiting_for_file = State()
    waiting_for_track_search = State()
    waiting_for_client_search = State()
```

## 5. keyboards/inline.py
```python
def get_main_keyboard() -> InlineKeyboardMarkup:
    # [Track kod tekshirish] [Admin]

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    # [Bekor qilish]

def get_admin_keyboard() -> InlineKeyboardMarkup:
    # [Baza yuklash] [Track qidirish] [Client qidirish] [Bazani tozalash] [Orqaga]

def get_back_keyboard() -> InlineKeyboardMarkup:
    # [Orqaga]

def get_admin_contact_keyboard(username: str) -> InlineKeyboardMarkup:
    # URL button: @MUSTAFOYEV_ANVAR
```

## 6. utils/excel_parser.py
`class ExcelParser:`
- `async def parse_file(file_path: str) -> List[CargoItem]`
- Columns: A=received_date, B=track_code, C=product_name_cn, D=product_name_ru, E=quantity, F=weight, G=client_code, H=box_number
- Date normalization: ISO format `YYYY-MM-DD HH:MM:SS` or other → parse with `dateutil`
- Skip rows where track_code is empty
- Strip all string values
- Convert types properly

## 7. utils/formatters.py
```python
class MessageFormatter:
    @staticmethod
    def format_user_result(item: CargoItem) -> str:
        # Without client_code

    @staticmethod
    def format_admin_result(item: CargoItem) -> str:
        # With client_code (Mijoz ID)

    @staticmethod
    def format_multiple_results(items: List[CargoItem], is_admin: bool = False) -> str:
        # Format multiple results with separator

    @staticmethod
    def format_welcome(full_name: str) -> str:
        # Welcome message with bot name

    @staticmethod
    def format_admin_welcome(full_name: str) -> str:
        # Admin welcome message
```

Message format (user):
```
🇨🇳 XITOY OMBORIDA

🔍 Track kod: {track_code}
✈️ Reys: M2 JET
📅 Qabul qilingan: {received_date}
📦 Mahsulot (RU): {product_name_ru}
📦 Mahsulot (CN): {product_name_cn}
⚖️ Vazn: {weight} kg
🔢 Miqdor: {quantity}
📦 Quti raqami: {box_number}

💡 Boshqa yukni tekshirish uchun keyingi track kodni yuboring.
Jarayonni to'xtatish uchun ❌ Bekor qilish tugmasini bosing.
```

Message format (admin):
```
🇨🇳 XITOY OMBORIDA

🔍 Track kod: {track_code}
👤 Mijoz ID: {client_code}
✈️ Reys: M2 JET
📅 Qabul qilingan: {received_date}
📦 Mahsulot (RU): {product_name_ru}
📦 Mahsulot (CN): {product_name_cn}
⚖️ Vazn: {weight} kg
🔢 Miqdor: {quantity}
📦 Quti raqami: {box_number}

💡 Boshqa yukni tekshirish uchun keyingi track kodni yuboring.
```

## 8. services.py — SOLID compliant
```python
class CargoService(ABC):
    @abstractmethod
    async def search_by_track(self, track_code: str) -> TrackSearchResult: ...
    @abstractmethod
    async def search_by_client(self, client_code: str) -> ClientSearchResult: ...

class CargoServiceImpl(CargoService):
    def __init__(self, db: DatabaseManager): ...

class ImportService(ABC):
    @abstractmethod
    async def import_from_excel(self, file_path: str) -> ImportResult: ...

class ImportServiceImpl(ImportService):
    def __init__(self, db: DatabaseManager, parser: ExcelParser): ...

class ImportResult(BaseModel):
    total_rows: int
    imported: int
    skipped: int
    errors: List[str]
```

## 9. Handlers

### common.py
- `/start` — Check if admin (user_id == ADMIN_ID), send welcome message with main keyboard. Admin gets admin keyboard.
- `Cancel` callback — Reset state, send main menu

### user.py
- `Track kod tekshirish` callback → Set state waiting_for_track, ask for track code with cancel keyboard
- In `waiting_for_track` state:
  - If text length < MIN_TRACK_LENGTH → error message
  - If text length > MAX_TRACK_LENGTH → error message
  - Else search by track_code (LIKE query for partial match, exact match first)
  - If found → format and send result(s)
  - If not found → "Topilmadi" message with support contact
  - Stay in state for next search, show cancel button

### admin.py
- `Admin` callback for regular users → Send admin contact inline button (@MUSTAFOYEV_ANVAR)
- For admin user:
  - `Baza yuklash` → Set state waiting_for_file, ask for Excel file
  - In `waiting_for_file`: Parse Excel, import to DB, show stats
  - `Track qidirish` → Set state waiting_for_track_search, admin track search
  - `Client qidirish` → Set state waiting_for_client_search, ask for client code
  - In `waiting_for_client_search`: Search by client_code, show results
  - `Bazani tozalash` → Confirm, then delete all items
  - Show admin keyboard after each action

## 10. main.py
```python
async def main():
    # Init bot, dp, database
    # Register all routers
    # Start polling
```

## Tech Stack
- `aiogram>=3.0.0` — Telegram bot framework
- `aiosqlite>=0.20.0` — Async SQLite
- `openpyxl>=3.1.0` — Excel parsing
- `python-dateutil>=2.9.0` — Date parsing
- `pydantic>=2.0` — Data validation
- `python-dotenv>=1.0.0` — Env vars

## Run command
```bash
python -m bot.main
```
