import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import time

# Настройка страницы
st.set_page_config(
    page_title="Mini-Aladdin | Портфель ОФЗ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS с универсальными цветами для любого фона
st.markdown("""
<style>
    /* Карточки метрик */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border: 2px solid #e0e0e0 !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    
    /* Текст метрик - тёмно-синий с белой обводкой */
    div[data-testid="stMetric"] p {
        color: #0d1b2a !important;
        font-size: 28px !important;
        font-weight: bold !important;
        text-shadow: 
            1px 1px 0 #ffffff,
            -1px -1px 0 #ffffff,
            1px -1px 0 #ffffff,
            -1px 1px 0 #ffffff,
            0 1px 0 #ffffff,
            0 -1px 0 #ffffff,
            1px 0 0 #ffffff,
            -1px 0 0 #ffffff !important;
    }
    
    /* Подписи метрик */
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] div[data-testid="stMetricLabel"] {
        color: #415a77 !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.8) !important;
    }
    
    /* Дельта */
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
        font-size: 16px !important;
        font-weight: 600 !important;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.8) !important;
    }
    
    /* Заголовки */
    h1, h2, h3, h4 {
        color: #0d1b2a !important;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.5) !important;
    }
    
    /* Обычный текст */
    p, span, div {
        color: #1a1a2e !important;
    }
    
    /* Сайдбар */
    section[data-testid="stSidebar"] {
        background-color: #1e3a5f !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
        text-shadow: none !important;
    }
    
    /* Таблицы */
    .stDataFrame, div[data-testid="stDataFrame"] {
        background-color: #ffffff !important;
    }
    
    /* Скрыть футер */
    footer {visibility: hidden;}
    
    /* Мобильная адаптация */
    @media (max-width: 768px) {
        div[data-testid="stMetric"] p {
            font-size: 22px !important;
        }
    }
</style>
""", unsafe_allow_html=True)


# ==================== КЛАССЫ ====================

class MOEXData:
    BASE_URL = "https://iss.moex.com/iss"
    
    @staticmethod
    def get_bond_price(ticker):
        url = f"{MOEXData.BASE_URL}/engines/stock/markets/bonds/boards/TQOB/securities/{ticker}.json"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            market_data = data['marketdata']['data']
            if market_data and len(market_data[0]) > 12:
                price = market_data[0][12]
                return price if price else None
            return None
        except:
            return None


class MiniAladdin:
    def __init__(self):
        self.positions = [
            {'ticker': 'SU26238RMFS4', 'short_name': 'ОФЗ 26238', 'qty': 41, 'buy_price': 59.2, 'coupon_rate': 0.071, 'duration': 7.2},
            {'ticker': 'SU26246RMFS5', 'short_name': 'ОФЗ 26246', 'qty': 65, 'buy_price': 88.4, 'coupon_rate': 0.12, 'duration': 5.6},
            {'ticker': 'SU26247RMFS1', 'short_name': 'ОФЗ 26247', 'qty': 149, 'buy_price': 89.0, 'coupon_rate': 0.1225, 'duration': 6.08},
            {'ticker': 'SU26248RMFS9', 'short_name': 'ОФЗ 26248', 'qty': 174, 'buy_price': 88.1, 'coupon_rate': 0.1225, 'duration': 6.2},
            {'ticker': 'SU26254RMFS6', 'short_name': 'ОФЗ 26254', 'qty': 250, 'buy_price': 93.0, 'coupon_rate': 0.13, 'duration': 6.06}
        ]
        self.moex = MOEXData()
        self.last_update = None
    
    def update_prices(self):
        for pos in self.positions:
            price = self.moex.get_bond_price(pos['ticker'])
            if price:
                pos['current_price'] = price
            else:
                pos['current_price'] = pos.get('current_price', pos['buy_price'])
        self.last_update = datetime.now()
    
    def calculate_metrics(self):
        df = pd.DataFrame(self.positions)
        df['market_value'] = df['qty'] * df['current_price'] * 10
        df['cost_basis'] = df['qty'] * df['buy_price'] * 10
        df['pnl'] = df['market_value'] - df['cost_basis']
        df['pnl_pct'] = (df['pnl'] / df['cost_basis']) * 100
        total_value = df['market_value'].sum()
        df['weight'] = df['market_value'] / total_value
        weighted_duration = (df['weight'] * df['duration']).sum()
        dv01 = total_value * weighted_duration * 0.0001
        annual_coupon = (df['qty'] * 1000 * df['coupon_rate']).sum()
        
        return {
            'total_value': total_value,
            'cost_basis': df['cost_basis'].sum(),
            'total_pnl': df['pnl'].sum(),
            'total_pnl_pct': (df['pnl'].sum() / df['cost_basis'].sum()) * 100,
            'weighted_duration': weighted_duration,
            'dv01': dv01,
            'annual_coupon': annual_coupon,
            'details': df,
            'last_update': self.last_update
        }


# ==================== ИНИЦИАЛИЗАЦИЯ ====================

@st.cache_resource
def get_aladdin():
    aladdin = MiniAladdin()
    aladdin.update_prices()
    return aladdin

aladdin = get_aladdin()
metrics = aladdin.calculate_metrics()


# ==================== САЙДБАР ====================

with st.sidebar:
    st.title("📊 Mini-Aladdin")
    st.markdown("---")
    
    page = st.radio(
        "🎯 Навигация",
        ["🏠 Главная", "📊 Позиции", "🔥 Стресс-тесты", 
         " Прогноз цели", "📈 Симуляция RGBI", "📱 О системе"],
        index=0
    )
    
    st.markdown("---")
    if aladdin.last_update:
        st.caption(f"🔄 Обновлено: {aladdin.last_update.strftime('%d.%m.%Y %H:%M')}")
    
    if st.button("🔄 Обновить цены"):
        aladdin.update_prices()
        st.cache_resource.clear()
        st.rerun()


# ==================== ГЛАВНАЯ ====================

if page == "🏠 Главная":
    st.title("💼 Обзор портфеля")
    st.caption(f"Последнее обновление: {aladdin.last_update.strftime('%d.%m.%Y %H:%M:%S')}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Стоимость",
            value=f"{metrics['total_value']:,.0f} ₽",
            delta=f"{metrics['total_pnl']:+,.0f} ₽"
        )
    
    with col2:
        st.metric(
            label="📈 Доходность",
            value=f"{metrics['total_pnl_pct']:+.2f}%",
            delta="vs покупка"
        )
    
    with col3:
        st.metric(
            label="⏱️ Дюрация",
            value=f"{metrics['weighted_duration']:.2f} лет",
            delta="средневзвеш."
        )
    
    with col4:
        st.metric(
            label="🎯 DV01",
            value=f"{metrics['dv01']:,.0f} ₽",
            delta="риск на 0.01%"
        )
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Распределение портфеля")
        fig_pie = px.pie(
            metrics['details'],
            values='market_value',
            names='short_name',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=400, template='plotly_white')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("💹 P&L по позициям")
        df = metrics['details']
        colors = ['rgb(46, 204, 113)' if x > 0 else 'rgb(231, 76, 60)' for x in df['pnl']]
        fig_bar = go.Figure(go.Bar(
            x=df['short_name'],
            y=df['pnl'],
            marker_color=colors,
            text=df['pnl'].apply(lambda x: f"{x:+,.0f} ₽"),
            textposition='auto'
        ))
        fig_bar.update_layout(
            height=400,
            yaxis_title="Прибыль/Убыток (₽)",
            template='plotly_white'
        )
        fig_bar.add_hline(y=0, line_dash="dash")
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🎯 Прогресс к цели 5 000 000 ₽")
    progress = metrics['total_value'] / 5_000_000
    st.progress(min(progress, 1.0))
    st.caption(f"Достигнуто: {metrics['total_value']:,.0f} ₽ из 5 000 000 ₽ ({progress*100:.1f}%)")
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💵 Купон в год", f"{metrics['annual_coupon']:,.0f} ₽")
    with col2:
        st.metric("💵 Купон в месяц", f"{metrics['annual_coupon']/12:,.0f} ₽")
    with col3:
        st.metric("💵 Купон в день", f"{metrics['annual_coupon']/365:,.0f} ₽")


# ==================== ПОЗИЦИИ ====================

elif page == "📊 Позиции":
    st.title("💼 Детали по позициям")
    
    df = metrics['details'][['short_name', 'qty', 'buy_price', 'current_price', 
                             'market_value', 'pnl', 'pnl_pct', 'duration', 'coupon_rate']].copy()
    df.columns = ['Облигация', 'Кол-во', 'Покупка %', 'Сейчас %', 
                  'Стоимость ₽', 'P&L ₽', 'P&L %', 'Дюрация', 'Купон %']
    
    st.dataframe(df.style.format({
        'Покупка %': '{:.2f}',
        'Сейчас %': '{:.2f}',
        'Стоимость ₽': '{:,.0f}',
        'P&L ₽': '{:+,.0f}',
        'P&L %': '{:+.2f}%',
        'Дюрация': '{:.2f}',
        'Купон %': '{:.2f}%'
    }), use_container_width=True, height=400)
    
    st.markdown("---")
    st.subheader("⏱️ Дюрация по позициям")
    fig_dur = go.Figure(go.Bar(
        x=df['Облигация'],
        y=df['Дюрация'],
        marker_color=px.colors.sequential.Blues_r[:len(df)],
        text=df['Дюрация'].apply(lambda x: f"{x:.2f}"),
        textposition='auto'
    ))
    fig_dur.update_layout(height=400, template='plotly_white')
    st.plotly_chart(fig_dur, use_container_width=True)


# ==================== СТРЕСС-ТЕСТЫ ====================

elif page == "🔥 Стресс-тесты":
    st.title("🔥 Стресс-тестирование")
    st.caption("Моделируйте реакцию портфеля на изменения рынка")
    
    col1, col2 = st.columns(2)
    with col1:
        rate_shock = st.slider(
            "📈 Изменение ключевой ставки",
            min_value=-5.0, max_value=10.0, value=0.0, step=0.1,
            format="%.1f%%"
        )
    with col2:
        fx_shock = st.slider(
            "💱 Ослабление рубля",
            min_value=0.0, max_value=50.0, value=0.0, step=1.0,
            format="%.0f%%"
        )
    
    current_value = metrics['total_value']
    duration = metrics['weighted_duration']
    
    price_change_pct = -duration * rate_shock
    value_change = current_value * (price_change_pct / 100)
    
    if fx_shock > 0:
        implied_rate_hike = fx_shock * 0.15
        additional_loss = current_value * (duration * implied_rate_hike / 100)
        value_change -= additional_loss
    
    new_value = current_value + value_change
    change_pct = (value_change / current_value) * 100
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 Текущая стоимость", f"{current_value:,.0f} ₽")
    with col2:
        st.metric("📊 Изменение", f"{value_change:+,.0f} ₽", delta=f"{change_pct:+.2f}%")
    with col3:
        st.metric("📉 Новая стоимость", f"{new_value:,.0f} ₽")
    
    st.markdown("---")
    st.subheader("📈 Чувствительность к ставке")
    
    rate_range = np.linspace(-5, 10, 100)
    losses = [current_value * (-duration * r / 100) for r in rate_range]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rate_range, y=losses, mode='lines',
        line=dict(color='rgb(52, 152, 219)', width=3),
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.1)',
        name='Изменение стоимости'
    ))
    fig.add_trace(go.Scatter(
        x=[rate_shock], y=[value_change], mode='markers',
        marker=dict(size=15, color='red', symbol='circle'),
        name='Ваш сценарий'
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    fig.update_layout(
        xaxis_title="Изменение ключевой ставки (%)",
        yaxis_title="Изменение стоимости (₽)",
        height=500, template='plotly_white'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📋 Готовые сценарии")
    
    scenarios = [
        ("🟢 Сильное снижение ставки", -3.0, 0),
        ("🟢 Умеренное снижение", -1.5, 0),
        ("⚪ Ставка без изменений", 0, 0),
        ("🟡 Небольшой рост", 1.0, 0),
        ("🟠 Значительный рост", 2.0, 0),
        ("🔴 Кризис", 5.0, 20),
    ]
    
    scenario_data = []
    for name, rate, fx in scenarios:
        change = current_value * (-duration * rate / 100)
        if fx > 0:
            change -= current_value * (duration * fx * 0.15 / 100)
        scenario_data.append({
            'Сценарий': name,
            'Шок ставки': f"{rate:+.1f}%",
            'Шок валюты': f"{fx:.0f}%",
            'Изменение ₽': f"{change:+,.0f}",
            'Новая стоимость ₽': f"{current_value + change:,.0f}"
        })
    
    st.dataframe(pd.DataFrame(scenario_data), use_container_width=True, hide_index=True)


# ==================== ПРОГНОЗ ЦЕЛИ ====================

elif page == "🎯 Прогноз цели":
    st.title("🎯 Прогноз достижения цели")
    
    target = st.number_input("Цель (₽)", value=5_000_000, step=100_000, format="%d")
    monthly = st.number_input("Ежемесячные вложения (₽)", value=100_000, step=10_000, format="%d")
    
    forecasts = []
    for pos in aladdin.positions:
        current_value = pos['qty'] * pos['current_price'] * 10
        coupon_rate = pos['coupon_rate']
        
        months = 0
        total_value = current_value
        total_coupons = 0
        
        while total_value < target and months < 600:
            months += 1
            total_value += monthly
            if months % 6 == 0:
                coupon = total_value * coupon_rate / 2
                total_value += coupon
                total_coupons += coupon
        
        forecasts.append({
            'Облигация': pos['short_name'],
            'Лет до цели': months / 12,
            'Купон %': f"{coupon_rate*100:.2f}%",
            'Реинвест. купоны ₽': f"{total_coupons:,.0f}"
        })
    
    df_forecast = pd.DataFrame(forecasts).sort_values('Лет до цели')
    
    st.markdown("---")
    st.subheader("⏱️ Время достижения цели по каждой облигации")
    
    fig = go.Figure(go.Bar(
        x=df_forecast['Облигация'],
        y=df_forecast['Лет до цели'],
        marker_color=px.colors.sequential.Viridis[:len(df_forecast)],
        text=df_forecast['Лет до цели'].apply(lambda x: f"{x:.1f} лет"),
        textposition='auto'
    ))
    fig.update_layout(height=400, template='plotly_white', yaxis_title="Лет")
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df_forecast, use_container_width=True, hide_index=True)
    
    best = df_forecast.iloc[0]
    st.success(f"🏆 **Лучший выбор:** {best['Облигация']} — достигнете цели за {best['Лет до цели']:.1f} лет")


# ==================== СИМУЛЯЦИЯ RGBI ====================

elif page == "📈 Симуляция RGBI":
    st.title("📊 Сравнение: RGBI vs Ваш портфель")
    
    months = st.slider("Период симуляции (месяцев)", 3, 60, 12)
    
    np.random.seed(42)
    current_value = metrics['total_value']
    daily_values = []
    
    for day in range(months * 30):
        daily_return = np.random.normal(0.12/252, 0.08/np.sqrt(252))
        current_value *= (1 + daily_return)
        if day % 30 == 0 and day > 0:
            current_value += current_value * 0.10 / 12
        daily_values.append({
            'date': datetime.now() + timedelta(days=day),
            'value': current_value
        })
    
    rgbi_final = current_value
    rgbi_return = (rgbi_final - metrics['total_value']) / metrics['total_value'] * 100
    
    ofz_value = metrics['total_value']
    monthly_growth = (metrics['annual_coupon'] / metrics['total_value']) / 12
    for month in range(months):
        ofz_value *= (1 + monthly_growth)
        ofz_value += 100_000
    
    ofz_return = (ofz_value - metrics['total_value']) / metrics['total_value'] * 100
    difference = rgbi_final - ofz_value
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(" RGBI", f"{rgbi_final:,.0f} ₽", f"{rgbi_return:+.2f}%")
    with col2:
        st.metric("💼 ОФЗ", f"{ofz_value:,.0f} ₽", f"{ofz_return:+.2f}%")
    with col3:
        label = "Перезаработок" if difference > 0 else "Недозаработок"
        st.metric("🆚 Разница", f"{difference:+,.0f} ₽", label)
    
    st.markdown("---")
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=[d['date'] for d in daily_values],
        y=[d['value'] for d in daily_values],
        mode='lines',
        name='RGBI',
        line=dict(color='rgb(52, 152, 219)', width=2)
    ))
    
    ofz_dates = [datetime.now() + timedelta(days=m*30) for m in range(months)]
    fig.add_trace(go.Scatter(
        x=ofz_dates,
        y=[metrics['total_value'] * (1 + monthly_growth)**m + 100_000 * m for m in range(months)],
        mode='lines+markers',
        name='ОФЗ',
        line=dict(color='rgb(46, 204, 113)', width=2)
    ))
    
    fig.update_layout(
        height=500, template='plotly_white',
        yaxis_title="Стоимость (₽)",
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)


