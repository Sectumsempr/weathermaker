import requests
from bs4 import BeautifulSoup

import re
from datetime import datetime

from DatabaseUpdater import check_format


class NoInformationAboutDate(Exception):
    pass


class WeatherMaker:
    def _get_number_of_month(self, month_txt):
        months = {
            "1": re.compile(r"\b[Яя][Нн][Вв][Аа][Рр]"),
            "2": re.compile(r"\b[Фф][Ее][Вв][Рр][Аа][Лл]"),
            "3": re.compile(r"\b[Мм][Аа][Рр]][Тт]"),
            "4": re.compile(r"\b[Аа][Пп][Рр][Ее][Лл]"),
            "5": re.compile(r"[Мм][Аа]"),
            "6": re.compile(r"[Ии][Юю][Нн]"),
            "7": re.compile(r"[Ии][Юю][Лл]"),
            "8": re.compile(r"[Аа][Вв][Гг][Уу][Сс][Тт]"),
            "9": re.compile(r"[Сс][Ее][Нн][Тт][Яя][Бб][Рр]"),
            "10": re.compile(r"[Оо][Кк][Тт][Яя][Бб][Рр]]"),
            "11": re.compile(r"[Нн][Оо][Яя][Бб][Рр]"),
            "12": re.compile(r"[Дд][Ее][Кк][Аа][Бб][Рр]")
        }
        for month, re_month in months.items():
            match = re.match(pattern=re_month, string=month_txt)
            if match:
                return month

    def get_dates(self, date_from_dt, date_to_dt, available_dates, available_dates_html):
        selected_dates, selected_dates_html = [], []
        if date_to_dt in available_dates:
            index_from, index_to = 0, available_dates.index(date_to_dt)
            if date_from_dt not in available_dates:
                index_from = available_dates.index(datetime(day=datetime.now().day,
                                                            month=datetime.now().month,
                                                            year=datetime.now().year))
            else:
                index_from = available_dates.index(date_from_dt)
            for elem in available_dates[index_from:index_to + 1]:
                selected_dates.append(elem)
            for elem in available_dates_html[index_from:index_to + 1]:
                selected_dates_html.append(elem)
        else:
            raise NoInformationAboutDate('Доступных прогнозов на выбранные даты нет!')
        return zip(selected_dates, selected_dates_html)

    def calculate_the_number_of_requests(self, date_from: datetime, date_to: datetime):
        beginning = date_from
        required_inquiries_archive = []
        now = datetime(day=datetime.now().day, year=datetime.now().year, month=datetime.now().month)
        if date_from >= now:
            return required_inquiries_archive, True
        while beginning <= date_to:
            required_inquiries_archive.append([beginning.month, beginning.year])
            if beginning.month == 12:
                month = 1
                year = beginning.year + 1
            else:
                month, year = beginning.month + 1, beginning.year
            beginning = datetime(day=date_to.day, month=month, year=year)
        return required_inquiries_archive, date_to >= now

    def get_info(self, day_forecast, *args, tag=None, get=False):
        list_day_night = []
        where_find = day_forecast.findAll(*args)
        if get:
            for element in where_find:
                if element.find('img'):
                    list_day_night.append(element.find('img').get(tag))
                else:
                    list_day_night.append(None)
        else:
            for element in where_find:
                if element.string.string.split():
                    list_day_night.append(element.string.split()[0])
                else:
                    list_day_night.append(None)
        return list_day_night

    def analyze_url_picture(self, url):
        info_weather = {
            "Солнечно": [1, 2, 12],
            "Снег": [8, 9, 10, 11, 14, 15, 17, 22],
            "Пасмурно": [6, 7, 13, 16, 18, 19, 20, 21, 23],
            "Облачно": [3, 4, 5]
        }
        image_weather_name = url[0].split('/')[-1]
        for weather_txt, digits in info_weather.items():
            for digit in digits:
                if str(digit) in image_weather_name:
                    return weather_txt
        return "Неизвестный тип погоды"

    def get_archive_forecast(self, need_requests, date_from_dt, exists_forecast, date_to_dt):
        forecast = exists_forecast
        for month, year in need_requests[0]:
            url_details = f'?month={month}&year={year}'
            response = requests.get(f'https://www.meteo-tv.ru/weather/archive/{url_details}')
            html_doc = BeautifulSoup(response.text, features='html.parser')
            table_content = html_doc.findAll("div", {"class": "archive__cnt jsTableContent"})

            for date_html in table_content:
                forecast_by_day_html = date_html.findAll("tr")
                for day_forecast in forecast_by_day_html:
                    date = day_forecast.findAll("td", {"class": "archive-table__date"})[0].text.split()[0][:-1]
                    date_dt = datetime.strptime(date, "%d.%m.%Y")
                    now = datetime(day=datetime.now().day, year=datetime.now().year, month=datetime.now().month)
                    if date_dt >= now:
                        break
                    elif date_dt < date_from_dt:
                        continue
                    elif date_dt > date_to_dt:
                        break

                    temperatures = self.get_info(day_forecast, "td", {"class": "archive-table__temp"})
                    exist = [True if temperature else False for temperature in temperatures]
                    if not any(exist):
                        raise NoInformationAboutDate('Resources have no information about this period of dates!')
                    pressures = self.get_info(day_forecast, "td", {"class": "archive-table__pressure"})
                    winds = self.get_info(day_forecast, "span", {"class": "archive-table__val"})
                    wets = self.get_info(day_forecast, "td", {"class": "archive-table__wet"})
                    wind_direction = self.get_info(day_forecast, "td", {"class": "archive-table__wind"}, tag='alt',
                                                   get=True)
                    weather_common = self.get_info(day_forecast, "td", {"class": "archive-table__weather"}, tag='src',
                                                   get=True)
                    weather_common = self.analyze_url_picture(weather_common)

                    times_of_day = ["day", "night"]
                    if date not in forecast:
                        base_info = {
                            "temperature": None,
                            "condition": None,
                            "pressure": None,
                            "wet": None,
                            "wind": None,
                            "wind_direction": None
                        }
                        forecast[date_dt] = {
                            times_of_day[0]: base_info.copy(),
                            times_of_day[1]: base_info.copy()
                        }
                    for num, time_of_day in enumerate(times_of_day):
                        forecast[date_dt][time_of_day]["temperature"] = f'{temperatures[num]} C' if temperatures[num] \
                            else "-"
                        forecast[date_dt][time_of_day]["condition"] = weather_common if weather_common else "-"
                        forecast[date_dt][time_of_day]["pressure"] = f'{pressures[num]} mm Hg' if pressures[num] \
                            else "-"
                        forecast[date_dt][time_of_day]["wet"] = f'{wets[num]}%' if wets[num] else "-"
                        forecast[date_dt][time_of_day]["wind"] = f'{winds[num]} m/s' if winds[num] else "-"
                        forecast[date_dt][time_of_day]["wind_direction"] = wind_direction[num] if wind_direction[
                            num] else "-"
        return forecast

    def get_future_forecast(self, date_from_dt, date_to_dt, exists_forecast):
        forecast = exists_forecast
        response = requests.get('https://yandex.ru/pogoda/moscow/details?via=ms')
        html_doc = BeautifulSoup(response.text, features='html.parser')
        forecast_by_days_html = html_doc.findAll("div", {"class": "card"})
        available_dates, available_dates_html = [], []
        for date_html in forecast_by_days_html:
            if not date_html.dt:
                continue
            date = int(date_html.dt['data-anchor'])
            month = date_html.findAll("span", {"class": "forecast-details__day-month"})[0].string
            month = int(self._get_number_of_month(month))
            data_forecast = datetime(day=date, month=month, year=datetime.now().year)
            available_dates.append(data_forecast)
            available_dates_html.append(date_html)

        selected_dates = self.get_dates(date_from_dt, date_to_dt, available_dates, available_dates_html)
        for date, date_html in selected_dates:
            all_rows = date_html.dd.table.tbody.findAll('tr')
            for row_number, row in enumerate(all_rows):
                if row_number != 1 and row_number != 3:
                    continue
                all_td = row.findAll("span", {"class": "temp__value"})
                times_of_day = ["day", "night"]
                if date not in forecast:
                    base_info = {
                        "temperature": None,
                        "condition": None,
                        "pressure": None,
                        "wet": None,
                        "wind": None,
                        "wind_direction": None
                    }
                    forecast[date] = {
                        times_of_day[0]: base_info.copy(),
                        times_of_day[1]: base_info.copy()
                    }

                temperatures = [td.string for td in all_td]

                index = 1 if row_number == 3 else 0
                forecast[date][times_of_day[index]]["temperature"] = f'{temperatures[0]} C'
                forecast[date][times_of_day[index]]["condition"] = row.findAll(
                    "td", {"class": "weather-table__body-cell weather-table__body-cell_type_condition"})[0].string
                key = "weather-table__body-cell weather-table__body-cell_type_air-pressure"
                pressure = f'{row.findAll("td", {"class": key})[0].string} mm Hg'
                forecast[date][times_of_day[index]]["pressure"] = pressure
                forecast[date][times_of_day[index]]["wet"] = row.findAll(
                    "td", {"class": "weather-table__body-cell weather-table__body-cell_type_humidity"})[0].string
                if row.findAll("span", {"class": "wind-speed"}):
                    wind = f'{row.findAll("span", {"class": "wind-speed"})[0].string} m/s'
                    forecast[date][times_of_day[index]]["wind"] = wind
                    forecast[date][times_of_day[index]]["wind_direction"] = row.findAll("abbr")[0]['title'][7:]

        return forecast

    def get_weather_forecast(self, date_from, date_to):
        """

        Метод, получающий прогноз для г. Москва за указанный диапозон дат.
        Для архивных запросов используется парсинг сайта https://www.meteo-tv.ru/weather/archive (с июля 2012 г.)
        Для прогнозов на 10 дней и прогноза на текущий день используется парсинг сайта https://yandex.ru/pogoda/moscow
        :param date_from: дата, с которой нужен прогноз погоды
        :param date_to: дата, по которую нужен прогноз погоды
        :return:
        """
        check_format(date_from, date_to)
        date_from_dt, date_to_dt = datetime.strptime(date_from, "%d.%m.%Y"), datetime.strptime(date_to, "%d.%m.%Y")

        need_requests = self.calculate_the_number_of_requests(date_from=date_from_dt, date_to=date_to_dt)
        forecast = {}
        if need_requests[1] and not need_requests[0]:
            forecast = self.get_future_forecast(date_from_dt, date_to_dt, forecast)
        elif not need_requests[1] and need_requests[0]:
            forecast = self.get_archive_forecast(need_requests, date_from_dt, forecast, date_to_dt)
        else:
            forecast = self.get_archive_forecast(need_requests, date_from_dt, forecast, date_to_dt)
            forecast = self.get_future_forecast(date_from_dt, date_to_dt, forecast)
        return forecast