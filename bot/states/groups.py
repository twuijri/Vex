from aiogram.fsm.state import State, StatesGroup

class GroupSettingsStates(StatesGroup):
    waiting_for_banned_word = State()
    waiting_for_whitelist_item = State()
    waiting_for_welcome_text = State()
    waiting_for_open_time = State()
    waiting_for_close_time = State()
    waiting_for_silent_message_text = State()
    waiting_for_rules = State()
