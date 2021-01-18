import logging
import peewee
from peewee import DatabaseProxy
import os
from playhouse.db_url import connect

database_proxy = DatabaseProxy()


class BaseTable(peewee.Model):
    class Meta:
        database = database_proxy


class Weather_forecast(BaseTable):
    name = peewee.CharField()


class Weather_forecast_by_days(BaseTable):
    table_name = peewee.ForeignKeyField(Weather_forecast)
    date = peewee.DateTimeField()
    time_of_day = peewee.CharField()
    temperature = peewee.CharField()
    condition = peewee.CharField()
    pressure = peewee.CharField()
    wet = peewee.CharField()
    wind = peewee.CharField()
    wind_direction = peewee.CharField()


log = logging.getLogger("forecast")

file_handler = logging.FileHandler(filename="forecast.log", encoding="UTF-8")
file_handler.setFormatter(logging.Formatter(fmt="%(asctime)s %(levelname)s %(message)s", datefmt='%d-%m-%Y %H:%M'))

log.addHandler(file_handler)
log.setLevel(logging.DEBUG)
file_handler.setLevel(logging.INFO)


class DatabaseInitializer:
    def __init__(self, database_path=''):
        database = connect(os.environ.get(database_path) or 'sqlite:///forecast.db')
        database_proxy.initialize(database)
        database.create_tables([Weather_forecast, Weather_forecast_by_days])

    def record_forecast(self, list_for_write):
        new_table = Weather_forecast(name='Table record')
        new_table.save()
        for row in list_for_write:
            query = Weather_forecast_by_days.select().where(
                Weather_forecast_by_days.date == row['date'],
                Weather_forecast_by_days.time_of_day == row['time_of_day'],
                Weather_forecast_by_days.temperature == row['temperature'],
                Weather_forecast_by_days.condition == row['condition'],
                Weather_forecast_by_days.pressure == row['pressure'],
                Weather_forecast_by_days.wet == row['wet'],
                Weather_forecast_by_days.wind == row['wind'],
                Weather_forecast_by_days.wind_direction == row['wind_direction']

            )
            if not query.exists():
                half_day_forecast = Weather_forecast_by_days.create(
                    table_name=new_table,
                    date=row['date'],
                    time_of_day=row['time_of_day'],
                    temperature=row['temperature'],
                    condition=row['condition'],
                    pressure=row['pressure'],
                    wet=row['wet'],
                    wind=row['wind'],
                    wind_direction=row['wind_direction']
                )
                log.info(f'В БД успешно записана информация: {row}')

    def get_forecast_db(self, date_from, date_to):
        list_to_return = []
        titles = list(Weather_forecast_by_days._meta.fields.keys())[2:]
        for forecast in Weather_forecast_by_days.select().where(Weather_forecast_by_days.date.between(
                date_from, date_to)):
            log.info(f'Информация успешно получена из БД: '
                     f'{forecast.date}, {forecast.time_of_day}, {forecast.temperature}, {forecast.condition}'
                     f'{forecast.pressure}, {forecast.wet}, {forecast.wind}, {forecast.wind_direction}')
            local_dict = {}
            for title in titles:
                title_value = getattr(forecast, title)
                local_dict[title] = title_value
            list_to_return.append(local_dict)
        return list_to_return
