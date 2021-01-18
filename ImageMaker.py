import os
import re
import cv2
import matplotlib.pyplot as plt
import numpy as np
import io

from google_trans_new import google_translator


class ImageMaker:
    image_path = 'extra_data/sample.jpg'
    font = cv2.FONT_HERSHEY_PLAIN
    color = (0, 0, 0)
    fontScale = 1
    thickness = 1
    thickness_header = 2

    colors = {
        'Black': '#000000',
        'Gray': '#808080',
        'Silver': '#C0C0C0',
        'White': '#FFFFFF',
        'Fuchsia': '#FF00FF',
        'Purple': '#800080',
        'Red': '#FF0000',
        'Maroon': '#800000',
        'Yellow': '#FFFF00',
        'Olive': '#808000',
        'Lime': '#00FF00',
        'Green': ':#008000',
        'Aqua': '#00FFFF',
        'Teal': '#008080',
        'Blue': '#0000FF',
        'Navy': '#000080'
    }

    weather_img = {
        re.compile(r"[Сс]олн|[Яя]сн"): ["python_snippets/external_data/weather_img/sun.jpg",
                                        [colors['Yellow'], colors['White']]],
        re.compile(r"[Сс]не[гж]|[Зз]амороз"): ["python_snippets/external_data/weather_img/snow.jpg",
                                               [colors['Blue'], colors['White']]],
        re.compile(r"[Пп]асмурн|[Дд]ожд|[Мм]орос"): ["python_snippets/external_data/weather_img/rain.jpg",
                                                     [colors['Aqua'], colors['White']]],
        re.compile(r"[Оо]блачн"): ["python_snippets/external_data/weather_img/cloud.jpg",
                                   [colors['Gray'], colors['White']]]
    }

    def __init__(self):
        self.forecast = None
        self.sample = cv2.imread(self.image_path)
        self.content = None
        self.vertical_values = None
        self.horizontal_values = None

    def overlay_image_alpha(self, img, img_overlay, pos, alpha_mask):
        """Overlay img_overlay on top of img at the position specified by
        pos and blend using alpha_mask.

        Alpha mask must contain values within the range [0, 1] and be the
        same size as img_overlay.
        """

        x, y = pos

        y1, y2 = max(0, y), min(img.shape[0], y + img_overlay.shape[0])
        x1, x2 = max(0, x), min(img.shape[1], x + img_overlay.shape[1])

        y1o, y2o = max(0, -y), min(img_overlay.shape[0], img.shape[0] - y)
        x1o, x2o = max(0, -x), min(img_overlay.shape[1], img.shape[1] - x)

        if y1 >= y2 or x1 >= x2 or y1o >= y2o or x1o >= x2o:
            return

        channels = img.shape[2]

        alpha = alpha_mask[y1o:y2o, x1o:x2o]
        alpha_inv = 1.0 - alpha

        for c in range(channels):
            img[y1:y2, x1:x2, c] = (alpha * img_overlay[y1o:y2o, x1o:x2o, c] +
                                    alpha_inv * img[y1:y2, x1:x2, c])

    def fadeColor(self, color_1, color_2, mix=0):
        assert len(color_1) == len(color_2)
        assert 1 >= mix >= 0, 'mix=' + str(mix)
        rgb1 = np.array([int(color_1[ii:ii + 2], 16) for ii in range(1, len(color_1), 2)])
        rgb2 = np.array([int(color_2[ii:ii + 2], 16) for ii in range(1, len(color_2), 2)])
        rgb = ((1 - mix) * rgb1 + mix * rgb2).astype(int)
        color = '#' + ('{:}' * 3).format(*[hex(a)[2:].zfill(2) for a in rgb])
        return color

    def paste_image_on_image(self, image, second_image, point=(0, 0)):
        x_offset, y_offset = point[0], point[1]
        self.overlay_image_alpha(image,
                                 second_image[:, :, 0:3],
                                 (x_offset, y_offset),
                                 second_image[:, :, 3] / 255.0)

    # def viewImage(self, image, name_of_window):
    #     cv2.namedWindow(name_of_window, cv2.WINDOW_NORMAL)
    #     cv2.imshow(name_of_window, image)
    #     cv2.waitKey(0)
    #     cv2.destroyAllWindows()

    def buf2cv2(self, buf):
        """Convert a buffer file to a cv2 Image and return it"""
        bytes_as_np_array = np.frombuffer(buf.read(), dtype=np.uint8)
        img = cv2.imdecode(bytes_as_np_array, -1)
        return img

    def get_gradient(self, colour_1, colour_2, height):
        """

        Creates rectangular gradient as jpg picture.
        :param colour_1: gradient start color (base colours are in dict colors)
        :param colour_2: gradient end color
        :param height: height of rectangle
        :return:
        """
        fig, ax = plt.subplots(figsize=(8, 5))

        n = 500
        for x in range(n + 1):
            ax.axvline(x, color=self.fadeColor(colour_1, colour_2, x / n), linewidth=4)
        buf = io.BytesIO()
        plt.savefig(buf)
        buf.seek(0)

        image_gradient = self.buf2cv2(buf)

        gradient_corners = [(126, 61), (126, 444), (718, 61), (718, 444)]  # [LU, LB, RU, RB]

        middle = (gradient_corners[0][0],
                  (gradient_corners[0][1] + gradient_corners[1][1]) * 0.5 + gradient_corners[0][1])
        x = middle[0]
        lu_y_middle = middle[1] - 0.5 * height
        y = (int(lu_y_middle) if gradient_corners[1][1] > lu_y_middle > gradient_corners[0][1]
             else gradient_corners[0][1])
        crop_img = image_gradient[y:min(gradient_corners[1][1], y + height), x: gradient_corners[2][0]]

        return crop_img

    def _keyword_path(self, text):
        if not text:
            return ""
        for pattern, details in self.weather_img.items():
            match = re.findall(pattern, text)
            if match:
                path = details[0]
                gradient_colours = details[1]
                return path, gradient_colours
        return None

    def centralize_point(self, point, text, font=font, fontScale=fontScale, thickness=thickness):
        text_size = cv2.getTextSize(text, font, fontScale, thickness)[0]
        text_x = point[0] - (text_size[0] // 2)
        text_y = point[1]
        return text_x, text_y

    def put_constants(self, list_coords_names, image):
        for num, value in enumerate(self.vertical_values):
            image = cv2.putText(image, value.capitalize(), list_coords_names[0][num], self.font, self.fontScale,
                                self.color, self.thickness_header, cv2.LINE_AA)

        for num, value in enumerate(self.horizontal_values):
            valuable_value = value.replace('_', ' ') if '_' in value else value
            image = cv2.putText(
                image, valuable_value.capitalize(), list_coords_names[1][num], self.font, self.fontScale,
                self.color, self.thickness_header, cv2.LINE_AA)

    def _get_positional_coordinates(self, image_width, image_height, point_header):
        list_coords_names, list_coords_values = [[], []], []
        list_x, list_y = [], []
        piece_of_one_column = image_width // (len(self.horizontal_values) + 2)
        gradient_y = []

        for num, value in enumerate(self.vertical_values):
            point_x = 10
            column_1 = point_header[1] * 2 + (image_height - point_header[1] * 2) * num // len(self.vertical_values)
            column_2 = (point_header[1] * 2 + (image_height - point_header[1] * 2)
                        * (num + 1) // len(self.vertical_values))
            point_y = (column_1 + column_2) // 2
            point = (point_x, point_y)
            list_y.append(point[1])
            if column_1 not in gradient_y:
                gradient_y.append(column_1)
            if column_2 not in gradient_y:
                gradient_y.append(column_2)
            list_coords_names[0].append(point)

        for num, value in enumerate(self.horizontal_values):
            column_1 = piece_of_one_column * (num)
            column_2 = piece_of_one_column * (num + 1)
            point_x = (column_1 + column_2) // 2
            point_y = point_header[1] * 2
            point = (point_x, point_y)
            list_x.append(point[0])
            list_coords_names[1].append(point)

        list_coords_values = []
        for i, y in enumerate(list_y):
            list_coords_values.append([])
            for num, x in enumerate(list_x):
                if num == 0:
                    list_coords_values[i].append((x + 20, y))
                else:
                    list_coords_values[i].append((x, y))
            else:
                column_1 = piece_of_one_column * (len(self.horizontal_values))
                column_2 = image_width
                x = (column_1 + column_2) // 2
                list_coords_values[i].append((x, y))

        return list_coords_names, list_coords_values, gradient_y

    def paste_gradient_image(self, image, gradient_y, gradient_colours):
        x_offset, y_offset = 0, gradient_y[0]
        gradient_image_point = (x_offset, y_offset)
        height = gradient_y[1] - gradient_y[0]
        gradient_image = self.get_gradient(
            gradient_colours[0], gradient_colours[1],
            height=height
        )
        self.paste_image_on_image(image, gradient_image, gradient_image_point)

    def paste_weather_image(self, image, weather_image, point):
        weather_image_point = (point[0], point[1])
        self.paste_image_on_image(image, weather_image, weather_image_point)

    def image_with_text_value(self, value, image, point, need_translate=False):
        valuable_value = "-" if not value or "None" in value else value
        textsize = cv2.getTextSize(valuable_value, self.font, self.fontScale, self.thickness)[0]
        amount_of_symbols_in_line = 14
        if need_translate:
            translator = google_translator()
            valuable_value = translator.translate(valuable_value, lang_tgt='en')
        if len(valuable_value) >= amount_of_symbols_in_line:
            image = cv2.putText(image, valuable_value[:amount_of_symbols_in_line],
                                point, self.font, self.fontScale, self.color, self.thickness_header, cv2.LINE_AA)

            point = (point[0], point[1] + textsize[1] + 10)

            image = cv2.putText(image, valuable_value[amount_of_symbols_in_line:],
                                point, self.font, self.fontScale, self.color, self.thickness_header, cv2.LINE_AA)
        else:
            image = cv2.putText(image, valuable_value,
                                point, self.font, self.fontScale, self.color, self.thickness_header, cv2.LINE_AA)
        return image

    def convert_list_to_dict(self, list_):
        dict_converted = {}

        for forecast_db_dict in list_:
            date, time_of_day = '', ''
            for name, value in forecast_db_dict.items():
                if name == 'date':
                    date = value
                    if date not in dict_converted:
                        dict_converted[date] = {}
                elif name == 'time_of_day':
                    time_of_day = value
                    if time_of_day not in dict_converted:
                        dict_converted[date][time_of_day] = {}
                else:
                    valuable_value = value.replace('−', '-') if '−' in value else value
                    dict_converted[date][time_of_day][name] = valuable_value
        return dict_converted

    def create_postcards(self, forecast):
        if isinstance(forecast, list):
            self.forecast = self.convert_list_to_dict(forecast)
        else:
            self.forecast = forecast
        self.content = list(self.forecast.values())[0]
        self.vertical_values = self.content.keys()
        self.horizontal_values = list(self.content.values())[0].keys()
        for data, content in self.forecast.items():
            date = data.strftime("%d_%m_%Y")
            date_to_print = data.strftime("%d.%m.%Y")
            image = self.sample.copy()
            image_width, image_height = image.shape[1], image.shape[0]

            point_header = self.centralize_point(point=(image_width // 2, image_height // 10), text=date_to_print,
                                                 fontScale=2)
            image = cv2.putText(image, date_to_print, point_header, self.font, 2, self.color, self.thickness_header,
                                cv2.LINE_AA)

            list_coords_names, list_coords_values, gradient_y = self._get_positional_coordinates(image_width,
                                                                                                 image_height,
                                                                                                 point_header)
            values_with_dict, unenclosed_values = [], []
            background_applied = [False] * len(content)

            for row, part_of_day in enumerate(self.vertical_values):
                row_value = content[part_of_day]

                for column, value in enumerate(self.horizontal_values):
                    column_value = row_value[value]
                    point = list_coords_values[row][column]

                    if self._keyword_path(column_value):
                        path_weather_image, gradient_colours = self._keyword_path(column_value)
                        weather_image = cv2.imread(path_weather_image)
                        weather_image = cv2.cvtColor(src=weather_image, code=cv2.COLOR_RGB2RGBA).copy()
                        self.paste_gradient_image(image, gradient_y[row:row + 2], gradient_colours)
                        image_point = (
                            list_coords_values[row][len(row_value)][0],
                            list_coords_values[row][len(row_value)][1] - (weather_image.shape[0] // 2)
                        )
                        self.paste_weather_image(image, weather_image, image_point)
                        background_applied[row] = True
                    if all(background_applied):
                        need_translate = True if value == 'condition' or value == 'wind_direction' else False
                        if '−' in column_value:
                            column_value.replace('−', '-')
                        image = self.image_with_text_value(column_value, image, point, need_translate)
                    else:
                        unenclosed_values.append([column_value, point, value])

            for value, point, key in unenclosed_values:
                need_translate = True if key == 'condition' or key == 'wind_direction' else False
                if '−' in value:
                    value.replace('−', '-')
                image = self.image_with_text_value(value, image, point, need_translate)
            self.put_constants(list_coords_names, image)
            if not os.path.exists(out_path):
                os.mkdir(out_path)
            cv2.imwrite(f'{out_path}/forecast_{date}.jpg', img=image)
            # self.viewImage(image, 'image')


out_path = 'my_postcards'
