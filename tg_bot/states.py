from aiogram.fsm.state import StatesGroup, State


class UserState(StatesGroup):
    WAITING_FOR_AMOUNT = State()
    WAITING_FOR_PAYMENT = State()
    WAITING_FOR_AMOUNT_XTR = State()
