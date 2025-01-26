import pandas as pd
import numpy as np


def norm_data(df: pd.DataFrame) -> pd.DataFrame:
    '''Нормализуем по значениям low и high, чтобы иметь одинаковые масштабы после нормализации'''

    df_max = df['high'].max()
    df_min = df['low'].min()
    df['high_norm'] = (df['high'] - df_min) / (df_max - df_min)
    df['low_norm'] = (df['low'] - df_min) / (df_max - df_min)
    df['open_norm'] = (df['open'] - df_min) / (df_max - df_min)
    df['close_norm'] = (df['close'] - df_min) / (df_max - df_min)

    return df


def calculate_dynamic_range(ATR: pd.Series, close: pd.Series,
                            multiplier: float = 2.0,
                            min_range: float = 0.0035,
                            max_range: float = 0.02) -> pd.Series:
    """Векторизованный расчет динамического диапазона с помощью индикатора ATR"""

    atr_percent = ATR.copy() / close.copy()
    return np.clip(atr_percent * multiplier, min_range, max_range)


def calculate_targets(df: pd.DataFrame) -> pd.Series:
    """Векторизованный расчет целевой переменной"""

    close = df['close'].values.copy()
    next_high = df['next_high'].values.copy()
    next_low = df['next_low'].values.copy()
    next_close = df['next_close'].values.copy()
    dynamic_range = df['dynamic_range'].values.copy()

    upper_breach = (next_high - close) / close >= dynamic_range
    lower_breach = (close - next_low) / close >= dynamic_range
    close_diff = next_close > close

    # Векторизованные условия
    return pd.Series(
        np.select(
            condlist=[
                upper_breach & lower_breach & close_diff,
                upper_breach & lower_breach & ~close_diff,
                upper_breach,
                lower_breach
            ],
            choicelist=[1, -1, 1, -1],
            default=0
        ),
        index=df.index
    )


def prepare_data(df: pd.DataFrame, multiplier: float = 2.0) -> pd.DataFrame:
    """Пайплайн обработки данных: включает определение динамических интервалов и целевую переменную"""

    df = df.copy(deep=True)

    # Сдвиги для будущих значений
    for col in ['high', 'low', 'close']:
        df[f'next_{col}'] = df[col].shift(-1)

    # Убираем NAN в первой строке
    df = df.dropna(subset=['next_high', 'next_low', 'next_close'])

    # Создаем динамический диапазон для TP/SL
    df['dynamic_range'] = calculate_dynamic_range(
        df['ATR'].copy(), df['close'].copy(), multiplier) / 2

    # Создаем целевую перменную
    df['target'] = calculate_targets(df)

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df.sort_index(inplace=True)

    return df.dropna()


def prepare_for_train(df: pd.DataFrame) -> pd.DataFrame:
    """Пайплайн подготовки датасета для обучения"""

    # train_df = pd.concat([
    #    # one-hot encoding целевой переменной
    #    pd.get_dummies(df['target'], prefix='target_'),
    #    df[['open', 'high', 'low', 'close',
    #        'SMA_delta', 'RSI_14', 'BB_delta_cu',
    #        'BB_delta_cl', 'ATR', 'Revers', 'Moment']]
    # ], axis=1
    # )

    return df[['open', 'high', 'low', 'close',
               'SMA_delta', 'RSI_14', 'BB_delta_cu',
               'BB_delta_cl', 'ATR', 'Revers', 'Moment', 'target']].copy()
