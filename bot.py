import logging
import os
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, CallbackQueryHandler
from telegram.ext import filters
import instaloader
from telegram.ext import PicklePersistence

# Включаем логирование для отслеживания ошибок и состояния
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для начала работы с ботом
async def start(update: Update, context: CallbackContext) -> None:
    # Проверяем, отправлялось ли сообщение ранее
    if context.user_data.get('welcome_message_sent', False) is False:
        # Отправляем приветственное сообщение с закреплением
        message = await update.message.reply_text(
            'Если вы хотите создать своего бота для ваших задач, обращайтесь ко мне — @Dfox8998 😊',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Написать мне', url='https://t.me/Dfox8998')]])
        )
        await message.pin()
        context.user_data['welcome_message_sent'] = True  # Помечаем, что сообщение было отправлено и закреплено

    # Создаем инлайн-кнопку
    keyboard = [[InlineKeyboardButton("Начать 👇", callback_data='start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Приветственное сообщение
    await update.message.reply_text(
        'Привет! Я помогу скачать видео из Instagram. Отправь мне ссылку, и я начну работу! 📸',
        reply_markup=reply_markup)

# Обработка нажатия кнопки
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'start':
        await query.edit_message_text(text="Отправь мне ссылку на видео из Instagram, и я помогу скачать.")

# Функция для скачивания видео из Instagram
async def download_video(update: Update, context: CallbackContext) -> None:
    video_url = update.message.text
    
    # Проверка, что это Instagram ссылка
    if 'instagram.com' not in video_url:
        await update.message.reply_text('Пожалуйста, отправь ссылку на видео из Instagram. 📸')
        return

    loader = instaloader.Instaloader()

    try:
        # Получаем данные о посте по ссылке
        post = instaloader.Post.from_shortcode(loader.context, video_url.split('/')[-2])

        # Создаем временную папку для загрузки, чтобы избежать конфликтов
        download_folder = 'downloads'
        os.makedirs(download_folder, exist_ok=True)

        # Скачиваем пост в папку
        loader.download_post(post, target=download_folder)
        
        # Ищем файл в папке загрузок
        files = os.listdir(download_folder)
        
        # Находим файл, который имеет расширение .mp4
        video_filename = None
        for file in files:
            if file.endswith('.mp4'):
                video_filename = os.path.join(download_folder, file)
                break
        
        if video_filename:
            # Генерация уникального имени для временного файла
            unique_filename = f'{uuid.uuid4()}.mp4'

            # Отправляем видео обратно пользователю
            with open(video_filename, 'rb') as video_file:
                await update.message.reply_video(video=video_file, caption="Вот ваше видео! 📸\n\nЕсли хотите скачать ещё, просто отправьте следующую ссылку.")

            # Удаляем файл после отправки
            os.remove(video_filename)

        else:
            await update.message.reply_text('Не удалось найти видео файл в скачанном посте. 😕')

    except Exception as e:
        await update.message.reply_text(f'Произошла ошибка при загрузке видео: {str(e)}')

# Главная функция для запуска бота
def main() -> None:
    # Токен, полученный от BotFather
   import os
TOKEN = os.getenv("BOT_TOKEN")


    # Создаем объект Application с поддержкой сохранения данных пользователей
persistence = PicklePersistence("bot_data")
application = Application.builder().token(TOKEN).persistence(persistence).build()

    # Регистрируем обработчики команд
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    # Регистрируем обработчик кнопок
application.add_handler(CallbackQueryHandler(button))

    # Запускаем бота
application.run_polling()

if __name__ == '__main__':
    main()
