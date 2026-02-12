import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Configuração da Página
st.set_page_config(layout="wide", page_title="Dashboard Larissa")

# 2. Conexão com a sua planilha Google
url = "https://docs.google.com/spreadsheets/d/1fjBec92s-t1PXyPRr80453Nh6aGM6GBRnabfLs_KNb0/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# Lendo a aba "BASE"
df = conn.read(spreadsheet=url, worksheet="BASE")

# 3. Cálculos dos KPIs (Baseado na sua planilha)
# Somamos a coluna de vendas de 2022
total_venda = df['Venda 2022 R$'].sum()
# Média da margem
margem_media = df['Margem Bruta 2022 %'].mean() * 100
# Soma de cupons (clientes)
total_clientes = df['Qtd de cupom 2022'].sum()
# Ticket médio
ticket_medio = total_venda / total_clientes if total_clientes > 0 else 0

# 4. Criando o visual no Streamlit
st.title("📊 Painel de Resultados - Larissa")

# Criando 4 colunas para os cartões
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Venda Total 2022", f"R$ {total_venda:,.2f}")

with col2:
    st.metric("Margem Média", f"{margem_media:.2f}%")

with col3:
    st.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")

with col4:
    st.metric("Nº de Cupons", f"{total_clientes:,.0f}")

# Exibir a tabela logo abaixo
st.subheader("Dados Consolidados")
st.dataframe(df)
