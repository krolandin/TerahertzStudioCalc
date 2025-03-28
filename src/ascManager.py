import re
from datetime import datetime
from dataTypes import DataTypes, FileTypes
from spectrumObject import SpectrumObject

class DataSet:
    def __init__(self, sample, thickness, temperature, comment, date, points, data_type, dataX, dataY):
        self.sample = sample
        self.thickness = thickness
        self.temperature = temperature
        self.comment = comment
        self.date = date
        self.points = points
        self.data_type = data_type
        self.dataX = dataX  # Массив для частот (Frequency)
        self.dataY = dataY  # Массив для значений (Transmission или Phase)

    def __repr__(self):
        return (f"DataSet(sample={self.sample}, thickness={self.thickness}, temperature={self.temperature}, "
                f"comment={self.comment}, date={self.date}, points={self.points}, "
                f"data_type={self.data_type}, dataX={self.dataX}, dataY={self.dataY})")

def parse_asc_data(text):
    # Регулярные выражения для извлечения данных
    sample_pattern = re.compile(r"Sample=(.*)")
    thickness_pattern = re.compile(r"Thickness,mm=(.*)")
    temperature_pattern = re.compile(r"Temperature=(.*)")
    comment_pattern = re.compile(r"Comment=(.*)")
    date_pattern = re.compile(r"(\d{2}\.\d{2}\.\d{4})")
    points_pattern = re.compile(r"Points=(.*)")
    data_header_pattern = re.compile(r"Frequency,GHz\t(Transmission|Phase)")
    data_row_pattern = re.compile(r"([\d,.]+E[+-]\d+)\t([\d,.]+E[+-]\d+)")  # Поддержка чисел с точкой и запятой

    datasets = []
    lines = text.strip().split('\n')
    i = 0
    while i < len(lines):
        # Парсим метаданные
        if i + 6 >= len(lines):  # Проверяем, что есть достаточно строк для заголовка
            break  # Если строк недостаточно, завершаем парсинг

        sample_match = sample_pattern.match(lines[i])
        thickness_match = thickness_pattern.match(lines[i + 1])
        temperature_match = temperature_pattern.match(lines[i + 2])
        comment_match = comment_pattern.match(lines[i + 3])
        date_match = date_pattern.match(lines[i + 4])
        points_match = points_pattern.match(lines[i + 5])
        data_header_match = data_header_pattern.match(lines[i + 6])

        # Если заголовок данных отсутствует, пропускаем этот блок
        if not all([sample_match, thickness_match, temperature_match, comment_match, date_match, points_match, data_header_match]):
            i += 1
            continue

        # Если все метаданные и заголовок найдены, продолжаем парсинг
        sample = sample_match.group(1)
        thickness = float(thickness_match.group(1).replace(',', '.'))
        temperature = float(temperature_match.group(1))
        comment = comment_match.group(1)
        date = date_match.group(1)#datetime.strptime(date_match.group(1), "%d.%m.%Y")
        points = int(points_match.group(1))
        _data_type = data_header_match.group(1)

        if _data_type == "Transmission":
            data_type = DataTypes.Trf
        else:
            data_type = DataTypes.Phf

        # Парсим данные
        dataX = []
        dataY = []
        i += 7
        while i < len(lines):
            data_row_match = data_row_pattern.match(lines[i])
            if not data_row_match:
                break
            # Преобразуем числа с запятой в точку и в float
            frequency = float(data_row_match.group(1).replace(',', '.'))/30
            value = float(data_row_match.group(2).replace(',', '.'))
            dataX.append(frequency)
            dataY.append(value)
            i += 1

        # Создаем объект DataSet и добавляем его в список
        dataset = DataSet(sample, thickness, temperature, comment, date, points, data_type, dataX, dataY)
        datasets.append(dataset)

    spectra = []
    fileType = FileTypes.asc
    for dataset in datasets:
        print(dataset)
        spectrum = SpectrumObject(dataset.sample, dataset.comment, dataset.temperature,
                                  dataset.thickness, dataset.date, "Clipboard",
                                  dataset.data_type, dataset.points, dataset.dataX[0], dataset.dataX[len(dataset.dataX) - 1],
                                  fileType)
        spectrum.xValues = dataset.dataX
        spectrum.yValues = dataset.dataY
        spectra.append(spectrum)

    # return datasets
    return spectra