# ==================== О СИСТЕМЕ ====================

elif page == "📱 О системе":
    st.title("📱 О системе Mini-Aladdin")
    
    st.markdown("""
    ###  Что это?
    **Mini-Aladdin** — это ваш персональный аналог профессиональной системы управления рисками 
    от BlackRock, адаптированный для Московской биржи.
    
    ### 💡 Возможности:
    - 📊 **Мониторинг портфеля** в реальном времени
    - 🔥 **Стресс-тесты** с интерактивными сценариями
    -  **Прогноз достижения целей** с реинвестированием
    - 📈 **Сравнение с индексами** (RGBI)
    - 🎯 **DV01** — точный расчёт риска в рублях
    
    ### 📱 Как установить на телефон:
    
    **iPhone (Safari):**
    1. Откройте это приложение в Safari
    2. Нажмите кнопку "Поделиться" (квадрат со стрелкой)
    3. Выберите "На экран «Домой»"
    4. Готово! Иконка появится как обычное приложение
    
    **Android (Chrome):**
    1. Откройте в Chrome
    2. Нажмите ⋮ (три точки) в правом верхнем углу
    3. Выберите "Добавить на главный экран"
    4. Готово!
    
    ### 🔧 Технологии:
    - Python + Streamlit
    - Plotly (интерактивные графики)
    - MOEX ISS API (данные с Московской биржи)
    """)
    
    st.markdown("---")
    st.caption("Создано с ❤️ для умных инвестиций")
