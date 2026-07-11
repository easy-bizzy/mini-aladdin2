import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta

# Настройка страницы
st.set_page_config(
    page_title="Mini-Aladdin",
    page_icon="📊",
    layout="wide"
)

# Простой CSS
st.markdown("""
<style>
    .main { background-color: #ffffff !important; }
    div[data-testid="stMetric"] { 
        background-color: #f8f9fa !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 15px !important;
    }
    div[data-testid="stMetric"] p { color: #000000 !important; }
    div[data-testid="stMetric"] label { color: #333333 !important; }
    section[data-testid="stSidebar"] { background-color: #1e3a5f !important; }
    section[data-testid="stSidebar"] * { color: #ffffff !important; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# Инициализация session state
if 'positions' not in st.session_state:
    st.session_state.positions = [
        {'ticker': 'SU26238RMFS4', 'short_name': 'ОФЗ 26238', 'qty': 41, 'buy_price': 59.2, 'coupon_rate': 0.071, 'duration': 7.2},
        {'ticker': 'SU26246RMFS5', 'short_name': 'ОФЗ 26246', 'qty': 65, 'buy_price': 88.4, 'coupon_rate': 0.12, 'duration': 5.6},
        {'ticker': 'SU26247RMFS1', 'short_name': 'ОФЗ 26247', 'qty': 149, 'buy_price': 89.0, 'coupon_rate': 0.1225, 'duration': 6.08},
        {'ticker': 'SU26248RMFS9', 'short_name': 'ОФЗ 26248', 'qty': 174, 'buy_price': 88.1, 'coupon_rate': 0.1225, 'duration': 6.2},
        {'ticker': 'SU26254RMFS6', 'short_name': 'ОФЗ 26254', 'qty': 250, 'buy_price': 93.0, 'coupon_rate': 0.13, 'duration': 6.06}
    ]

if 'last_update' not in st.session_state:
    st.session_state.last_update = None

# Функция получения цен (с кэшированием)
@st.cache_data(ttl=300)  # Кэш на 5 минут
def get_moex_prices():
    """Получить цены с MOEX"""
    prices = {}
    base_url = "https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQOB/securities"
    
    for pos in st.session_state.positions:
        try:
            url = f"{base_url}/{pos['ticker']}.json"
            response = requests.get(url, timeout=5)
            data = response.json()
            market_data = data.get('marketdata', {}).get('data', [])
            if market_data and len(market_data[0]) > 12:
                price = market_data[0][12]
                prices[pos['ticker']] = price if price else pos['buy_price']
            else:
                prices[pos['ticker']] = pos['buy_price']
        except:
            prices[pos['ticker']] = pos['buy_price']
    
    return prices

# Получить цены
prices = get_moex_prices()

# Обновить текущие цены в позициях
for pos in st.session_state.positions:
    pos['current_price'] = prices.get(pos['ticker'], pos['buy_price'])

# Расчет метрик
df = pd.DataFrame(st.session_state.positions)
df['market_value'] = df['qty'] * df['current_price'] * 10
df['cost_basis'] = df['qty'] * df['buy_price'] * 10
df['pnl'] = df['market_value'] - df['cost_basis']
df['pnl_pct'] = (df['pnl'] / df['cost_basis']) * 100

total_value = df['market_value'].sum()
df['weight'] = df['market_value'] / total_value
weighted_duration = (df['weight'] * df['duration']).sum()
dv01 = total_value * weighted_duration * 0.0001
annual_coupon = (df['qty'] * 1000 * df['coupon_rate']).sum()

metrics = {
    'total_value': total_value,
    'cost_basis': df['cost_basis'].sum(),
    'total_pnl': df['pnl'].sum(),
    'total_pnl_pct': (df['pnl'].sum() / df['cost_basis'].sum()) * 100,
    'weighted_duration': weighted_duration,
    'dv01': dv01,
    'annual_coupon': annual_coupon,
    'details': df
}

# Сайдбар
with st.sidebar:
    st.title("📊 Mini-Aladdin")
    st.markdown("---")
    
    page = st.radio(
        "Навигация",
        [" Главная", "📊 Позиции", "🔥 Стресс-тесты", 
         "🎯 Прогноз цели", "📈 Симуляция RGBI"],
        index=0
    )
    
    st.markdown("---")
    st.caption(f" Обновлено: {datetime.now().strftime('%H:%M')}")
    
    if st.button("🔄 Обновить цены"):
        st.cache_data.clear()
        st.rerun()

# ==================== ГЛАВНАЯ ====================

if page == "🏠 Главная":
    st.title(" Обзор портфеля")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Стоимость", f"{metrics['total_value']:,.0f} ₽", 
                 f"{metrics['total_pnl']:+,.0f} ₽")
    
    with col2:
        st.metric("📈 Доходность", f"{metrics['total_pnl_pct']:+.2f}%", "vs покупка")
    
    with col3:
        st.metric("⏱️ Дюрация", f"{metrics['weighted_duration']:.2f} лет", "средневзвеш.")
    
    with col4:
        st.metric("🎯 DV01", f"{metrics['dv01']:,.0f} ₽", "риск на 0.01%")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Распределение")
        fig_pie = px.pie(metrics['details'], values='market_value', 
                        names='short_name', hole=0.4)
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("💹 P&L")
        colors = ['green' if x > 0 else 'red' for x in metrics['details']['pnl']]
        fig_bar = go.Figure(go.Bar(
            x=metrics['details']['short_name'],
            y=metrics['details']['pnl'],
            marker_color=colors
        ))
        fig_bar.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🎯 Цель: 5 000 000 ₽")
    progress = min(metrics['total_value'] / 5_000_000, 1.0)
    st.progress(progress)
    st.caption(f"{metrics['total_value']:,.0f} ₽ ({progress*100:.1f}%)")

# ==================== ПОЗИЦИИ ====================

elif page == "📊 Позиции":
    st.title("💼 Управление позициями")
    
    st.subheader("Текущие позиции")
    display_df = metrics['details'][['short_name', 'qty', 'buy_price', 
                                     'current_price', 'market_value', 'pnl']].copy()
    display_df.columns = ['Облигация', 'Кол-во', 'Покупка', 'Сейчас', 'Стоимость', 'P&L']
    st.dataframe(display_df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("➕ Добавить позицию")
    
    col1, col2 = st.columns(2)
    with col1:
        new_ticker = st.text_input("Тикер", "SU26230RMFS5")
        new_name = st.text_input("Название", "ОФЗ 26230")
        new_qty = st.number_input("Количество", min_value=1, value=10)
    
    with col2:
        new_price = st.number_input("Цена покупки %", value=90.0)
        new_coupon = st.number_input("Купон %", value=10.0)
        new_duration = st.number_input("Дюрация", value=5.0)
    
    if st.button("Добавить"):
        st.session_state.positions.append({
            'ticker': new_ticker,
            'short_name': new_name,
            'qty': int(new_qty),
            'buy_price': float(new_price),
            'coupon_rate': float(new_coupon)/100,
            'duration': float(new_duration),
            'current_price': float(new_price)
        })
        st.cache_data.clear()
        st.success("✅ Добавлено!")
        st.rerun()

# ==================== СТРЕСС-ТЕСТЫ ====================

elif page == " Стресс-тесты":
    st.title("🔥 Стресс-тесты")
    
    col1, col2 = st.columns(2)
    with col1:
        rate_shock = st.slider("Изменение ставки %", -5.0, 10.0, 0.0, 0.1)
    with col2:
        fx_shock = st.slider("Ослабление рубля %", 0.0, 50.0, 0.0, 1.0)
    
    duration = metrics['weighted_duration']
    current_value = metrics['total_value']
    
    value_change = current_value * (-duration * rate_shock / 100)
    if fx_shock > 0:
        value_change -= current_value * (duration * fx_shock * 0.15 / 100)
    
    new_value = current_value + value_change
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Текущая", f"{current_value:,.0f} ₽")
    with col2:
        st.metric("Изменение", f"{value_change:+,.0f} ₽", 
                 f"{(value_change/current_value)*100:+.2f}%")
    with col3:
        st.metric("Новая", f"{new_value:,.0f} ₽")

# ==================== ПРОГНОЗ ====================

elif page == "🎯 Прогноз цели":
    st.title("🎯 Прогноз")
    
    target = st.number_input("Цель ₽", value=5_000_000, step=100_000)
    monthly = st.number_input("Вложения в месяц ₽", value=100_000, step=10_000)
    
    forecasts = []
    for pos in st.session_state.positions:
        value = pos['qty'] * pos['current_price'] * 10
        coupon = pos['coupon_rate']
        
        months = 0
        while value < target and months < 600:
            months += 1
            value += monthly
            if months % 6 == 0:
                value += value * coupon / 2
        
        forecasts.append({
            'Облигация': pos['short_name'],
            'Лет': months / 12
        })
    
    df_forecast = pd.DataFrame(forecasts).sort_values('Лет')
    st.dataframe(df_forecast, use_container_width=True)

# ==================== RGBI ====================

elif page == "📈 Симуляция RGBI":
    st.title("📈 RGBI vs ОФЗ")
    
    months = st.slider("Месяцев", 3, 60, 12)
    
    np.random.seed(42)
    current = metrics['total_value']
    values = [current]
    
    for day in range(months * 30):
        ret = np.random.normal(0.12/252, 0.08/np.sqrt(252))
        current *= (1 + ret)
        if day % 30 == 0 and day > 0:
            current += current * 0.10 / 12
        values.append(current)
    
    st.metric("RGBI финал", f"{values[-1]:,.0f} ₽", 
             f"{(values[-1]/metrics['total_value']-1)*100:+.2f}%")
    
    fig = go.Figure(go.Scatter(y=values, mode='lines'))
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
