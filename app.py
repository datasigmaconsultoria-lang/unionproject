import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Dashboard Union", initial_sidebar_state="expanded")

# --- ESTILIZAÇÃO CSS (Visual Figma) ---
st.markdown("""
<style>
    /* Fundo geral */
    .stApp {
        background-color: #F5F5F7;
    }
    
    /* Estilo dos Cards de KPI */
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #E5E7EB;
    }
    
    /* Títulos das Métricas */
    div[data-testid="metric-container"] label {
        font-size: 14px;
        color: #6B7280;
        font-weight: 500;
    }
    
    /* Valores das Métricas */
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #111827;
        font-weight: 700;
    }

    /* Ajuste de espaçamento */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE LIMPEZA DE DADOS ---
def clean_currency(x):
    """Converte strings como 'R$ 1.000,00' para float 1000.00"""
    if isinstance(x, str):
        # Remove R$, espaços e pontos de milhar
        clean_str = x.replace('R$', '').replace('.', '').replace(' ', '').strip()
        # Troca vírgula decimal por ponto
        clean_str = clean_str.replace(',', '.')
        try:
            return float(clean_str)
        except ValueError:
            return 0.0
    return x

def clean_percentage(x):
    """Converte strings como '25,5%' para float 25.5"""
    if isinstance(x, str):
        clean_str = x.replace('%', '').replace(',', '.').strip()
        try:
            return float(clean_str)
        except ValueError:
            return 0.0
    return x

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def load_data():
    try:
        # Procura arquivos CSV na pasta
        arquivos_csv = [f for f in os.listdir('.') if f.endswith('.csv') or f.endswith('.CSV')]
        
        if not arquivos_csv:
            st.error("❌ Nenhum arquivo CSV encontrado no GitHub.")
            st.stop()
            
        # Pega o primeiro CSV encontrado (prioridade para 'base.csv' ou 'dados.csv' se existirem)
        arquivo_alvo = arquivos_csv[0]
        for f in arquivos_csv:
            if 'base' in f.lower() or 'dados' in f.lower():
                arquivo_alvo = f
                break
                
        df = pd.read_csv(arquivo_alvo)
        
        # 1. REMOVER ESPAÇOS DOS NOMES DAS COLUNAS (Crucial!)
        df.columns = df.columns.str.strip()
        
        # 2. SELEÇÃO E LIMPEZA DAS COLUNAS NECESSÁRIAS
        # Mapeamento para garantir nomes fáceis de trabalhar
        col_map = {
            'Venda 2022 R$': 'Venda',
            'Meta Venda 2022': 'Meta',
            'Margem Bruta 2022 %': 'Margem_Percent',
            'Qtd de cupom 2022': 'Clientes',
            'NOME LOJA': 'Loja',
            'MÊS': 'Mes'
        }
        
        # Verifica se as colunas existem (mesmo com nomes levemente diferentes)
        cols_found = {}
        for key in col_map.keys():
            if key in df.columns:
                cols_found[key] = col_map[key]
            else:
                # Tenta achar ignorando case sensitive
                for col_original in df.columns:
                    if key.lower() in col_original.lower():
                        cols_found[col_original] = col_map[key]
                        break
        
        if not cols_found:
            st.error("Não foi possível identificar as colunas principais (Venda, Meta, Margem). Verifique o CSV.")
            st.write("Colunas encontradas:", df.columns.tolist())
            st.stop()
            
        # Renomeia para facilitar
        df = df.rename(columns=cols_found)
        
        # Aplica conversão numérica
        cols_numericas = ['Venda', 'Meta', 'Clientes']
        for col in cols_numericas:
            if col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].apply(clean_currency)
                else:
                    df[col] = df[col].fillna(0)

        if 'Margem_Percent' in df.columns:
            if df['Margem_Percent'].dtype == 'object':
                 df['Margem_Percent'] = df['Margem_Percent'].apply(clean_percentage)
        
        # Remove linhas vazias de venda
        df = df[df['Venda'] > 0]
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        st.stop()
        return pd.DataFrame()

# Carrega os dados
df = load_data()

# --- SIDEBAR (FILTROS) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2857/2857433.png", width=50) # Placeholder logo
st.sidebar.title("Filtros")

# Filtro de Mês
meses_disponiveis = df['Mes'].unique()
# Ordenação customizada de meses
ordem_meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
meses_ordenados = sorted([m for m in meses_disponiveis if m in ordem_meses], key=lambda x: ordem_meses.index(x))

mes_selecionado = st.sidebar.multiselect("Selecione o Mês", meses_ordenados, default=meses_ordenados)

# Filtro de Loja
lojas_disponiveis = sorted(df['Loja'].unique().astype(str))
loja_selecionada = st.sidebar.multiselect("Selecione a Loja", lojas_disponiveis, default=lojas_disponiveis)

# Aplicando Filtros
df_filtered = df.copy()
if mes_selecionado:
    df_filtered = df_filtered[df_filtered['Mes'].isin(mes_selecionado)]
if loja_selecionada:
    df_filtered = df_filtered[df_filtered['Loja'].isin(loja_selecionada)]

# --- CÁLCULOS KPI ---
venda_total = df_filtered['Venda'].sum()
meta_total = df_filtered['Meta'].sum()
# Média ponderada da margem seria o ideal, mas faremos média simples dos registros filtrados para simplificar visualização
margem_media = df_filtered['Margem_Percent'].mean()
clientes_total = df_filtered['Clientes'].sum()
ticket_medio = venda_total / clientes_total if clientes_total > 0 else 0

# --- INTERFACE PRINCIPAL ---

st.title("Performance de Vendas")
st.markdown(f"Visão Geral • **{'Todas as Lojas' if len(loja_selecionada) == len(lojas_disponiveis) else 'Lojas Selecionadas'}**")

# Espaçamento
st.markdown("###")

# KPI CARDS
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric("Venda Total", f"R$ {venda_total:,.2f}".replace(",", "_").replace(".", ",").replace("_", "."))

with kpi2:
    st.metric("Margem Média", f"{margem_media:.2f}%", delta_color="normal")

with kpi3:
    st.metric("Ticket Médio", f"R$ {ticket_medio:.2f}".replace(",", "_").replace(".", ",").replace("_", "."))

with kpi4:
    st.metric("Clientes (Cupons)", f"{clientes_total:,.0f}".replace(",", "."))

st.markdown("###")

# --- GRÁFICOS ---

col_g1, col_g2 = st.columns([2, 1])

# Gráfico de Evolução (Barras + Linha)
with col_g1:
    st.subheader("Evolução de Vendas vs Meta")
    
    # Agrupamento por mês
    df_chart = df_filtered.groupby('Mes')[['Venda', 'Meta']].sum().reset_index()
    # Ordenar meses
    df_chart['Mes'] = pd.Categorical(df_chart['Mes'], categories=ordem_meses, ordered=True)
    df_chart = df_chart.sort_values('Mes')
    
    fig_combo = go.Figure()
    
    # Barra Vendas
    fig_combo.add_trace(go.Bar(
        x=df_chart['Mes'],
        y=df_chart['Venda'],
        name='Venda Realizada',
        marker_color='#6366F1', # Cor indigo moderna
        radius=4
    ))
    
    # Linha Meta
    fig_combo.add_trace(go.Scatter(
        x=df_chart['Mes'],
        y=df_chart['Meta'],
        name='Meta',
        mode='lines+markers',
        line=dict(color='#10B981', width=3), # Verde esmeralda
        marker=dict(size=8)
    ))
    
    fig_combo.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#F3F4F6'),
        height=400
    )
    st.plotly_chart(fig_combo, use_container_width=True)

# Gráfico de Atingimento de Meta (Gauge)
with col_g2:
    st.subheader("Atingimento Global")
    
    percentual_atingimento = (venda_total / meta_total * 100) if meta_total > 0 else 0
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = percentual_atingimento,
        number = {'suffix': "%", 'font': {'size': 40, 'color': "#111827"}},
        gauge = {
            'axis': {'range': [None, 120], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#6366F1"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 100], 'color': "#E5E7EB"},
                {'range': [100, 120], 'color': "#D1FAE5"}
            ],
            'threshold': {
                'line': {'color': "#10B981", 'width': 4},
                'thickness': 0.75,
                'value': 100
            }
        }
    ))
    
    fig_gauge.update_layout(
        height=400, 
        margin=dict(t=40, b=20),
        paper_bgcolor='white',
        font={'family': "Arial"}
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

# --- TABELA DETALHADA ---
st.subheader("Detalhamento por Loja")
df_table = df_filtered.groupby('Loja')[['Venda', 'Meta', 'Clientes']].sum().reset_index()
df_table['Atingimento %'] = (df_table['Venda'] / df_table['Meta'] * 100).fillna(0)
df_table = df_table.sort_values('Venda', ascending=False)

# Formatação para exibição
st.dataframe(
    df_table.style.format({
        'Venda': 'R$ {:,.2f}',
        'Meta': 'R$ {:,.2f}',
        'Clientes': '{:,.0f}',
        'Atingimento %': '{:.1f}%'
    }),
    use_container_width=True,
    column_config={
        "Atingimento %": st.column_config.ProgressColumn(
            "Atingimento da Meta",
            format="%.1f%%",
            min_value=0,
            max_value=120,
        ),
    }
)
