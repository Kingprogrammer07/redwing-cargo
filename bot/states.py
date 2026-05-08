"""
aiogram FSM (Finite State Machine) state definitions.
"""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    """States for regular users."""

    waiting_for_track = State()


class AdminState(StatesGroup):
    """States for admin operations."""

    waiting_for_file = State()
    waiting_for_flight_name = State()
    waiting_for_track_search = State()
    waiting_for_client_search = State()
    waiting_for_confirm_clear = State()
    waiting_for_delete_by_flight = State()
    waiting_for_edit_flight_name = State()
    waiting_for_confirm_delete_flight = State()
