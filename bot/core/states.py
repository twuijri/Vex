"""
FSM States for complex user interactions
"""
from aiogram.fsm.state import State, StatesGroup


class WelcomeStates(StatesGroup):
    """States for editing welcome message"""
    waiting_for_message = State()
    waiting_for_button_text = State()
    waiting_for_button_url = State()


class RulesStates(StatesGroup):
    """States for editing rules"""
    waiting_for_message = State()
    waiting_for_button_text = State()
    waiting_for_button_url = State()


class BlockedWordsStates(StatesGroup):
    """States for managing blocked words"""
    waiting_for_word_to_add = State()
    waiting_for_word_to_remove = State()


class AllowedWordsStates(StatesGroup):
    """States for managing allowed words"""
    waiting_for_word_to_add = State()
    waiting_for_word_to_remove = State()


class SilentStates(StatesGroup):
    """States for silent mode configuration"""
    waiting_for_lock_message = State()
    waiting_for_unlock_message = State()
    waiting_for_timer_message = State()
    waiting_for_from_time = State()
    waiting_for_to_time = State()
    waiting_for_timer_duration = State()


class SupportStates(StatesGroup):
    """States for support system"""
    waiting_for_block_reason = State()


class CaptchaStates(StatesGroup):
    """States for captcha verification"""
    waiting_for_answer = State()


class WarnStates(StatesGroup):
    """States for warn system configuration"""
    waiting_for_max_warns = State()
    waiting_for_warn_action = State()


class FloodStates(StatesGroup):
    """States for flood control configuration"""
    waiting_for_max_messages = State()
    waiting_for_time_window = State()
    waiting_for_flood_action = State()
