import requests

from config import TOMTOM_API_KEY

import logging

logger = logging.getLogger(__name__)


def get_current_traffic():
    base_url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

    # Координаты центра Воронежа
    point = "51.660598,39.200585"

    params = {
        'point': point,
        'unit': 'KMPH',
        'thickness': 1,
        'openLr': False,
        'key': TOMTOM_API_KEY
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        # Извлекаем уровень загруженности (0-1, где 1 - максимальная загрузка)
        current_speed = data['flowSegmentData']['currentSpeed']
        free_flow_speed = data['flowSegmentData']['freeFlowSpeed']
        traffic_level = 1 - (current_speed / free_flow_speed)
        logger.info(f"Получены данные о пробках: {traffic_level:.2f} (скорость {current_speed}/{free_flow_speed} км/ч)")
        # Конвертируем в баллы 0-5
        traffic_level = round(traffic_level * 5) / 5  # Округляем до ближайшего 0.2
        return traffic_level
    except Exception as e:
        logger.error(f"Ошибка при получении данных: {e}")
        return None
