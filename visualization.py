import matplotlib.pyplot as plt
from datetime import datetime
from database import get_historical_data
import io
import logging
from matplotlib.dates import DateFormatter
import models
logger = logging.getLogger(__name__)


def generate_traffic_plot(date_str):
    """Генерирует график пробок за указанный день"""
    try:
        # Проверяем и преобразуем дату
        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError as e:
            logger.error(f"Неверный формат даты: {date_str}")
            return None, "Неверный формат даты. Используйте ДД.ММ.ГГГГ"

        # Получаем данные за день
        data = get_historical_data(specific_date=date_obj)

        if not data:
            return None, f"Нет данных за {date_str}"

        times = [dt for dt, _ in data]
        levels = [level * 5 for _, level in data]
        plt.figure(figsize=(10, 5))

        plt.plot(times, levels,
                 marker='o',
                 linestyle='-',
                 color='red',
                 markersize=5,
                 linewidth=2)

        plt.title(f"График пробок за {date_str}")
        plt.xlabel("Время", fontsize=12)
        plt.ylabel("Уровень пробок (0-5)", fontsize=12)
        plt.ylim(0, 5.5)
        plt.grid(True, linestyle='--', alpha=0.7)

        ax = plt.gca()
        ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))
        plt.xticks(rotation=45)

        avg_level = sum(levels) / len(levels)
        plt.axhline(avg_level, color='blue', linestyle='--',
                    label=f'Средний уровень: {avg_level:.1f}/5')
        plt.legend()

        buf = io.BytesIO()
        plt.savefig(buf,
                    format='png',
                    dpi=80,
                    bbox_inches='tight',
                    facecolor='white')
        buf.seek(0)
        plt.close()

        return buf, None

    except Exception as e:
        logger.error(f"Ошибка при генерации графика: {e}", exc_info=True)
        return None, f"Ошибка при генерации графика: {str(e)}"


def generate_prediction_plot(date_str):
    """Генерирует график предсказаний пробок на указанный день"""
    try:
        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            return None, "Неверный формат даты. Используйте ДД.ММ.ГГГГ"

        predictions = models.predict_day(date_obj)

        if not predictions:
            return None, "Не удалось сгенерировать прогноз"

        times = [dt for dt, _ in predictions]
        levels = [level * 5 for _, level in predictions]

        plt.figure(figsize=(12, 6))

        plt.plot(times, levels,
                 color='#FF6B6B',
                 linewidth=3,
                 label='Прогноз пробок')

        plt.fill_between(times, 0, levels,
                         color='#FF6B6B',
                         alpha=0.2)

        morning_peak = (7, 10)
        evening_peak = (16, 19)

        for peak, color in [(morning_peak, '#4ECDC4'), (evening_peak, '#45B7D1')]:
            plt.axvspan(
                datetime(date_obj.year, date_obj.month, date_obj.day, peak[0]),
                datetime(date_obj.year, date_obj.month, date_obj.day, peak[1]),
                color=color, alpha=0.1,
                label=f'{"Утренние" if peak == morning_peak else "Вечерние"} часы пик'
            )

        plt.title(f"Прогноз пробок на {date_str}", pad=20, fontsize=16)
        plt.xlabel("Время", fontsize=12)
        plt.ylabel("Уровень пробок (0-5)", fontsize=12)
        plt.ylim(0, 5.5)
        plt.grid(True, linestyle='--', alpha=0.5)

        ax = plt.gca()
        ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))
        plt.xticks(rotation=45)

        avg_level = sum(levels) / len(levels)
        plt.axhline(avg_level, color='#6B46C1', linestyle='--',
                    label=f'Средний уровень: {avg_level:.1f}/5')

        plt.legend(loc='upper right', framealpha=0.9)

        buf = io.BytesIO()
        plt.savefig(buf,
                    format='png',
                    dpi=80,
                    bbox_inches='tight',
                    facecolor='white')
        buf.seek(0)
        plt.close()

        return buf, None

    except Exception as e:
        logger.error(f"Ошибка при генерации графика прогноза: {e}", exc_info=True)
        return None, f"Ошибка генерации прогноза: {str(e)}"