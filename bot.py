import logging
import sqlite3
from datetime import datetime

from telegram import Update, InputFile, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from config import TOKEN, DB_NAME
from tomtom_api import get_current_traffic
from database import insert_traffic_data, get_record_count
from models import predict_traffic, train_model
from utils import generate_traffic_message
from visualization import generate_traffic_plot, generate_prediction_plot

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

last_record_count = 0


async def check_retrain(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет необходимость переобучения"""
    global last_record_count
    current_count = get_record_count()

    if current_count >= last_record_count + 500:
        logger.info(f"Обнаружено {current_count - last_record_count} новых записей. Инициирую переобучение...")
        if train_model():
            last_record_count = current_count
            await context.bot.send_message(
                chat_id=context.job.chat_id,
                text="🔁 Модель успешно переобучена на новых данных!"
            )


async def post_init(application: Application):
    """Инициализация при старте бота"""
    global last_record_count
    last_record_count = get_record_count()
    logger.info(f"Бот инициализирован. Текущее количество записей: {last_record_count}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start с улучшенным интерфейсом"""
    menu_buttons = [
        ["🚦 Текущие пробки"],
        ["🔮 Прогноз на час"],
        ["📊 График за день"],
        ["📅 Прогноз на день"],
        ["ℹ️ Помощь"]
    ]

    reply_markup = ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True)

    await update.message.reply_text(
        "🚗 <b>Бот мониторинга пробок Воронежа</b>\n\n"
        "Выберите действие из меню ниже или введите команду:\n\n"
        "• /current - текущий уровень пробок\n"
        "• /predict - прогноз на ближайший час\n"
        "• /plot ДД.ММ.ГГГГ - график пробок за день\n"
        "• /predict_plot ДД.ММ.ГГГГ - прогноз на день\n\n"
        f"📊 В базе: {get_record_count()} записей",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help с примерами"""
    await update.message.reply_text(
        "ℹ️ <b>Справка по использованию бота</b>\n\n"
        "<b>Примеры команд:</b>\n"
        "• /plot 15.05.2025 - график за 15 мая 2025\n"
        "• /predict_plot 20.05.2025 - прогноз на 20 мая\n\n"
        "📅 Можно использовать даты от 2020 до 2030 года\n"
        "🕒 Графики доступны для дней, когда есть данные\n\n"
        "Автообновление данных каждые 5 минут",
        parse_mode='HTML'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений (для кнопок)"""
    text = update.message.text

    if text == "🚦 Текущие пробки":
        await current_traffic(update, context)
    elif text == "🔮 Прогноз на час":
        await predict(update, context)
    elif text == "📊 График за день":
        context.user_data['last_action'] = 'plot'
        await update.message.reply_text("Введите дату в формате ДД.ММ.ГГГГ\nПример: 12.05.2025")
    elif text == "📅 Прогноз на день":
        context.user_data['last_action'] = 'predict_plot'
        await update.message.reply_text("Введите дату в формате ДД.ММ.ГГГГ\nПример: 15.05.2025")
    elif text == "ℹ️ Помощь":
        await help_command(update, context)
    elif "." in text and len(text.split(".")) == 3:
        try:
            datetime.strptime(text, "%d.%m.%Y")

            if context.user_data.get('last_action') == 'predict_plot':
                context.args = [text]
                await predict_plot(update, context)
            else:
                context.args = [text]
                await show_plot(update, context)
        except ValueError:
            await update.message.reply_text("Неверный формат даты. Используйте ДД.ММ.ГГГГ")
    else:
        await update.message.reply_text("Я не понимаю эту команду. Нажмите кнопку или введите /help")


async def current_traffic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    traffic_level = get_current_traffic()
    if traffic_level is not None:
        insert_traffic_data(traffic_level)
        message = generate_traffic_message(traffic_level)
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Не удалось получить данные о пробках.")


async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    day_of_week = now.weekday()
    hour_of_day = now.hour + 1

    if hour_of_day > 23:
        hour_of_day = 0
        day_of_week = (day_of_week + 1) % 7

    prediction = predict_traffic(day_of_week, hour_of_day)

    if prediction is not None:
        current_level = get_current_traffic()
        message = generate_traffic_message(current_level, prediction)
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Недостаточно данных для прогноза.")


async def update_traffic_data(context: ContextTypes.DEFAULT_TYPE):
    traffic_level = get_current_traffic()
    if traffic_level is not None:
        insert_traffic_data(traffic_level)
        logger.info(f"Updated traffic data: {traffic_level}")


async def show_plot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /plot"""
    if not context.args:
        await update.message.reply_text(
            "Используйте: /plot ДД.ММ.ГГГГ\n"
            "Пример: /plot 12.05.2025\n\n"
            "Доступные даты можно посмотреть командой /dates"
        )
        return

    date_str = context.args[0]
    msg = await update.message.reply_text(f"⏳ Генерирую график за {date_str}...")

    buf, error = generate_traffic_plot(date_str)

    if error:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            text=f"❌ {error}"
        )
        return

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=InputFile(buf),
        caption=f"📊 График пробок за {date_str}"
    )
    await context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=msg.message_id
    )
    buf.close()


async def show_available_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает даты, для которых есть данные"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT DISTINCT date(timestamp) as day 
    FROM traffic_data 
    ORDER BY day DESC
    LIMIT 30
    ''')

    dates = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not dates:
        await update.message.reply_text("В базе нет данных")
        return

    text = "📅 Доступные даты для графиков:\n" + "\n".join(
        f"- {datetime.strptime(d, '%Y-%m-%d').strftime('%d.%m.%Y')}"
        for d in dates
    )

    await update.message.reply_text(text)


async def predict_plot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /predict_plot"""
    if not context.args and update.message.text and "." in update.message.text:
        date_str = update.message.text
    elif context.args:
        date_str = context.args[0]
    else:
        await update.message.reply_text(
            "📅 Введите дату в формате ДД.ММ.ГГГГ\n"
            "Пример: /predict_plot 15.05.2025\n\n"
            "Доступны даты до 2030 года"
        )
        return

    try:
        date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
        current_year = datetime.now().year

        if date_obj.year < 2020 or date_obj.year > 2030:
            await update.message.reply_text(
                "⚠️ Пожалуйста, введите дату между 2020 и 2030 годом"
            )
            return

        if (datetime.now().date() - date_obj).days > 365:
            await update.message.reply_text(
                "📅 Эта дата слишком далеко в прошлом"
            )
            return

    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат даты\n"
            "Используйте: ДД.ММ.ГГГГ\n"
            "Пример: 15.05.2025"
        )
        return

    status_msg = await update.message.reply_text(f"🔮 Генерирую прогноз на {date_str}...")

    buf, error = generate_prediction_plot(date_str)

    if error:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text=f"❌ {error}"
        )
        return

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=InputFile(buf),
        caption=f"🔮 Прогноз пробок на {date_str}"
    )
    await context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=status_msg.message_id
    )
    buf.close()


def main():
    application = Application.builder().token(TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("current", current_traffic))
    application.add_handler(CommandHandler("predict", predict))
    application.add_handler(CommandHandler("plot", show_plot))
    application.add_handler(CommandHandler("dates", show_available_dates))
    application.add_handler(CommandHandler("predict_plot", predict_plot))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Периодические задачи
    application.job_queue.run_repeating(
        check_retrain,
        interval=21600,
        first=10
    )

    application.run_polling()


if __name__ == '__main__':
    main()
