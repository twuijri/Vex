"""
معالجات إعدادات قاعدة البيانات
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database.models import Group
from bot.api import update_group_database_name, get_group_database_name

router = Router(name="database_settings")


class DatabaseStates(StatesGroup):
    """حالات إدارة قاعدة البيانات"""
    waiting_for_db_name = State()


@router.callback_query(F.data.startswith("db_settings:"))
async def handle_database_settings(callback: CallbackQuery, state: FSMContext):
    """معالج إعدادات قاعدة البيانات"""
    
    action = callback.data.split(":")[1]
    chat_id = callback.from_user.id
    
    if action == "view":
        # عرض اسم قاعدة البيانات الحالي
        db_name = await get_group_database_name(chat_id)
        current_name = db_name or "Vex_db"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✏️ تغيير الاسم",
                callback_data="db_settings:change"
            )],
            [InlineKeyboardButton(
                text="🔙 عودة",
                callback_data="main:back"
            )],
        ])
        
        await callback.message.edit_text(
            f"📊 إعدادات قاعدة البيانات\n\n"
            f"الاسم الحالي: <code>{current_name}</code>\n\n"
            f"اختر إجراء:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    elif action == "change":
        # طلب اسم جديد
        await callback.message.edit_text(
            "📝 أدخل اسم قاعدة البيانات الجديد:\n\n"
            "مثال: coffeeBot, mydata, production\n\n"
            "⚠️ اتركه فارغاً للاستخدام الافتراضي: <code>Vex_db</code>",
            parse_mode="HTML"
        )
        await state.set_state(DatabaseStates.waiting_for_db_name)
        await state.update_data(chat_id=chat_id)


@router.message(DatabaseStates.waiting_for_db_name)
async def process_new_db_name(message, state: FSMContext):
    """معالجة الاسم الجديد"""
    
    data = await state.get_data()
    chat_id = data.get("chat_id")
    new_name = message.text.strip()
    
    # إذا كان فارغاً → استخدم الـ default
    if not new_name:
        new_name = "Vex_db"
    
    # التحقق من الطول (لو كتب شيء)
    if len(new_name) > 64:
        await message.answer(
            "❌ اسم قاعدة البيانات طويل جداً!\n"
            "الحد الأقصى: 64 حرف"
        )
        return
    
    # تحديث في قاعدة البيانات
    success = await update_group_database_name(chat_id, new_name)
    
    if success:
        await message.answer(
            f"✅ تم تحديث اسم قاعدة البيانات!\n"
            f"الاسم الجديد: <code>{new_name}</code>",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ فشل تحديث اسم قاعدة البيانات"
        )
    
    await state.clear()
