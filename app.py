import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    layout="wide", 
    page_title="Larissa Supermercados - Union", 
    initial_sidebar_state="expanded",
    page_icon="🛒"
)

# --- ESTILIZAÇÃO CSS (GOOGLE MATERIAL 3 - M3) ---
st.markdown("""
<style>
    /* Importando fonte Roboto (Google Fonts) */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

    /* Reset básico e Fonte */
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }

    /* Fundo Geral (M3 Surface) */
    .stApp {
        background-color: #F7F9FC; /* Azul acinzentado muito claro */
    }

    /* Cards de KPI (M3 Elevation + Rounded) */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        padding: 24px;
        border-radius: 24px; /* M3 Rounded Corners */
        box-shadow: 0 4px 8px rgba(0,0,0,0.02); /* Sombra suave */
        border: 1px solid #E0E3E7;
        transition: transform 0.2s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.05);
    }

    /* Texto do Label da Métrica */
    div[data-testid="metric-container"] label {
        font-size: 14px;
        color: #444746; /* M3 OnSurfaceVariant */
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Valor da Métrica */
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        font-size: 32px;
        color: #1F1F1F; /* M3 OnSurface */
        font-weight: 700;
    }

    /* Delta (Variação) */
    div[data-testid="stMetricDelta"] {
        background-color: #F2F6FC;
        padding: 4px 8px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 600;
    }

    /* Ajuste do Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E0E3E7;
    }

    /* Títulos */
    h1, h2, h3 {
        color: #001D35; /* Azul profundo */
        font-weight: 700;
    }
    
    /* Remover padding excessivo do topo */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE LIMPEZA E TRATAMENTO ---
def clean_currency(x):
    """Limpeza robusta para valores monetários com aspas, espaços e símbolos"""
    if isinstance(x, (int, float)):
        return float(x)
        
    if isinstance(x, str):
        # Remove aspas extras que podem vir do CSV
        clean_str = x.replace('"', '').replace("'", "")
        # Remove R$, espaços e pontos de milhar
        clean_str = clean_str.replace('R$', '').replace('.', '').replace(' ', '').strip()
        # Troca vírgula decimal por ponto
        clean_str = clean_str.replace(',', '.')
        
        # Se string vazia, retorna 0
        if not clean_str:
            return 0.0
            
        try:
            return float(clean_str)
        except ValueError:
            return 0.0
    return 0.0

def clean_percentage(x):
    """Limpeza robusta para porcentagens"""
    if isinstance(x, (int, float)):
        return float(x)
        
    if isinstance(x, str):
        clean_str = x.replace('"', '').replace('%', '').replace(',', '.').strip()
        try:
            return float(clean_str)
        except ValueError:
            return 0.0
    return 0.0

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def load_data():
    try:
        # Busca automática do CSV
        arquivos_csv = [f for f in os.listdir('.') if f.endswith('.csv') or f.endswith('.CSV')]
        
        if not arquivos_csv:
            st.error("❌ Nenhum arquivo CSV encontrado.")
            st.stop()
            
        # Prioriza arquivos com 'base' ou 'dados' no nome
        arquivo_alvo = arquivos_csv[0]
        for f in arquivos_csv:
            if 'base' in f.lower() or 'dados' in f.lower():
                arquivo_alvo = f
                break
                
        # Lê o CSV ignorando linhas ruins
        df = pd.read_csv(arquivo_alvo, on_bad_lines='skip')
        
        # 1. Normalização dos nomes das colunas
        df.columns = df.columns.str.strip()
        
        # 2. Mapeamento flexível das colunas essenciais
        col_map = {
            'Venda 2022 R$': 'Venda',
            'Meta Venda 2022': 'Meta',
            'Margem Bruta 2022 %': 'Margem_Percent',
            'Qtd de cupom 2022': 'Clientes',
            'NOME LOJA': 'Loja',
            'MÊS': 'Mes'
        }
        
        # Tenta encontrar as colunas
        cols_found = {}
        for key, target in col_map.items():
            # Busca exata
            if key in df.columns:
                cols_found[key] = target
            else:
                # Busca aproximada (case insensitive)
                for col_original in df.columns:
                    if key.lower() in col_original.lower():
                        cols_found[col_original] = target
                        break
        
        if not cols_found:
            st.warning("Colunas não identificadas automaticamente. Verifique o CSV.")
            return pd.DataFrame() # Retorna vazio para não quebrar
            
        df = df.rename(columns=cols_found)
        
        # 3. Conversão de Tipos (Crucial para evitar ValueError)
        cols_numericas = ['Venda', 'Meta', 'Clientes']
        for col in cols_numericas:
            if col in df.columns:
                df[col] = df[col].apply(clean_currency)
                # Garante que não tem NaN ou Infinito
                df[col] = df[col].fillna(0)

        if 'Margem_Percent' in df.columns:
            df['Margem_Percent'] = df['Margem_Percent'].apply(clean_percentage)
            df['Margem_Percent'] = df['Margem_Percent'].fillna(0)
            
        # Filtra apenas dados válidos de venda
        df = df[df['Venda'] > 0]
        
        return df
        
    except Exception as e:
        st.error(f"Erro crítico no carregamento: {e}")
        st.stop()

df = load_data()

# --- SIDEBAR (FILTROS UX MELHORADA) ---
st.sidebar.markdown("### Filtros")

# 1. Filtro de Mês (Dropdown único com opção 'Todos')
if 'Mes' in df.columns:
    meses_disponiveis = df['Mes'].unique()
    # Ordem cronológica
    ordem_meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    # Ordena apenas os meses presentes nos dados
    meses_ordenados = sorted([m for m in meses_disponiveis if m in ordem_meses], key=lambda x: ordem_meses.index(x))
    
    # Adiciona opção 'Todos' no início
    opcoes_mes = ['Todos'] + meses_ordenados
    
    mes_selecionado = st.sidebar.selectbox("Selecione o Mês", options=opcoes_mes)
else:
    mes_selecionado = 'Todos'

# 2. Filtro de Loja (Dropdown único com opção 'Todas')
if 'Loja' in df.columns:
    lojas_disponiveis = sorted(df['Loja'].unique().astype(str))
    opcoes_loja = ['Todas'] + lojas_disponiveis
    loja_selecionada = st.sidebar.selectbox("Selecione a Loja", options=opcoes_loja)
else:
    loja_selecionada = 'Todas'

# --- APLICAÇÃO DOS FILTROS ---
df_filtered = df.copy()

if mes_selecionado != 'Todos':
    df_filtered = df_filtered[df_filtered['Mes'] == mes_selecionado]

if loja_selecionada != 'Todas':
    df_filtered = df_filtered[df_filtered['Loja'] == loja_selecionada]

# --- VERIFICAÇÃO DE DADOS APÓS FILTRO ---
if df_filtered.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# --- CÁLCULOS KPI ---
venda_total = df_filtered['Venda'].sum()
meta_total = df_filtered['Meta'].sum()
margem_media = df_filtered['Margem_Percent'].mean()
clientes_total = df_filtered['Clientes'].sum()
ticket_medio = venda_total / clientes_total if clientes_total > 0 else 0

# --- HEADER PRINCIPAL ---
st.title("Larissa Supermercados")
st.markdown(f"**Visão Gerencial Union** • {mes_selecionado if mes_selecionado != 'Todos' else 'Ano 2022'} • {loja_selecionada}")
st.markdown("---")

# --- KPI CARDS (Big Numbers) ---
c1, c2, c3, c4 = st.columns(4)

def formata_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formata_numero(valor):
    return f"{valor:,.0f}".replace(",", ".")

with c1:
    st.metric("Venda Total", formata_moeda(venda_total))
with c2:
    st.metric("Margem Média", f"{margem_media:.2f}%")
with c3:
    st.metric("Ticket Médio", formata_moeda(ticket_medio))
with c4:
    st.metric("Clientes", formata_numero(clientes_total))

st.markdown("###") # Espaçamento

# --- GRÁFICOS ---
col_charts_1, col_charts_2 = st.columns([2, 1])

# 1. Gráfico de Evolução (Material Design Style)
with col_charts_1:
    st.subheader("Evolução Mensal")
    
    if 'Mes' in df_filtered.columns:
        df_chart = df_filtered.groupby('Mes')[['Venda', 'Meta']].sum().reset_index()
        # Reordena
        df_chart['Mes'] = pd.Categorical(df_chart['Mes'], categories=ordem_meses, ordered=True)
        df_chart = df_chart.sort_values('Mes')
        
        fig = go.Figure()
        
        # Barras arredondadas (Venda)
        fig.add_trace(go.Bar(
            x=df_chart['Mes'], y=df_chart['Venda'],
            name='Venda',
            marker_color='#6750A4', # M3 Primary Purple
            marker_pattern_shape="", 
            width=0.5
        ))
        
        # Linha Suave (Meta)
        fig.add_trace(go.Scatter(
            x=df_chart['Mes'], y=df_chart['Meta'],
            name='Meta',
            mode='lines+markers',
            line=dict(color='#B3261E', width=3, shape='spline'), # M3 Error Red
            marker=dict(size=8, color='#FFFFFF', line=dict(width=2, color='#B3261E'))
        ))
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", y=1.1),
            height=350,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#E0E3E7')
        )
        st.plotly_chart(fig, use_container_width=True)

# 2. Gráfico Gauge (Atingimento)
with col_charts_2:
    st.subheader("Atingimento Meta")
    percentual = (venda_total / meta_total * 100) if meta_total > 0 else 0
    
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percentual,
        number={'suffix': "%", 'font': {'size': 40, 'color': "#1F1F1F", 'family': "Roboto"}},
        gauge={
            'axis': {'range': [None, 120], 'tickwidth': 0},
            'bar': {'color': "#6750A4"}, # Primary
            'bgcolor': "white",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 100], 'color': "#EADDFF"}, # Primary Container (Light Purple)
                {'range': [100, 120], 'color': "#C4EED0"} # Success Light Green
            ],
            'threshold': {
                'line': {'color': "#21005D", 'width': 4},
                'thickness': 0.75,
                'value': 100
            }
        }
    ))
    fig_gauge.update_layout(height=350, margin=dict(t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_gauge, use_container_width=True)

# --- TABELA DETALHADA ---
st.subheader("Detalhamento por Loja")

if 'Loja' in df_filtered.columns:
    # Agrupa e trata os dados
    df_table = df_filtered.groupby('Loja')[['Venda', 'Meta', 'Clientes']].sum().reset_index()
    
    # Previne divisão por zero e cria coluna float explícita
    df_table['Atingimento'] = df_table.apply(
        lambda row: (row['Venda'] / row['Meta']) if row['Meta'] > 0 else 0.0, axis=1
    )
    
    # Ordena
    df_table = df_table.sort_values('Venda', ascending=False)
    
    # Configuração da Tabela
    st.dataframe(
        df_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Loja": st.column_config.TextColumn("Loja", width="medium"),
            "Venda": st.column_config.NumberColumn(
                "Venda Realizada", format="R$ %.2f"
            ),
            "Meta": st.column_config.NumberColumn(
                "Meta", format="R$ %.2f"
            ),
            "Clientes": st.column_config.NumberColumn(
                "Cupons", format="%.0f"
            ),
            "Atingimento": st.column_config.ProgressColumn(
                "Atingimento %",
                format="%.1f%%",
                min_value=0,
                max_value=1.5, # Define 150% como máximo da barra visual
            )
        }
    )
