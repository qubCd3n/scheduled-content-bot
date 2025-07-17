import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.database import get_db
from database.models import User, Post, Template
from services.deepseek_service import DeepseekService
from services.scheduler_service import SchedulerService
from config import Config

logger = logging.getLogger(__name__)
router = Router()

class PostCreationStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_edit_method = State()
    waiting_for_template_choice = State()
    waiting_for_custom_prompt = State()
    waiting_for_edit_confirmation = State()
    waiting_for_schedule_time = State()
    waiting_for_final_confirmation = State()

# Initialize handlers
user_handlers = None

def init_user_handlers(scheduler_service: SchedulerService):
    global user_handlers
    user_handlers = UserHandlers(scheduler_service)
    # Регистрация хендлеров вручную
    router.message(Command("start"))(user_handlers.start_command)
    router.message(Command("help"))(user_handlers.help_command)
    router.message(Command("cancel"))(user_handlers.cancel_command)
    router.message(Command("my_posts"))(user_handlers.my_posts_command)
    router.message(F.text)(user_handlers.handle_text_message)
    router.message(F.photo)(user_handlers.handle_photo_message)
    router.message(F.video)(user_handlers.handle_video_message)
    router.callback_query(F.data == "edit_template")(user_handlers.handle_template_choice)
    router.callback_query(F.data.startswith("template_"))(user_handlers.handle_template_selected)
    router.callback_query(F.data == "edit_custom")(user_handlers.handle_custom_prompt)
    router.callback_query(F.data == "edit_skip")(user_handlers.handle_skip_edit)
    router.callback_query(F.data == "confirm_edit")(user_handlers.handle_edit_confirmation)
    router.callback_query(F.data == "re_edit")(user_handlers.handle_re_edit)
    router.callback_query(F.data == "confirm_publish")(user_handlers.handle_publish_confirmation)
    router.callback_query(F.data == "cancel")(user_handlers.handle_cancel)
    return user_handlers

