from datetime import datetime, timedelta
from DatabaseInitializer import DatabaseInitializer


def check_format(date_from, date_to):
    try:
        date_from_dt = datetime.strptime(date_from, "%d.%m.%Y")
    except ValueError as exs:
        if 'day is out of range' in exs.args[0]:
            raise ValueError(f'Нет такого числа в месяце для даты {date_from}!')
        raise ValueError('Введите даты в формате ДД.ММ.ГГ. Например, 01.01.2000')

    try:
        date_to_dt = datetime.strptime(date_to, "%d.%m.%Y")
    except ValueError as exs:
        if 'day is out of range' in exs.args[0]:
            raise ValueError(f'Нет такого числа в месяце для даты {date_to}!')
        raise ValueError('Введите даты в формате ДД.ММ.ГГ. Например, 01.01.2000')

    if date_from_dt > date_to_dt:
        raise ValueError('Даты должны быть в хронологическом порядке!')
    future = datetime.now() + timedelta(days=9)
    if future <= date_to_dt:
        raise ValueError('Прогноз погоды может быть дан максимум на 10 дней вперед!')


class DatabaseUpdater:
    def __init__(self):
        database = DatabaseInitializer()
        self.get_forecast_db = database.get_forecast_db
        self.record_forecast = database.record_forecast

    def get_forecast_from_db(self, date_from, date_to):
        """

        Метод получает данные из базы данных за указанный диапазон дат.
        """
        check_format(date_from, date_to)
        date_from_dt, date_to_dt = datetime.strptime(date_from, "%d.%m.%Y"), datetime.strptime(date_to, "%d.%m.%Y")
        return self.get_forecast_db(date_from_dt, date_to_dt)

    def save_forecast_to_db(self, forecast: dict):
        """

        Метод сохраняет прогнозы в базу данных.
        """
        list_for_write = []
        i = 0
        for date, content in forecast.items():
            for time_of_day, info_dict in content.items():
                local_dict = {'date': date, 'time_of_day': time_of_day}
                for value_name, value in info_dict.items():
                    local_dict[value_name] = value
                list_for_write.append(local_dict)
                i += 1
        self.record_forecast(list_for_write)
