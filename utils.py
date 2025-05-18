from datetime import datetime


def percent_to_score(percent):
    """Конвертация процентов (0-1) в баллы (0-5)"""
    if percent < 0.2:
        return 1
    elif percent < 0.4:
        return 2
    elif percent < 0.6:
        return 3
    elif percent < 0.8:
        return 4
    else:
        return 5


def get_traffic_level_description(score):
    """Описание уровня пробок по баллам"""
    descriptions = {
        1: "🟢 Свободно (1/5)",
        2: "🟡 Умеренно (2/5)",
        3: "🟠 Загружено (3/5)",
        4: "🔴 Пробки (4/5)",
        5: "🔴🚗💨 Сильные пробки (5/5)"
    }
    return descriptions.get(score, "Нет данных")


def generate_traffic_message(current_level, prediction=None):
    now = datetime.now()
    current_score = percent_to_score(current_level)

    message = f"🚦 Дорожная ситуация в Воронеже ({now.strftime('%H:%M %d.%m')}):\n"
    message += f"{get_traffic_level_description(current_score)}\n"

    if prediction is not None:
        prediction_score = percent_to_score(prediction)
        message += "\n🔮 Прогноз на ближайший час:\n"
        message += f"{get_traffic_level_description(prediction_score)}"

    message += "\n\n" + "🚗" * current_score + "🚙" * (5 - current_score)

    return message
