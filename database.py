import sqlite3
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from config import DB_NAME


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS traffic_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME NOT NULL,
        traffic_level REAL NOT NULL,
        day_of_week INTEGER NOT NULL,
        hour_of_day INTEGER NOT NULL,
        weather TEXT,
        is_holiday INTEGER DEFAULT 0
    )
    ''')

    conn.commit()
    conn.close()


def is_record_exists(timestamp, threshold_minutes=5):
    """Проверяем, есть ли уже запись в этом временном интервале"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    min_time = (timestamp - timedelta(minutes=threshold_minutes)).strftime('%Y-%m-%d %H:%M:%S')
    max_time = (timestamp + timedelta(minutes=threshold_minutes)).strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
    SELECT COUNT(*) FROM traffic_data 
    WHERE timestamp BETWEEN ? AND ?
    ''', (min_time, max_time))

    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def insert_traffic_data(traffic_level, weather=None, is_holiday=False, custom_timestamp=None):
    """Добавляет данные о пробках в БД"""
    now = custom_timestamp if custom_timestamp else datetime.now()
    day_of_week = now.weekday()
    hour_of_day = now.hour

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO traffic_data (timestamp, traffic_level, day_of_week, hour_of_day, weather, is_holiday)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (now, traffic_level, day_of_week, hour_of_day, weather, int(is_holiday)))

    conn.commit()
    conn.close()


async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hist_data = get_historical_data()
    if len(hist_data) < 100:
        await update.message.reply_text(
            "⚠️ В базе мало данных для точного прогноза.\n"
            "Сейчас используется тестовый алгоритм.\n"
            "Добавьте больше данных за разные дни."
        )


def get_record_count():
    """Возвращает общее количество записей в БД"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM traffic_data")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_historical_data(days=None, specific_date=None):
    """Возвращает исторические данные"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if specific_date:
        date_str = specific_date.strftime("%Y-%m-%d")
        cursor.execute('''
        SELECT timestamp, traffic_level FROM traffic_data 
        WHERE date(timestamp) = ?
        ORDER BY timestamp
        ''', (date_str,))
    else:
        cursor.execute('''
        SELECT timestamp, traffic_level FROM traffic_data 
        WHERE timestamp >= datetime('now', ?)
        ORDER BY timestamp
        ''', (f'-{days} days',))

    data = []
    for ts, level in cursor.fetchall():
        try:
            if '.' in ts:
                dt = datetime.strptime(ts.split('.')[0], "%Y-%m-%d %H:%M:%S")
            else:
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            data.append((dt, level))
        except ValueError as e:
            continue

    conn.close()
    return data


init_db()
