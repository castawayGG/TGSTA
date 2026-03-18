"""FSM states for the buy flow."""
from aiogram.fsm.state import State, StatesGroup


class BuyStates(StatesGroup):
    choosing_package = State()
    choosing_recipient = State()
    entering_username = State()
    confirming_username = State()


class AdminStates(StatesGroup):
    entering_clarification = State()
