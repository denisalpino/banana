import pandas as pd
import numpy as np
import vectorbt as vbt
import os


def make_indicators(
    column_name_cl='close', column_name_h='high',
    column_name_l='low', column_name_o='open'
):
    """
    Обрабатывает CSV-файлы, рассчитывает индикаторы и возвращает датафреймы.

    :param file_pattern: Паттерн для выбора файлов, например, '*.csv'.
    :param column_name: Название столбца с ценами в файлах.
    :return: Словарь с именами файлов как ключами и датафреймами с индикаторами как значениями.
    """
    # Получаем список всех CSV-файлов
    csv_files = [f for f in os.listdir(
        "./data/") if os.path.isfile(os.path.join("./data/", f))]

    results = {}
    for file_path in csv_files:
        # Загружаем данные из файла, используя полный путь
        df = pd.read_csv('./data/' + file_path, sep=';')

        # Извлекаем нужные столбцы
        price_data = df[column_name_cl]
        high_data = df[column_name_h]
        low_data = df[column_name_l]
        open_data = df[column_name_o]

        # Считаем индикаторы
        sma_q = vbt.MA.run(price_data, window=20, short_name='SMA')
        sma_s = vbt.MA.run(price_data, window=200, short_name='SMA1')
        rsi = vbt.RSI.run(price_data, window=14)
        bbands = vbt.BBANDS.run(price_data, window=20, alpha=2)
        atr = vbt.ATR.run(price_data, high_data, low_data, window=14)
        rev = -np.log(df[column_name_o] / df[column_name_cl].shift())
        mom = np.log(df[column_name_cl].shift() / df[column_name_o].shift())

        # Добавляем индикаторы в датафрейм
        # df['SMA_20'] = sma_q.ma  # Быстрая скользящая средняя
        # df['SMA_200'] = sma_s.ma  # Медленная скользящая средняя
        df['SMA_delta'] = sma_s.ma - sma_q.ma  # Дельта скользящих
        df['RSI_14'] = rsi.rsi  # Индекс относительной силы
        # df['BB_Upper'] = bbands.upper  # Верхняя полоса Боллинджера
        # df['BB_Lower'] = bbands.lower  # Нижняя полоса Боллинджера
        # df['BB_Middle'] = bbands.middle  # Средняя линия Боллинджера
        # df['BB_delta'] = bbands.upper - bbands.lower
        df['BB_delta_cu'] = bbands.upper - price_data
        df['BB_delta_cl'] = price_data - bbands.lower
        df['ATR'] = atr.atr
        df['Revers'] = rev  # Mean-reversion
        df['Moment'] = mom  # Momentum

        # Сохраняем результат в словарь
        results[file_path] = df

    df_variables = {}

    for file_name, df in results.items():
        var_name = file_name.replace('.csv', '')
        df_variables[var_name] = df

    return df_variables


df_variables = make_indicators()

AAVE = df_variables.get('AAVE_USDT_15m_candles')
ARB = df_variables.get('ARB_USDT_15m_candles')
BNB = df_variables.get('BNB_USDT_15m_candles')
BTC = df_variables.get('BTC_USDT_15m_candles')
ETH = df_variables.get('ETH_USDT_15m_candles')
JASMY = df_variables.get('JASMY_USDT_15m_candles')
LDO = df_variables.get('LDO_USDT_15m_candles')
LINK = df_variables.get('LINK_USDT_15m_candles')
OP = df_variables.get('OP_USDT_15m_candles')
PENDLE = df_variables.get('PENDLE_USDT_15m_candles')
