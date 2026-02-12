import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da Página
st.set_page_config(layout="wide", page_title="Dashboard Union")

# Estilização CSS para aproximar do visual "clean" do seu projeto original
st.markdown("""
<style>
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stApp {
        background-color: #F5F5F7;
    }
</style>
""", unsafe_allow_html=True)

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def load_data():
    try:
        # Lê o arquivo local 'dados.csv' que você subiu no GitHub
        df = pd.read_csv("dados.csv")
        
        # Limpeza básica e conversão de tipos se necessário
        # Removemos linhas onde a Venda 2022 está vazia
        df = df.dropna(subset=['Venda 2022 R$'])
        
        return df
    except FileNotFoundError:
        st.error("Arquivo 'dados.csv' não encontrado. Por favor, faça o upload do arquivo CSV no GitHub com esse nome.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.stop()

# --- CÁLCULOS DOS KPIS ---
venda_total = df['Venda 2022 R$'].sum()
meta_total = df['Meta Venda 2022'].sum() if 'Meta Venda 2022' in df.columns else 0
margem_media = df['Margem Bruta 2022 %'].mean() * 100
qtd_clientes = df['Qtd de cupom 2022'].sum()
ticket_medio = venda_total / qtd_clientes if qtd_clientes > 0 else 0

# Variação (Exemplo simples comparando com 2021)
venda_2021 = df['Venda 2021 R$'].sum()
variacao_venda = ((venda_total - venda_2021) / venda_2021) * 100 if venda_2021 > 0 else 0

# --- HEADER ---
st.title("📊 Painel de Performance")
st.markdown("---")

# --- KPI CARDS ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Venda Total", 
        value=f"R$ {venda_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        delta=f"{variacao_venda:.1f}% vs 2021"
    )

with col2:
    st.metric(
        label="Margem Bruta", 
        value=f"{margem_media:.2f}%"
    )

with col3:
    st.metric(
        label="Ticket Médio", 
        value=f"R$ {ticket_medio:.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

with col4:
    st.metric(
        label="Nº Clientes", 
        value=f"{qtd_clientes:,.0f}".replace(",", ".")
    )

st.markdown("---")

# --- GRÁFICOS (LINHA 1) ---
col_charts_1, col_charts_2 = st.columns(2)

# Gráfico 1: Evolução Mensal (Venda vs Meta)
with col_charts_1:
    st.subheader("Evolução Mensal")
    # Agrupando por mês
    df_monthly = df.groupby('MÊS')[['Venda 2022 R$', 'Meta Venda 2022']].sum().reset_index()
    
    # Ordenação correta dos meses (se necessário, criar mapa de ordem)
    meses_ordem = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    df_monthly['MÊS'] = pd.Categorical(df_monthly['MÊS'], categories=meses_ordem, ordered=True)
    df_monthly = df_monthly.sort_values('MÊS')

    fig_evolution = go.Figure()
    fig_evolution.add_trace(go.Bar(
        x=df_monthly['MÊS'], 
        y=df_monthly['Venda 2022 R$'], 
        name='Realizado',
        marker_color='#4F46E5'
    ))
    fig_evolution.add_trace(go.Scatter(
        x=df_monthly['MÊS'], 
        y=df_monthly['Meta Venda 2022'], 
        name='Meta', 
        mode='lines+markers',
        line=dict(color='#EF4444', width=2)
    ))
    fig_evolution.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_evolution, use_container_width=True)

# Gráfico 2: Progresso da Meta (Gauge Chart)
with col_charts_2:
    st.subheader("Atingimento da Meta Global")
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = venda_total,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Vendas vs Meta"},
        delta = {'reference': meta_total, 'relative': True, "valueformat": ".1%"},
        gauge = {
            'axis': {'range': [None, meta_total * 1.2]},
            'bar': {'color': "#4F46E5"},
            'steps': [
                {'range': [0, meta_total], 'color': "lightgray"},
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': meta_total
            }
        }
    ))
    fig_gauge.update_layout(height=400)
    st.plotly_chart(fig_gauge, use_container_width=True)

# --- GRÁFICOS (LINHA 2) ---
col_charts_3, col_charts_4 = st.columns(2)

# Gráfico 3: Distribuição por Loja/Regional
with col_charts_3:
    st.subheader("Vendas por Loja")
    # Agrupando por Nome da Loja (Top 10)
    df_store = df.groupby('NOME LOJA')['Venda 2022 R$'].sum().sort_values(ascending=True).tail(10)
    
    fig_bar = px.bar(
        df_store, 
        x=df_store.values, 
        y=df_store.index, 
        orientation='h',
        color_discrete_sequence=['#10B981']
    )
    fig_bar.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

# Gráfico 4: Margem por Mês
with col_charts_4:
    st.subheader("Margem % por Mês")
    # Recalculando margem média ponderada por mês se necessário, ou média simples
    df_margin = df.groupby('MÊS')['Margem Bruta 2022 %'].mean().reset_index()
    df_margin['Margem Bruta 2022 %'] = df_margin['Margem Bruta 2022 %'] * 100
    
    # Ordenar
    df_margin['MÊS'] = pd.Categorical(df_margin['MÊS'], categories=meses_ordem, ordered=True)
    df_margin = df_margin.sort_values('MÊS')

    fig_line = px.line(
        df_margin, 
        x='MÊS', 
        y='Margem Bruta 2022 %',
        markers=True,
        color_discrete_sequence=['#F59E0B']
    )
    fig_line.update_layout(height=400)
    st.plotly_chart(fig_line, use_container_width=True)

# --- TABELA DE DADOS ---
st.subheader("Detalhamento por Loja")
st.dataframe(
    df[['MÊS', 'NOME LOJA', 'Venda 2022 R$', 'Margem Bruta 2022 %', 'Meta Venda 2022']], 
    use_container_width=True,
    hide_index=True
)
