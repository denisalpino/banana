import plotly.graph_objects as go
import pandas as pd


def create_candlestick_chart(
    df: pd.DataFrame,
    title: str = "Свечной график",
    width: int = 1500,
    height: int = 800
) -> go.Figure:
    """Создание базового свечного графика"""
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df["timestamp"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name="Candlestick"
            )
        ]
    )

    fig.update_layout(
        title=title,
        xaxis_title="Время",
        yaxis_title="Цена",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        width=width,
        height=height
    )
    return fig


def add_target_annotations(fig: go.Figure, df: pd.DataFrame) -> None:
    """Добавление аннотаций целевой переменной"""
    for _, row in df.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row["timestamp"]],
                y=[row["close"]],
                mode="text",
                text=str(['Stay', 'Buy', 'Sell'][row["target"]]),
                textposition="top center",
                showlegend=False,
                textfont=dict(size=14)
            )
        )


def add_levels(fig: go.Figure, df: pd.DataFrame) -> None:
    """Добавление уровней TP/SL с цветовой индикацией по target"""
    # Фильтруем записи с ненулевым target и получаем следующий таймстемп
    filtered = df[df['target'] != 0].copy()
    filtered['next_timestamp'] = df['timestamp'].shift(-1).loc[filtered.index]

    # Разделяем на две группы
    long_signals = filtered[filtered['target'] == 1]
    short_signals = filtered[filtered['target'] == -1]

    # Уровни для лонгов (target=1)
    if not long_signals.empty:
        # TP (верхний уровень - зеленый)
        fig.add_trace(
            go.Scatter(
                x=long_signals['next_timestamp'],
                y=long_signals['close'] * (1 + long_signals['dynamic_range']),
                mode='markers+text',
                marker=dict(color='green', size=8, symbol='triangle-up'),
                textposition='top center',
                name='Long TP'
            )
        )
        # SL (нижний уровень - красный)
        fig.add_trace(
            go.Scatter(
                x=long_signals['next_timestamp'],
                y=long_signals['close'] * (1 - long_signals['dynamic_range']),
                mode='markers+text',
                marker=dict(color='red', size=8, symbol='triangle-down'),
                textposition='bottom center',
                name='Long SL'
            )
        )

    # Уровни для шортов (target=-1)
    if not short_signals.empty:
        # TP (нижний уровень - зеленый)
        fig.add_trace(
            go.Scatter(
                x=short_signals['next_timestamp'],
                y=short_signals['close'] *
                (1 - short_signals['dynamic_range']),
                mode='markers+text',
                marker=dict(color='green', size=8, symbol='triangle-down'),
                textposition='bottom center',
                name='Short TP'
            )
        )
        # SL (верхний уровень - красный)
        fig.add_trace(
            go.Scatter(
                x=short_signals['next_timestamp'],
                y=short_signals['close'] *
                (1 + short_signals['dynamic_range']),
                mode='markers+text',
                marker=dict(color='red', size=8, symbol='triangle-up'),
                textposition='top center',
                name='Short SL'
            )
        )


def calculate_trade_outcome(row: pd.Series) -> dict:
    """Определение параметров сделки и результата"""
    entry_price = row['close']
    tp_level = entry_price * (1 + row['dynamic_range'])
    sl_level = entry_price * (1 - row['dynamic_range'])
    next_high = row['next_high']
    next_low = row['next_low']
    next_close = row['next_close']

    # Определение сработавшего уровня
    hit_tp = next_high >= tp_level
    hit_sl = next_low <= sl_level

    if row['target'] == 1:
        exit_price = tp_level if hit_tp else sl_level if hit_sl else next_close
        exit_type = 'TP' if hit_tp else 'SL' if hit_sl else 'Close'
    elif row['target'] == -1:
        exit_price = sl_level if hit_sl else tp_level if hit_tp else next_close
        exit_type = 'SL' if hit_sl else 'TP' if hit_tp else 'Close'
    else:
        return None

    # Расчет доходности
    pnl = (exit_price / entry_price - 1) * 100
    if row['target'] == -1:
        pnl *= -1

    return {
        'entry_time': row['timestamp'],
        'exit_time': row['timestamp'] + pd.Timedelta(minutes=15),
        'entry_price': entry_price,
        'exit_price': exit_price,
        'direction': 'Long' if row['target'] == 1 else 'Short',
        'exit_type': exit_type,
        'pnl': pnl
    }


def add_trade_lines(fig: go.Figure, df: pd.DataFrame) -> None:
    """Добавление линий сделок и аннотаций"""
    trades = df[df['target'] != 0].apply(
        calculate_trade_outcome, axis=1).dropna()

    for trade in trades:
        color = 'green' if trade['pnl'] > 0 else 'red'
        line_width = 1.5

        # Линия сделки
        fig.add_trace(
            go.Scatter(
                x=[trade['entry_time'], trade['exit_time']],
                y=[trade['entry_price'], trade['exit_price']],
                mode='lines+markers',
                line=dict(color=color, width=line_width),
                marker=dict(size=6),
                showlegend=False
            )
        )

        # Аннотация с доходностью
        fig.add_annotation(
            x=trade['exit_time'],
            y=trade['exit_price'],
            text=f"{trade['pnl']:.2f}%",
            showarrow=False,
            font=dict(color=color, size=12),
            xshift=-20,
            yshift=10 if trade['direction'] == 'Long' else -10
        )

        # Маркеры уровней
        fig.add_trace(
            go.Scatter(
                x=[trade['exit_time']],
                y=[trade['exit_price']],
                mode='markers',
                marker=dict(
                    color=color,
                    size=16,
                    symbol='triangle-up' if trade['exit_type'] == 'TP' else 'triangle-down'
                ),
                showlegend=False
            )
        )


def show_example(df):
    # tp_profit = df[df['target'] == 1]['returns'].mean()
    # sl_loss = df[df['target'] == -1]['returns'].abs().mean()
    # print(f"Средний TP: {tp_profit:.4%}, Средний SL: {sl_loss:.4%}")
    # print(df.target.value_counts())

    # Визуализация
    viz_df = df[:50].copy(deep=True)
    fig = create_candlestick_chart(viz_df)
    add_levels(fig, viz_df)
    add_target_annotations(fig, viz_df)
    add_trade_lines(fig, viz_df)  # Заменяем предыдущие аннотации

    fig.show()