class UserHandlers:
    def __init__(self, scheduler_service: SchedulerService):
        self.scheduler_service = scheduler_service
        self.deepseek_service = DeepseekService()
        
    # Удалены декораторы @router.message и @router.callback_query
    async def start_command(self, message: Message):
        """Handle /start command"""
        try:
            if not message.from_user:
                await message.answer("Ошибка: не удалось определить пользователя Telegram.")
                return
            db_gen = get_db()
            db = next(db_gen)
            try:
                # Create or get user
                user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
                if not user:
                    user = User(
                        telegram_id=message.from_user.id,
                        username=message.from_user.username,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name
                    )
                    db.add(user)
                    db.commit()
                welcome_text = """
🤖 Добро пожаловать в Scheduled Content Editor!

Этот бот поможет вам:
• Создавать контент с текстом и медиа
• Редактировать текст через AI
• Планировать публикацию постов
• Автоматически публиковать в указанное время

📝 Отправьте мне сообщение с текстом и/или медиа, чтобы начать создание поста.

Доступные команды:
/start - Начать работу
/help - Показать справку
/my_posts - Мои запланированные посты
/cancel - Отменить текущую операцию
                """
                await message.answer(welcome_text)
            finally:
                db_gen.close()
        except Exception as e:
            logger.error(f"Error in start command: {str(e)}")
            await message.answer("Произошла ошибка. Попробуйте позже.")
            
    async def help_command(self, message: Message):
        """Handle /help command"""
        help_text = """
📚 Справка по использованию бота:

1️⃣ Отправьте контент (текст + фото/видео)
2️⃣ Выберите метод редактирования:
   • Шаблон (формальный, разговорный и др.)
   • Свой промпт
3️⃣ Подтвердите отредактированный текст
4️⃣ Укажите время публикации
5️⃣ Подтвердите финальный пост

🕐 Формат времени: ДД.ММ.ГГГГ ЧЧ:ММ
Пример: 15.07.2025 14:30

📋 Команды:
/start - Начать работу
/help - Эта справка
/my_posts - Запланированные посты
/cancel - Отменить операцию
        """
        await message.answer(help_text)
        
    async def cancel_command(self, message: Message, state: FSMContext):
        """Handle /cancel command"""
        await state.clear()
        await message.answer("❌ Операция отменена. Отправьте новый контент для создания поста.")
        
    async def my_posts_command(self, message: Message):
        """Handle /my_posts command"""
        try:
            if not message.from_user:
                await message.answer("Ошибка: не удалось определить пользователя Telegram.")
                return
            db_gen = get_db()
            db = next(db_gen)
            try:
                user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
                if not user:
                    await message.answer("Пользователь не найден. Используйте /start для регистрации.")
                    return
                scheduled_posts = self.scheduler_service.get_scheduled_posts(user.id)
                if not scheduled_posts:
                    await message.answer("У вас нет запланированных постов.")
                    return
                posts_text = "📋 Ваши запланированные посты:\n\n"
                for i, post in enumerate(scheduled_posts, 1):
                    text_preview = (post.edited_text or post.original_text)[:50] + "..."
                    scheduled_time = post.scheduled_time.strftime("%d.%m.%Y %H:%M")
                    posts_text += f"{i}. {text_preview}\n⏰ {scheduled_time}\n\n"
                await message.answer(posts_text)
            finally:
                db_gen.close()
        except Exception as e:
            logger.error(f"Error in my_posts command: {str(e)}")
            await message.answer("Произошла ошибка при получении списка постов.")
            
    async def handle_text_message(self, message: Message, state: FSMContext):
        """Handle text messages"""
        current_state = await state.get_state()
        
        if current_state == PostCreationStates.waiting_for_content:
            # User sent initial content
            await self._handle_initial_content(message, state)
        elif current_state == PostCreationStates.waiting_for_custom_prompt:
            # User sent custom prompt
            await self._handle_custom_prompt(message, state)
        elif current_state == PostCreationStates.waiting_for_schedule_time:
            # User sent schedule time
            await self._handle_schedule_time(message, state)
        else:
            # Start new post creation
            await self._handle_initial_content(message, state)
            
    async def handle_photo_message(self, message: Message, state: FSMContext):
        """Handle photo messages"""
        current_state = await state.get_state()
        
        if current_state == PostCreationStates.waiting_for_content:
            await self._handle_initial_content(message, state)
        else:
            await self._handle_initial_content(message, state)
            
    async def handle_video_message(self, message: Message, state: FSMContext):
        """Handle video messages"""
        current_state = await state.get_state()
        
        if current_state == PostCreationStates.waiting_for_content:
            await self._handle_initial_content(message, state)
        else:
            await self._handle_initial_content(message, state)
            
    async def _handle_initial_content(self, message: Message, state: FSMContext):
        """Handle initial content from user"""
        try:
            # Extract text and media
            text = message.text or message.caption or ""
            media_files = []
            
            if message.photo:
                media_files.append({
                    'type': 'photo',
                    'file_id': message.photo[-1].file_id
                })
            elif message.video:
                media_files.append({
                    'type': 'video',
                    'file_id': message.video.file_id
                })
                
            # Store in state
            await state.update_data(
                original_text=text,
                media_files=media_files
            )
            
            # Ask for edit method
            await self._ask_for_edit_method(message, state)
            
        except Exception as e:
            logger.error(f"Error handling initial content: {str(e)}")
            await message.answer("Произошла ошибка при обработке контента. Попробуйте еще раз.")
            
    async def _ask_for_edit_method(self, message: Message, state: FSMContext):
        """Ask user to choose edit method"""
        builder = InlineKeyboardBuilder()
        builder.button(text="📝 Выбрать шаблон", callback_data="edit_template")
        builder.button(text="✏️ Свой промпт", callback_data="edit_custom")
        builder.button(text="⏭️ Без редактирования", callback_data="edit_skip")
        
        await message.answer(
            "Выберите метод редактирования текста:",
            reply_markup=builder.as_markup()
        )
        await state.set_state(PostCreationStates.waiting_for_edit_method)
        
    async def handle_template_choice(self, callback: CallbackQuery, state: FSMContext):
        """Handle template choice"""
        try:
            db_gen = get_db()
            db = next(db_gen)
            try:
                templates = db.query(Template).filter(Template.is_default == True).order_by(Template.id).limit(3).all()
                builder = InlineKeyboardBuilder()
                for template in templates:
                    builder.button(text=template.name, callback_data=f"template_{template.id}")
                builder.button(text="❌ Отмена", callback_data="cancel")
                if callback.message and hasattr(callback.message, "edit_text"):
                    await callback.message.edit_text(
                        "Выберите шаблон для редактирования:",
                        reply_markup=builder.as_markup()
                    )
                elif callback.message and hasattr(callback.message, "answer"):
                    await callback.message.answer(
                        "Выберите шаблон для редактирования:",
                        reply_markup=builder.as_markup()
                    )
                else:
                    logger.error("callback.message is None or has no edit_text/answer method")
                await state.set_state(PostCreationStates.waiting_for_template_choice)
            finally:
                db_gen.close()
        except Exception as e:
            logger.error(f"Error in template choice: {str(e)}")
            if callback.message and hasattr(callback.message, "answer"):
                await callback.message.answer("Произошла ошибка. Попробуйте еще раз.")
            
    async def handle_template_selected(self, callback: CallbackQuery, state: FSMContext):
        """Handle template selection"""
        try:
            if not callback.data or not isinstance(callback.data, str):
                if callback.message and hasattr(callback.message, "answer"):
                    await callback.message.answer("Ошибка: не удалось получить данные шаблона.")
                return
            parts = callback.data.split("_")
            if len(parts) < 2 or not parts[1].isdigit():
                if callback.message and hasattr(callback.message, "answer"):
                    await callback.message.answer("Ошибка: некорректные данные шаблона.")
                return
            template_id = int(parts[1])
            db_gen = get_db()
            db = next(db_gen)
            try:
                template = db.query(Template).filter(Template.id == template_id).first()
                
                if not template:
                    if callback.message and hasattr(callback.message, "answer"):
                        await callback.message.answer("❌ Шаблон не найден.")
                    return
                
                # Get original text
                data = await state.get_data()
                original_text = data.get('original_text', '')
                
                if not original_text:
                    if callback.message and hasattr(callback.message, "answer"):
                        await callback.message.answer("Текст для редактирования не найден.")
                    return
                
                # Edit text using Deepseek
                await callback.message.answer("🔄 Редактирую текст...")
                edited_text = await self.deepseek_service.edit_text(original_text, template.prompt)
                
                if edited_text:
                    await state.update_data(
                        edited_text=edited_text,
                        template_used=template.name,
                        custom_prompt=None
                    )
                    await self._show_edit_preview(callback.message, original_text, edited_text, state)
                else:
                    if callback.message and hasattr(callback.message, "answer"):
                        await callback.message.answer("❌ Ошибка при редактировании текста. Попробуйте другой шаблон или свой промпт.")
            finally:
                db_gen.close()
        except Exception as e:
            logger.error(f"Error in template selection: {str(e)}")
            if callback.message and hasattr(callback.message, "answer"):
                await callback.message.answer("Произошла ошибка при редактировании.")
            
    async def handle_custom_prompt(self, callback: CallbackQuery, state: FSMContext):
        """Handle custom prompt request"""
        await callback.message.edit_text(
            "✏️ Введите ваш промпт для редактирования текста:\n\n"
            "Пример: Перепиши этот текст в формальном стиле"
        )
        await state.set_state(PostCreationStates.waiting_for_custom_prompt)
        
    async def _handle_custom_prompt(self, message: Message, state: FSMContext):
        """Handle custom prompt from user"""
        try:
            custom_prompt = message.text.strip()
            data = await state.get_data()
            original_text = data.get('original_text', '')
            
            if not original_text:
                await message.answer("Текст для редактирования не найден.")
                return
                
            # Edit text using Deepseek
            await message.answer("🔄 Редактирую текст...")
            edited_text = await self.deepseek_service.edit_text(original_text, custom_prompt)
            
            if edited_text:
                await state.update_data(
                    edited_text=edited_text,
                    template_used=None,
                    custom_prompt=custom_prompt
                )
                await self._show_edit_preview(message, original_text, edited_text, state)
            else:
                await message.answer("❌ Ошибка при редактировании текста. Попробуйте другой промпт.")
                
        except Exception as e:
            logger.error(f"Error in custom prompt: {str(e)}")
            await message.answer("Произошла ошибка при редактировании.")
            
    async def handle_skip_edit(self, callback: CallbackQuery, state: FSMContext):
        """Handle skip edit option"""
        data = await state.get_data()
        original_text = data.get('original_text', '')
        
        await state.update_data(
            edited_text=None,
            template_used=None,
            custom_prompt=None
        )
        
        await self._show_edit_preview(callback.message, original_text, original_text, state)
        
    async def _show_edit_preview(self, message, original_text: str, edited_text: str, state: FSMContext):
        """Show edit preview to user"""
        preview_text = f"""
📝 Предварительный просмотр:

📄 Исходный текст:
{original_text}

✏️ Отредактированный текст:
{edited_text}

Подтвердите редактирование:
        """
        
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Подтвердить", callback_data="confirm_edit")
        builder.button(text="🔄 Перередактировать", callback_data="re_edit")
        builder.button(text="❌ Отменить", callback_data="cancel")
        
        await message.answer(preview_text, reply_markup=builder.as_markup())
        await state.set_state(PostCreationStates.waiting_for_edit_confirmation)
        
    async def handle_edit_confirmation(self, callback: CallbackQuery, state: FSMContext):
        """Handle edit confirmation"""
        await callback.message.edit_text(
            "⏰ Введите время публикации в формате ЧЧ:ММ (UTC)\n\n"
            "Пример: 14:30"
        )
        await state.set_state(PostCreationStates.waiting_for_schedule_time)
        
    async def handle_re_edit(self, callback: CallbackQuery, state: FSMContext):
        """Handle re-edit request"""
        await self._ask_for_edit_method(callback.message, state)
        
    async def _handle_schedule_time(self, message: Message, state: FSMContext):
        """Handle schedule time input"""
        from datetime import datetime, time, timedelta
        try:
            time_str = message.text.strip()
            # Parse time only
            try:
                user_time = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                await message.answer(
                    "❌ Неверный формат времени. Используйте формат ЧЧ:ММ (например, 14:30)"
                )
                return
            now_utc = datetime.utcnow()
            today = now_utc.date()
            scheduled_datetime = datetime.combine(today, user_time)
            # Если время уже прошло — публикуем сразу
            if scheduled_datetime <= now_utc:
                await state.update_data(scheduled_time=now_utc)
                await message.answer("⏰ Выбранное время уже прошло, пост будет опубликован сразу после подтверждения.")
            else:
                await state.update_data(scheduled_time=scheduled_datetime)
            await self._show_final_preview(message, state)
        except Exception as e:
            logger.error(f"Error handling schedule time: {str(e)}")
            await message.answer("Произошла ошибка при обработке времени.")
            
    async def _show_final_preview(self, message: Message, state: FSMContext):
        """Show final post preview"""
        try:
            data = await state.get_data()
            text_to_publish = data.get('edited_text') or data.get('original_text', '')
            media_count = len(data.get('media_files', []))
            scheduled_time = data.get('scheduled_time')
            preview_time = scheduled_time.strftime("%d.%m.%Y %H:%M") if scheduled_time else "не указано"
            preview_text = f"""
📋 Финальный пост:

📝 Текст:
{text_to_publish}

📎 Медиа: {media_count} файл(ов)
⏰ Время публикации (UTC): {preview_time}

Подтвердите публикацию:
            """
            builder = InlineKeyboardBuilder()
            builder.button(text="✅ Опубликовать", callback_data="confirm_publish")
            builder.button(text="❌ Отменить", callback_data="cancel")
            await message.answer(preview_text, reply_markup=builder.as_markup())
            await state.set_state(PostCreationStates.waiting_for_final_confirmation)
        except Exception as e:
            logger.error(f"Error showing final preview: {str(e)}")
            await message.answer("Произошла ошибка при создании предварительного просмотра.")
            
    async def handle_publish_confirmation(self, callback: CallbackQuery, state: FSMContext):
        """Handle publish confirmation"""
        try:
            data = await state.get_data()
            db_gen = get_db()
            db = next(db_gen)
            try:
                # Get or create user
                if not callback.from_user:
                    if callback.message and hasattr(callback.message, "answer"):
                        await callback.message.answer("Ошибка: не удалось определить пользователя Telegram.")
                    return
                user = db.query(User).filter(User.telegram_id == callback.from_user.id).first()
                if not user:
                    await callback.message.answer("Пользователь не найден. Используйте /start для регистрации.")
                    return
                
                # Create post
                post = Post(
                    user_id=user.id,
                    original_text=data.get('original_text', ''),
                    edited_text=data.get('edited_text'),
                    template_used=data.get('template_used'),
                    custom_prompt=data.get('custom_prompt'),
                    media_files=data.get('media_files', []),
                    scheduled_time=data.get('scheduled_time'),
                    target_channel=Config.TARGET_CHANNEL_ID,
                    status='scheduled'
                )
                
                db.add(post)
                db.commit()
                
                # Schedule post
                self.scheduler_service.schedule_post(post)
                
                await callback.message.edit_text(
                    f"✅ Пост запланирован на {data.get('scheduled_time').strftime('%d.%m.%Y %H:%M')}!\n\n"
                    f"Вы получите уведомление после публикации."
                )
                
                await state.clear()
            finally:
                db_gen.close()
        except Exception as e:
            logger.error(f"Error confirming publish: {str(e)}")
            if callback.message and hasattr(callback.message, "answer"):
                await callback.message.answer("Произошла ошибка при планировании поста.")
            
    async def handle_cancel(self, callback: CallbackQuery, state: FSMContext):
        """Handle cancel action"""
        await state.clear()
        await callback.message.edit_text("❌ Операция отменена. Отправьте новый контент для создания поста.") 