from datetime import datetime, timedelta
from database import insert_traffic_data

base_data = [
    # Будни
    ("12.05.2025 00:00", 0.0, None, False),
    ("12.05.2025 01:00", 0.0, None, False),
    ("12.05.2025 02:00", 0.0, None, False),
    ("12.05.2025 03:00", 0.0, None, False),
    ("12.05.2025 04:00", 0.0, None, False),
    ("12.05.2025 05:00", 0.0, None, False),
    ("12.05.2025 06:00", 0.0, None, False),
    ("12.05.2025 07:00", 0.0, None, False),
    ("12.05.2025 07:15", 1.0, None, False),
    ("12.05.2025 07:30", 2.0, None, False),
    ("12.05.2025 07:45", 3.0, None, False),
    ("12.05.2025 08:00", 3.0, None, False),
    ("12.05.2025 08:15", 4.0, None, False),
    ("12.05.2025 08:30", 4.0, None, False),
    ("12.05.2025 09:30", 3.0, None, False),
    ("12.05.2025 10:30", 2.0, None, False),
    ("12.05.2025 11:30", 2.0, None, False),
    ("12.05.2025 12:30", 3.0, None, False),
    ("12.05.2025 13:30", 3.0, None, False),
    ("12.05.2025 14:30", 3.0, None, False),
    ("12.05.2025 14:45", 2.0, None, False),
    ("12.05.2025 16:30", 2.0, None, False),
    ("12.05.2025 16:45", 3.0, None, False),
    ("12.05.2025 17:30", 4.0, None, False),
    ("12.05.2025 18:30", 4.0, None, False),
    ("12.05.2025 19:00", 3.0, None, False),
    ("12.05.2025 19:45", 2.0, None, False),
    ("12.05.2025 20:30", 1.0, None, False),
    ("12.05.2025 21:30", 1.0, None, False),
    ("12.05.2025 22:30", 0.0, None, False),
    ("12.05.2025 23:30", 0.0, None, False),

    # Выходные
    ("17.05.2025 00:00", 0.0, None, True),
    ("17.05.2025 01:00", 0.0, None, True),
    ("17.05.2025 02:00", 0.0, None, True),
    ("17.05.2025 03:00", 0.0, None, True),
    ("17.05.2025 04:00", 0.0, None, True),
    ("17.05.2025 05:00", 0.0, None, True),
    ("17.05.2025 06:00", 0.0, None, True),
    ("17.05.2025 07:00", 0.0, None, True),
    ("17.05.2025 08:00", 0.0, None, True),
    ("17.05.2025 09:00", 0.0, None, True),
    ("17.05.2025 09:30", 1.0, None, True),
    ("17.05.2025 10:30", 1.0, None, True),
    ("17.05.2025 11:30", 2.0, None, True),
    ("17.05.2025 12:30", 2.0, None, True),
    ("17.05.2025 13:30", 2.0, None, True),
    ("17.05.2025 14:30", 2.0, None, True),
    ("17.05.2025 15:15", 1.0, None, True),
    ("17.05.2025 16:15", 1.0, None, True),
    ("17.05.2025 17:15", 1.0, None, True),
    ("17.05.2025 18:15", 1.0, None, True),
    ("17.05.2025 19:15", 1.0, None, True),
    ("17.05.2025 20:15", 1.0, None, True),
    ("17.05.2025 21:15", 1.0, None, True),
    ("17.05.2025 22:00", 0.0, None, True),
    ("17.05.2025 22:30", 0.0, None, True),
    ("17.05.2025 23:30", 0.0, None, True),

]


def generate_week_data():
    all_data = []

    weekday_pattern = {}
    weekend_pattern = {}

    for dt_str, level, weather, is_holiday in base_data:
        dt = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
        hour = dt.hour + dt.minute / 60

        if is_holiday:
            if hour not in weekend_pattern:
                weekend_pattern[hour] = []
            weekend_pattern[hour].append(level)
        else:
            if hour not in weekday_pattern:
                weekday_pattern[hour] = []
            weekday_pattern[hour].append(level)

    start_date = datetime(2025, 5, 12)
    for day in range(14):
        current_date = start_date + timedelta(days=day)
        is_holiday = current_date.weekday() >= 5

        for hour in range(24):
            for minute in [0, 30]:
                time_key = hour + minute / 60

                pattern = weekend_pattern if is_holiday else weekday_pattern

                closest_time = min(pattern.keys(), key=lambda x: abs(x - time_key))
                base_levels = pattern[closest_time]

                avg_level = sum(base_levels) / len(base_levels)
                level = max(0, min(5, avg_level + random.uniform(-0.5, 0.5)))

                dt_str = current_date.strftime("%d.%m.%Y") + f" {hour:02d}:{minute:02d}"

                all_data.append((dt_str, round(level, 1), None, is_holiday))

    return all_data


def fill_with_test_data():
    print("Заполнение базы данных тестовыми данными...")

    test_data = generate_week_data()

    for record in base_data:
        if record not in test_data:
            test_data.append(record)

    test_data.sort(key=lambda x: datetime.strptime(x[0], "%d.%m.%Y %H:%M"))

    for record in test_data:
        dt_str, level, weather, is_holiday = record
        dt = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
        level_normalized = level / 5

        insert_traffic_data(level_normalized, weather, is_holiday, custom_timestamp=dt)
        print(f"Добавлено: {dt_str} - {level}/5 (выходной: {is_holiday})")

    print(f"Готово! Добавлено {len(test_data)} записей за 2 недели.")


if __name__ == '__main__':
    import random

    random.seed(42)
    fill_with_test_data()