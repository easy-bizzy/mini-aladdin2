import streamlit as st
import pandas as pd

st.set_page_config(page_title="Тест", page_icon="✅", layout="wide")

st.title("✅ Mini-Aladdin работает!")
st.success("Поздравляю! Приложение успешно запущено.")

# Простые данные
st.metric("💰 Стоимость портфеля", "1 234 567 ₽", "+12 345 ₽")
st.metric("📈 Доходность", "+8.45%", "+1.2%")
st.metric("⏱️ Дюрация", "6.02 лет", "средневзвеш.")

st.subheader("📊 Тестовая таблица")
df = pd.DataFrame({
    'Облигация': ['ОФЗ 26238', 'ОФЗ 26246', 'ОФЗ 26247'],
    'Кол-во': [41, 65, 149],
    'Цена': [59.2, 88.4, 89.0],
    'P&L': [1200, -500, 3400]
})
st.dataframe(df, use_container_width=True)

st.info("Если вы видите эту страницу — всё работает! Теперь можно загружать полный код.")
