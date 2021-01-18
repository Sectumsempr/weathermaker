# -*- coding: utf-8 -*-

from datetime import datetime, timedelta


class WeatherReceiver:
    forecast = []
    need_exit = False
    list_of_commands = {
        "add_forecast": {
            "description": "Добавление прогнозов за диапазон дат в базу данных",
            "commands_three": [
                ("WeatherMaker", "get_weather_forecast"), ("DatabaseUpdater", "save_forecast_to_db")]
        },
        "get_forecast": {
            "description": "Получение прогнозов за диапазон дат из базы",
            "commands_three": [("DatabaseUpdater", "get_forecast_from_db")]
        },
        "create_postcard": {
            "description": "Создание открыток из полученных прогнозов",
            "commands_three": [("ImageMaker", "create_postcards")]
        },
        "show_forecast": {
            "description": "Выведение полученных прогнозов на консоль",
            "commands_three": [("WeatherReceiver", "show_forecast")]
        },
        "help": {
            "description": "Получить справку",
            "commands_three": [("WeatherReceiver", "help_info")]
        },
        "exit": {
            "description": "Выйти из программы",
            "commands_three": [("WeatherReceiver", "exit")]
        },
    }

    def get_or_add_forecast(
            self, necessary_args, class_, function_name, command, def_atr=None, get_from_db=False, silence=False):
        if not silence:
            print(f"Введите следующие переменные через запятую: {', '.join(arg for arg in necessary_args)}")
        n = 0
        while True:
            n += 1
            if n > 1:
                print('Переменные введены неправильно. Попробуйте ещё раз...')
            atr = input('\n') if not def_atr else def_atr
            if "exit" in atr:
                self.do_command("exit")
                break
            if not atr or len(atr.split(',')) != len(necessary_args):
                continue
            atrs = atr.split(',')
            atrs = [atr.replace(' ', '') for atr in atrs]
            if not silence:
                print(f"Вы ввели следующие переменные: {', '.join(atr for atr in atrs)}")
                print("Приступаем к выполнению команды...")
            class_exemplar = class_()
            function_ = getattr(class_exemplar, function_name)
            acquired_info = function_(*atrs)
            if get_from_db:
                self.forecast = acquired_info
                if not self.forecast:
                    print(f"Прогноз не получен! Необходимо предворительно занести его в БД")
                    self.do_command("add_forecast", atr)
                    self.do_command(command, atr)

            if isinstance(acquired_info, dict):
                return acquired_info
            break

    def use_forecast(self, class_, function_name, command, forecast_to_add_to_db, silence):
        if not self.need_exit:
            if not silence:
                print("Приступаем к выполнению команды...")
            class_exemplar = class_()
            function_ = getattr(class_exemplar, function_name)
            if function_name == "save_forecast_to_db":
                function_(forecast_to_add_to_db)
            elif self.forecast:
                function_(self.forecast)
            else:
                print("Для начала нужно получить прогноз.")
                self.do_command("get_forecast")
                self.do_command(command)

    def show_forecast(self, command="show_forecast"):
        if not self.forecast:
            print("Для начала нужно получить прогноз.")
            self.do_command("get_forecast")
            self.do_command(command)
        else:
            forecast_list_sorted = self.forecast
            forecast_list_sorted.sort(key=lambda forecast_key: forecast_key['date'])
            for n, forecast_db_dict in enumerate(forecast_list_sorted):
                values_to_print, titles_to_print = '', ''
                for key, value in forecast_db_dict.items():
                    if n == 0:
                        add_title = f'{key:^15}' if key != 'condition' else f'{key:^30}'
                        titles_to_print += add_title
                    if isinstance(value, datetime):
                        add = f'{value.strftime("%d.%m.%Y"):^15}'
                    else:
                        add = f'{value:^15}' if key != 'condition' else f'{value:^30}'
                    values_to_print += add
                if n == 0:
                    print(titles_to_print)
                print(values_to_print)

    def exit(self):
        self.need_exit = True

    def self_command(self, command):
        class_name, function_name = self.list_of_commands[command]["commands_three"][0]
        function_ = getattr(self, function_name)
        function_()

    def another_module_command(self, command, atr, silence):
        forecast_to_add_to_db = {}
        for class_name, function_name in self.list_of_commands[command]["commands_three"]:
            module_name = class_name
            module = __import__(module_name)
            class_ = getattr(module, class_name)
            function_ = getattr(class_, function_name)
            necessary_args = list(function_.__code__.co_varnames[:function_.__code__.co_argcount])

            if 'self' in necessary_args:
                necessary_args.remove('self')
            if necessary_args and 'forecast' not in necessary_args:
                need_get_from_db = True if "get_forecast" in command else False
                forecast_to_add_to_db = self.get_or_add_forecast(
                    necessary_args, class_, function_name, command, atr, need_get_from_db, silence)
            elif necessary_args and 'forecast' in necessary_args:
                self.use_forecast(class_, function_name, command, forecast_to_add_to_db, silence)
            else:
                class_exemplar = class_()
                function_ = getattr(class_exemplar, function_name)
                function_()

    def do_command(self, command, atr=None, silence=False):
        if self.need_exit:
            pass
        elif command in self.list_of_commands.keys():
            if not silence:
                print(f'Вы выбрали {self.list_of_commands[command]["description"]}')
            if self.list_of_commands[command]["commands_three"][0][0] == self.__class__.__name__:
                self.self_command(command)
            else:
                self.another_module_command(command, atr, silence)
            if not silence:
                print('Команда успешно выполнена.')
        else:
            print('Команда введена неверно!')
            return False

    def help_info(self):
        print("Здравствуйте! Вы запустили программу для получения информации о погоде. Для работы используйте "
              "следующие из доступных команд:")
        for command, content in self.list_of_commands.items():
            print('{command:^20}{description:^20}'.format(command=command, description=content["description"]))

    def run_program(self):
        self.help_info()
        current_date = datetime.now().strftime("%d.%m.%Y")
        one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%d.%m.%Y")
        self.do_command("add_forecast", f"{one_week_ago}, {current_date}", silence=True)
        self.do_command("get_forecast", f"{one_week_ago}, {current_date}", silence=True)

        while not self.need_exit:
            command = input('\nВведите команду:\n')
            try:
                self.do_command(command)
            except Exception as exc:
                print(f'Во время выполнения произошла ошибка:\n{exc}')


if __name__ == '__main__':
    my_program = WeatherReceiver()
    my_program.run_program()
#зачёт!