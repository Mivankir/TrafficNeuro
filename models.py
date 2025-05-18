import logging

import numpy as np
import sqlite3
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from config import DB_NAME
import joblib
import os
from datetime import datetime

from database import get_historical_data

logger = logging.getLogger(__name__)
MODEL_FILE = "data/traffic_model.joblib"


def prepare_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT day_of_week, hour_of_day, is_holiday, traffic_level 
    FROM traffic_data
    WHERE traffic_level IS NOT NULL
    ''')

    data = cursor.fetchall()
    conn.close()

    if not data:
        return None, None

    X = np.array([[d[0], d[1], d[2]] for d in data])
    y = np.array([d[3] for d in data])

    return X, y


def train_model():
    """Обучение модели с логированием"""
    try:
        X, y = prepare_data()
        if X is None or len(X) < 100:
            logger.warning(f"Недостаточно данных для обучения ({len(X) if X else 0} записей)")
            return None

        logger.info(f"Начато обучение модели на {len(X)} записях")

        model = Pipeline([
            ('scaler', StandardScaler()),
            ('mlp', MLPRegressor(hidden_layer_sizes=(50, 30), max_iter=1000, random_state=42))
        ])

        model.fit(X, y)
        joblib.dump(model, MODEL_FILE)
        logger.info("Модель успешно переобучена")
        return model
    except Exception as e:
        logger.error(f"Ошибка при обучении модели: {e}")
        return None


def load_model():
    if os.path.exists(MODEL_FILE):
        return joblib.load(MODEL_FILE)
    return None


def predict_traffic(day_of_week, hour_of_day, is_holiday=False):
    # Если данных мало - используем эвристику
    if len(get_historical_data()) < 100:
        # Простая логика для тестового режима
        if 7 <= hour_of_day < 10:
            return 0.6  # 3/5 утром
        elif 16 <= hour_of_day < 19:
            return 0.8  # 4/5 вечером
        else:
            return 0.2  # 1/5 в остальное время

    # Иначе используем нейросеть
    model = load_model()
    if model is None:
        model = train_model()
        if model is None:
            return None

    input_data = np.array([[day_of_week, hour_of_day, int(is_holiday)]])
    prediction = model.predict(input_data)[0]

    # Ограничиваем и округляем до ближайшего балла
    prediction = max(0, min(1, prediction))
    return round(prediction * 5) / 5  # Округляем до 0.0, 0.2, 0.4, ..., 1.0


def predict_day(day_date):
    """Возвращает предсказания на весь указанный день"""
    try:
        day_of_week = day_date.weekday()
        is_holiday = day_of_week >= 5

        predictions = []
        model = load_model()
        if model is None:
            model = train_model()
            if model is None:
                return None

        for hour in range(24):
            for minute in [0, 30]:
                input_data = np.array([[day_of_week, hour + minute / 60, int(is_holiday)]])
                prediction = model.predict(input_data)[0]
                prediction = max(0, min(1, prediction))
                predictions.append((
                    datetime(day_date.year, day_date.month, day_date.day, hour, minute),
                    prediction
                ))

        return predictions

    except Exception as e:
        logger.error(f"Ошибка при прогнозировании дня: {e}")
        return None
