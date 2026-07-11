import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import json
import os

# Настройка страницы
st.set_page_config(
    page_title="Mini-Aladdin",
    page_icon="📊",
    layout="wide"
)

# Простой CSS - только самое необходимое
st.markdown("""
<style>
    /* Принудительно светлая тема */
    .stApp {
        background-color: #ffffff;
        color: #000000;
    }
    
    /* Метрики */
    div[data-testid="stMetric"] {
        background-color: #f0f0f0;
        border-radius: 10px;
        padding: 15px;
    }
    
    div[data-testid="stMetric"] p {
        color: #000000 !important;
        font-size: 24px;
        font-weight: bold;
    }
    
    div[data-testid="stMetric"] label {
        color: #333333 !important;
    }
    
    /* Заголовки */
    h1, h2, h3 {
        color: #000000 !important;
    }
    
    /* Текст */
    p, span, div, label {
        color: #000000 !important;
    }
    
    /* Сайдбар */
    section[data-testid="stSidebar"] {
        background-color: #2c3e50 !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Кнопки */
    .stButton>button {
        background-color: #3498db;
        color: white !important;
    }
    
    /* Таблицы */
    .stDataFrame {
        background-color: #ffffff;
    }
    
    /* Скрыть футер */
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ==================== ИНИЦИАЛИЗАЦИЯ ПОРТФЕЛЯ ====================

# Файл для сохранения портфеля
PORTFOLIO_FILE = 'portfolio.json'

def load_portfolio():
    """Загрузка портфеля из файла"""
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, 'r') as f:
            return json.load(f)
    else:
        # Портфель по умолчанию
        return [
            {'ticker': 'SU26238RMFS4', 'short_name': 'ОФЗ 26238', 'qty': 41, 'buy_price': 59.2, 'coupon_rate': 0.071, 'duration': 7.2},
            {'ticker': 'SU26246RMFS5', 'short_name': 'ОФЗ 26246', 'qty': 65, 'buy_price': 88.4, 'coupon_rate': 0.12, 'duration': 5.6},
            {'ticker': 'SU26247RMFS1', 'short_name': 'ОФЗ 26247', 'qty': 149, 'buy_price': 89.0, 'coupon_rate': 0.1225, 'duration': 6.08},
            {'ticker': 'SU26248RMFS9', 'short_name': 'ОФЗ 26248', 'qty': 174, 'buy_price': 88.1, 'coupon_rate': 0.1225, 'duration': 6.2},
            {'ticker': 'SU26254RMFS6', 'short_name': 'ОФЗ 26254', 'qty': 250, 'buy_price': 93.0, 'coupon_rate': 0.13, 'duration': 6.06}
        ]

def save_portfolio(portfolio):
    """Сохранение портфеля в файл"""
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(portfolio, f, indent=2)

# Загрузка портфеля
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = load_portfolio()


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


def calculate_metrics(portfolio):
    """Расчет метрик портфеля"""
    if not portfolio:
        return None
    
    df = pd.DataFrame(portfolio)
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
        'details': df
    }


# ==================== САЙДБАР ====================

with st.sidebar:
    st.title("📊 Mini-Aladdin")
    st.markdown("---")
    
    page = st.radio(
        "Навигация",
        ["Главная", "Позиции", "Стресс-тесты", 
         "Прогноз цели", "Симуляция RGBI", "Управление портфелем"],
        index=0
    )
    
    st.markdown("---")
    st.caption("v1.0")


# ==================== УПРАВЛЕНИЕ ПОРТФЕЛЕМ ====================

if page == "Управление портфелем":
    st.title("💼 Управление портфелем")
    
    st.subheader("Добавить новую позицию")
    
    with st.form("add_position"):
        col1, col2 = st.columns(2)
        with col1:
            ticker = st.text_input("Тикер (например: SU26238RMFS4)")
            short_name = st.text_input("Название (например: ОФЗ 26238)")
            qty = st.number_input("Количество", min_value=1, value=10)
        with col2:
            buy_price = st.number_input("Цена покупки (%)", min_value=0.0, value=90.0, step=0.1)
            coupon_rate = st.number_input("Купонная ставка (%)", min_value=0.0, value=7.0, step=0.01) / 100
            duration = st.number_input("Дюрация (лет)", min_value=0.0, value=5.0, step=0.1)
        
        submitted = st.form_submit_button("Добавить позицию")
        
        if submitted:
            if ticker and short_name:
                new_position = {
                    'ticker': ticker,
                    'short_name': short_name,
                    'qty': qty,
                    'buy_price': buy_price,
                    'coupon_rate': coupon_rate,
                    'duration': duration
                }
                st.session_state.portfolio.append(new_position)
                save_portfolio(st.session_state.portfolio)
                st.success(f"✅ Добавлена позиция: {short_name}")
                st.rerun()
            else:
                st.error("❌ Заполните тикер и название")
    
    st.markdown("---")
    st.subheader("Удалить позицию")
    
    if st.session_state.portfolio:
        position_to_delete = st.selectbox(
            "Выберите позицию для удаления",
            [f"{p['short_name']} ({p['qty']} шт)" for p in st.session_state.portfolio]
        )
        
        if st.button("Удалить"):
            idx = [f"{p['short_name']} ({p['qty']} шт)" for p in st.session_state.portfolio].index(position_to_delete)
            deleted = st.session_state.portfolio.pop(idx)
            save_portfolio(st.session_state.portfolio)
            st.success(f"Удалена позиция: {deleted['short_name']}")
            st.rerun()
    
    st.markdown("---")
    st.subheader("Текущий портфель")
    st.write(f"Всего позиций: {len(st.session_state.portfolio)}")


# ==================== ОБНОВЛЕНИЕ ЦЕН ====================

# Обновление цен для всех позиций
for pos in st.session_state.portfolio:
    price = MOEXData.get_bond_price(pos['ticker'])
    if price:
        pos['current_price'] = price
    else:
        pos['current_price'] = pos.get('current_price', pos['buy_price'])

last_update = datetime.now()
metrics = calculate_metrics(st.session_state.portfolio)


# ==================== ГЛАВНАЯ ====================

if page == "Главная":
    st.title("Обзор портфеля")
    st.caption(f"Обновлено: {last_update.strftime('%d.%m.%Y %H:%M:%S')}")
    
    if metrics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Стоимость", f"{metrics['total_value']:,.0f} ₽", f"{metrics['total_pnl']:+,.0f} ₽")
        
        with col2:
            st.metric("Доходность", f"{metrics['total_pnl_pct']:+.2f}%", "vs покупка")
        
        with col3:
            st.metric("Дюрация", f"{metrics['weighted_duration']:.2f} лет", "средневзвеш.")
        
        with col4:
            st.metric("DV01", f"{metrics['dv01']:,.0f} ₽", "риск на 0.01%")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Распределение портфеля")
            fig_pie = px.pie(
                metrics['details'],
                values='market_value',
                names='short_name',
                hole=0.4
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("P&L по позициям")
            df = metrics['details']
            colors = ['green' if x > 0 else 'red' for x in df['pnl']]
            fig_bar = go.Figure(go.Bar(
                x=df['short_name'],
                y=df['pnl'],
                marker_color=colors,
                text=df['pnl'].apply(lambda x: f"{x:+,.0f} ₽"),
                textposition='auto'
            ))
            fig_bar.update_layout(height=400)
            fig_bar.add_hline(y=0, line_dash="dash")
            st.plotly_chart(fig_bar, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Прогресс к цели 5 000 000 ₽")
        progress = metrics['total_value'] / 5_000_000
        st.progress(min(progress, 1.0))
        st.caption(f"Достигнуто: {metrics['total_value']:,.0f} ₽ из 5 000 000 ₽ ({progress*100:.1f}%)")
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Купон в год", f"{metrics['annual_coupon']:,.0f} ₽")
        with col2:
            st.metric("Купон в месяц", f"{metrics['annual_coupon']/12:,.0f} ₽")
        with col3:
            st.metric("Купон в день", f"{metrics['annual_coupon']/365:,.0f} ₽")


# ==================== ПОЗИЦИИ ====================

elif page == "Позиции":
    st.title("Детали по позициям")
    
    if metrics:
        df = metrics['details'][['short_name', 'qty', 'buy_price', 'current_price', 
                                 'market_value', 'pnl', 'pnl_pct', 'duration', 'coupon_rate']].copy()
        df.columns = ['Облигация', 'Кол-во', 'Покупка %', 'Сейчас %', 
                      'Стоимость ₽', 'P&L ₽', 'P&L %', 'Дюрация', 'Купон %']
        
        st.dataframe(df, use_container_width=True)


# ==================== СТРЕСС-ТЕСТЫ ====================

elif page == "Стресс-тесты":
    st.title("Стресс-тестирование")
    
    if metrics:
        col1, col2 = st.columns(2)
        with col1:
            rate_shock = st.slider("Изменение ставки (%)", -5.0, 10.0, 0.0, 0.1)
        with col2:
            fx_shock = st.slider("Ослабление рубля (%)", 0.0, 50.0, 0.0, 1.0)
        
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
            st.metric("Текущая стоимость", f"{current_value:,.0f} ₽")
        with col2:
            st.metric("Изменение", f"{value_change:+,.0f} ₽", f"{change_pct:+.2f}%")
        with col3:
            st.metric("Новая стоимость", f"{new_value:,.0f} ₽")


# ==================== ПРОГНОЗ ЦЕЛИ ====================

elif page == "Прогноз цели":
    st.title("Прогноз достижения цели")
    
    if metrics:
        target = st.number_input("Цель (₽)", value=5_000_000, step=100_000)
        monthly = st.number_input("Ежемесячные вложения (₽)", value=100_000, step=10_000)
        
        forecasts = []
        for pos in st.session_state.portfolio:
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
        st.dataframe(df_forecast, use_container_width=True)


# ==================== СИМУЛЯЦИЯ RGBI ====================

elif page == "Симуляция RGBI":
    st.title("Сравнение: RGBI vs Портфель")
    
    if metrics:
        months = st.slider("Период (месяцев)", 3, 60, 12)
        
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
            st.metric("RGBI", f"{rgbi_final:,.0f} ₽", f"{rgbi_return:+.2f}%")
        with col2:
            st.metric("ОФЗ", f"{ofz_value:,.0f} ₽", f"{ofz_return:+.2f}%")
        with col3:
            label = "Перезаработок" if difference > 0 else "Недозаработок"
            st.metric("Разница", f"{difference:+,.0f} ₽", label)
        
        st.markdown("---")
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=[d['date'] for d in daily_values],
            y=[d['value'] for d in daily_values],
            mode='lines',
            name='RGBI'
        ))
        
        fig.update_layout(height=500, yaxis_title="Стоимость (₽)")
        st.plotly_chart(fig, use_container_width=True)
