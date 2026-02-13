import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    layout="wide", 
    page_title="Union | Data Sigma", 
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS (UX & BRANDBOOK DATA SIGMA) ---
st.markdown("""
<style>
    /* Importando Fontes Google */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    /* Variáveis de Cor - Brandbook Data Sigma */
    :root {
        --sigma-blue: #0047AB; 
        --sigma-green: #00A859;
        --sigma-gradient: linear-gradient(90deg, #0047AB 0%, #00A859 100%);
        
        --color-bg: #F4F6F9;
        --color-surface: #FFFFFF;
        --color-text-main: #1F2937;
        --color-text-light: #6B7280;
        --color-border: #E5E7EB;
        --color-alert: #EF4444;
    }

    /* Reset Geral */
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        color: var(--color-text-main);
        background-color: var(--color-bg);
    }

    /* Fundo do App */
    .stApp {
        background-color: var(--color-bg);
    }
    
    /* Ajuste de Padding Principal (Correção do Header Cortado) */
    .block-container {
        padding-top: 1.5rem !important; /* Mais espaço no topo */
        padding-bottom: 3rem;
        max-width: 100%;
    }

    /* --- CABEÇALHO PERSONALIZADO --- */
    .header-sigma {
        display: flex;
        justify_content: space-between;
        align-items: center;
        background: var(--color-surface);
        padding: 1.2rem 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
        border-bottom: 3px solid transparent;
        border-image: var(--sigma-gradient);
        border-image-slice: 1;
    }
    
    .header-logo-left {
        font-weight: 800;
        font-size: 22px;
        background: var(--sigma-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }
    
    .header-title {
        font-size: 14px;
        color: var(--color-text-light);
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
        text-align: center;
    }

    .header-logo-right {
        font-weight: 700;
        color: var(--color-text-main);
        font-size: 16px;
    }

    /* Mobile Header Fix */
    @media (max-width: 768px) {
        .header-sigma {
            flex-direction: column;
            gap: 10px;
            text-align: center;
        }
    }

    /* CARDS (Big Numbers) */
    div[data-testid="metric-container"] {
        background-color: var(--color-surface);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid var(--color-border);
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        border-left: 4px solid var(--sigma-blue);
        transition: transform 0.2s ease;
        height: 100%; /* Altura consistente */
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.08);
    }

    div[data-testid="metric-container"] label {
        font-size: 13px !important;
        font-weight: 600 !important;
        color: var(--color-text-light) !important;
    }
    
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 700 !important;
        color: var(--color-text-main) !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: var(--color-surface);
        border-right: 1px solid var(--color-border);
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem !important;
    }

    /* Inputs e Selectboxes (UX Melhorada) */
    .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px;
        border: 1px solid var(--color-border);
        min-height: 45px; /* Altura de toque maior */
    }
    
    .stSelectbox div[data-baseweb="select"]:hover {
        border-color: var(--sigma-blue);
    }

    /* Botões */
    .stButton button {
        background: var(--sigma-blue);
        color: white;
        border-radius: 8px;
        border: none;
        height: 45px;
        font-weight: 600;
        transition: all 0.3s;
        width: 100%;
    }
    
    .stButton button:hover {
        background: var(--sigma-green);
        box-shadow: 0 4px 10px rgba(0, 168, 89, 0.3);
    }

    /* Tabs (Abas) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--color-border);
        margin-bottom: 20px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        background-color: white;
        border: 1px solid var(--color-border);
        color: var(--color-text-light);
        font-weight: 500;
        font-size: 14px;
        padding: 0 24px;
    }

    .stTabs [aria-selected="true"] {
        background: var(--sigma-gradient);
        color: white;
        border: none;
        box-shadow: 0 2px 6px rgba(0, 71, 171, 0.3);
    }
    
    /* Remover fundo branco padrão dos gráficos Plotly se houver container extra */
    .js-plotly-plot .plotly .main-svg {
        background: transparent !important;
    }

</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE LIMPEZA ROBUSTAS ---
def clean_currency_br(x):
    """Limpeza extrema para evitar erros de conversão"""
    if pd.isna(x) or x == "": return 0.0
    if isinstance(x, (int, float)): return float(x)
    s = str(x).strip().replace('"', '').replace("'", "").replace('R$', '').replace(' ', '')
    s = s.replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

def clean_percentage_br(x):
    if pd.isna(x) or x == "": return 0.0
    if isinstance(x, (int, float)): return float(x)
    s = str(x).strip().replace('"', '').replace('%', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def load_data():
    datasets = {}
    
    # 1. BASE GERAL
    try:
        files = [f for f in os.listdir('.') if f.endswith('.csv') or f.endswith('.CSV')]
        base_file = next((f for f in files if 'base' in f.lower() or 'dados' in f.lower()), None)
        
        if base_file:
            try:
                df_base = pd.read_csv(base_file, encoding='utf-8', on_bad_lines='skip')
            except:
                df_base = pd.read_csv(base_file, encoding='latin1', on_bad_lines='skip')
                
            df_base.columns = df_base.columns.str.strip()
            
            col_map = {
                'Venda 2022 R$': 'Venda', 'Meta Venda 2022': 'Meta',
                'Margem Bruta 2022 %': 'Margem_Perc', 'Qtd de cupom 2022': 'Clientes',
                'NOME LOJA': 'Loja', 'MÊS': 'Mes'
            }
            cols_found = {}
            for k, v in col_map.items():
                match = next((c for c in df_base.columns if k.lower() in c.lower()), None)
                if match: cols_found[match] = v
            
            df_base = df_base.rename(columns=cols_found)
            for col in ['Venda', 'Meta', 'Clientes']:
                if col in df_base.columns: df_base[col] = df_base[col].apply(clean_currency_br)
            if 'Margem_Perc' in df_base.columns:
                df_base['Margem_Perc'] = df_base['Margem_Perc'].apply(clean_percentage_br)
                
            datasets['base'] = df_base
    except Exception as e:
        st.error(f"Erro base principal: {e}")

    # 2. CLASSIFICAÇÃO MERCADOLÓGICA
    try:
        class_file = next((f for f in files if 'classificacao' in f.lower()), None)
        if class_file:
            try:
                df_test = pd.read_csv(class_file, encoding='utf-8', on_bad_lines='skip', nrows=5)
                if 'Classificação' in df_test.columns or 'Código' in df_test.columns:
                    df_class = pd.read_csv(class_file, encoding='utf-8', on_bad_lines='skip')
                else:
                    df_class = pd.read_csv(class_file, encoding='utf-8', on_bad_lines='skip', skiprows=1)
            except:
                df_class = pd.read_csv(class_file, encoding='latin1', on_bad_lines='skip', skiprows=1)

            df_class.columns = df_class.columns.str.strip()
            
            class_map = {
                'Classificação': 'Hierarquia', 'Grupo': 'Descricao', 
                'Valor': 'Venda', '% Partic': 'Part', '% Lucro': 'Lucro'
            }
            cols_found = {}
            for k, v in class_map.items():
                match = next((c for c in df_class.columns if k.lower() in c.lower()), None)
                if match: cols_found[match] = v
            
            df_class = df_class.rename(columns=cols_found)
            
            if 'Venda' in df_class.columns:
                df_class['Venda'] = df_class['Venda'].apply(clean_currency_br)
            if 'Hierarquia' in df_class.columns:
                df_class = df_class.dropna(subset=['Hierarquia'])
                df_class['Hierarquia'] = df_class['Hierarquia'].astype(str)
                df_class['Nivel'] = df_class['Hierarquia'].apply(lambda x: x.count('.') + 1 if '.' in x else 1)
                
            datasets['mix'] = df_class
    except Exception as e:
        pass

    return datasets

data = load_data()
df = data.get('base', pd.DataFrame())
df_mix = data.get('mix', pd.DataFrame())

if df.empty:
    st.warning("⚠️ Arquivo 'base.csv' não encontrado ou vazio. Faça upload no GitHub.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.markdown("### 🔍 Filtros de Análise")
st.sidebar.markdown("---")

sel_mes = 'Todos'
sel_loja = 'Todas'

if 'Mes' in df.columns:
    meses_unicos = df['Mes'].unique()
    ordem_meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    meses_sorted = sorted([m for m in meses_unicos if isinstance(m, str)], 
                          key=lambda x: ordem_meses.index(x.upper()) if x.upper() in ordem_meses else 99)
    sel_mes = st.sidebar.selectbox("Período (Mês)", ['Todos'] + meses_sorted)

if 'Loja' in df.columns:
    lojas = sorted([l for l in df['Loja'].unique() if isinstance(l, str)])
    sel_loja = st.sidebar.selectbox("Unidade de Negócio", ['Todas'] + lojas)

st.sidebar.markdown("---")
st.sidebar.info("**Nota Data Sigma:** Dados processados via Pipeline ETL.")

# Aplica Filtros
df_filtered = df.copy()
if sel_mes != 'Todos': df_filtered = df_filtered[df_filtered['Mes'] == sel_mes]
if sel_loja != 'Todas': df_filtered = df_filtered[df_filtered['Loja'] == sel_loja]

# --- CABEÇALHO PERSONALIZADO (BRANDBOOK) ---
st.markdown(f"""
<div class="header-sigma">
    <div class="header-logo-left">DATA SIGMA</div>
    <div class="header-title">DASHBOARD EXECUTIVO • UNION</div>
    <div class="header-logo-right">LARISSA SUPERMERCADOS</div>
</div>
""", unsafe_allow_html=True)

# --- CORES DA MARCA PARA GRÁFICOS ---
COLOR_BLUE = "#0047AB" # Azul Sigma
COLOR_GREEN = "#00A859" # Verde Sigma
COLOR_ALERT = "#EF4444" # Vermelho Alerta
COLOR_NEUTRAL = "#E5E7EB" # Cinza Neutro
COLOR_TEXT = "#1F2937"
COLOR_GRADIENT = ["#0047AB", "#006494", "#00817D", "#009C65", "#00A859"] # Gradiente Data Sigma

# Configuração global de layout para gráficos transparentes
def update_fig_layout(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', # Transparente
        plot_bgcolor='rgba(0,0,0,0)',  # Transparente
        font={'color': COLOR_TEXT, 'family': 'Roboto'},
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', zeroline=False),
    )
    return fig

tab1, tab2, tab3 = st.tabs(["📊 Visão Executiva", "📦 Análise de Mix", "📋 Detalhes Operacionais"])

# --- TAB 1: EXECUTIVA ---
with tab1:
    # 1. KPIs
    venda = df_filtered['Venda'].sum() if 'Venda' in df_filtered.columns else 0
    meta = df_filtered['Meta'].sum() if 'Meta' in df_filtered.columns else 0
    clientes = df_filtered['Clientes'].sum() if 'Clientes' in df_filtered.columns else 0
    ticket = venda / clientes if clientes > 0 else 0
    
    if 'Margem_Perc' in df_filtered.columns:
        margem = df_filtered['Margem_Perc'].mean()
    else: margem = 0

    c1, c2, c3, c4 = st.columns(4)
    
    with c1: st.metric("Venda Total", f"R$ {venda:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with c2: st.metric("Margem", f"{margem:.1f}%")
    with c3: st.metric("Ticket Médio", f"R$ {ticket:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with c4: st.metric("Clientes Atendidos", f"{clientes:,.0f}".replace(",", "."))
    
    st.markdown("###")

    # 2. LINHA 1 DE GRÁFICOS
    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        st.markdown("##### 📈 Evolução vs Metas")
        if 'Mes' in df_filtered.columns:
            idx_col = 'Mes' if sel_mes == 'Todos' else 'Loja'
            df_chart = df_filtered.groupby(idx_col)[['Venda', 'Meta']].sum().reset_index()
            
            if idx_col == 'Mes':
                df_chart['sort'] = df_chart['Mes'].apply(lambda x: ordem_meses.index(x.upper()) if x.upper() in ordem_meses else 99)
                df_chart = df_chart.sort_values('sort')
            else:
                df_chart = df_chart.sort_values('Venda', ascending=False)

            fig = go.Figure()
            # Azul para Realizado
            fig.add_trace(go.Bar(
                x=df_chart[idx_col], y=df_chart['Venda'], 
                name='Realizado', 
                marker_color=COLOR_BLUE,
                opacity=0.9
            ))
            # Verde para Meta
            fig.add_trace(go.Scatter(
                x=df_chart[idx_col], y=df_chart['Meta'], 
                name='Meta', 
                mode='lines+markers', 
                line=dict(color=COLOR_GREEN, width=3),
                marker=dict(size=6, color='white', line=dict(width=2, color=COLOR_GREEN))
            ))
            
            fig = update_fig_layout(fig)
            fig.update_layout(height=320, legend=dict(orientation="h", y=1.1, x=1, xanchor='right'))
            st.plotly_chart(fig, use_container_width=True)
            
    with col_g2:
        st.markdown("##### 🎯 Atingimento Global")
        perc = (venda / meta * 100) if meta > 0 else 0
        perc_visual = min(perc, 999)
        
        gauge_color = COLOR_GREEN if perc >= 100 else (COLOR_BLUE if perc >= 80 else COLOR_ALERT)

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=perc_visual,
            number={'suffix': "%", 'font': {'size': 36, 'family': 'Roboto', 'color': COLOR_TEXT}},
            gauge={
                'axis': {'range': [0, 120]}, 
                'bar': {'color': gauge_color}, 
                'steps': [{'range': [0, 100], 'color': "rgba(200, 200, 200, 0.2)"}], # Fundo do arco mais suave
                'threshold': {'line': {'color': COLOR_GREEN, 'width': 4}, 'thickness': 0.75, 'value': 100}
            }
        ))
        fig_gauge = update_fig_layout(fig_gauge)
        fig_gauge.update_layout(height=320, margin=dict(t=40,b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

    # 3. LINHA 2 DE GRÁFICOS
    col_g3, col_g4 = st.columns(2)
    
    with col_g3:
        st.markdown("##### 🍰 Distribuição por Departamento (Top 5)")
        if not df_mix.empty and 'Descricao' in df_mix.columns:
            if 'Nivel' in df_mix.columns:
                df_depto = df_mix[df_mix['Nivel'] == 1].copy()
                if df_depto.empty: df_depto = df_mix.copy()
            else:
                df_depto = df_mix.copy()
            
            df_depto = df_depto.sort_values('Venda', ascending=False).head(5)
            
            fig_donut = px.pie(
                df_depto, values='Venda', names='Descricao', hole=0.6, 
                color_discrete_sequence=COLOR_GRADIENT
            )
            fig_donut = update_fig_layout(fig_donut)
            fig_donut.update_layout(height=320, margin=dict(t=0,b=0,l=0,r=0), showlegend=True)
            fig_donut.update_traces(textinfo='percent+label', textposition='inside')
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("Aguardando arquivo de Classificação Mercadológica.")
            
    with col_g4:
        st.markdown("##### 🏆 Ranking de Lojas")
        if 'Loja' in df_filtered.columns:
            df_rank = df_filtered.groupby('Loja')['Venda'].sum().sort_values(ascending=True).reset_index()
            fig_bar = px.bar(
                df_rank, x='Venda', y='Loja', orientation='h', 
                text_auto='.2s', color_discrete_sequence=[COLOR_BLUE]
            )
            fig_bar = update_fig_layout(fig_bar)
            fig_bar.update_layout(height=320, xaxis=dict(showgrid=False))
            st.plotly_chart(fig_bar, use_container_width=True)

# --- TAB 2: MIX ---
with tab2:
    if df_mix.empty:
        st.warning("⚠️ Arquivo de Classificação Mercadológica não encontrado.")
    else:
        st.markdown("##### 🌳 Árvore de Produtos (Bill of Materials)")
        st.caption("Visão hierárquica do portfólio de produtos.")
        
        nivel_selecionado = st.slider("Nível de Detalhe:", 1, 4, 2)
        
        df_tree = df_mix[(df_mix['Nivel'] == nivel_selecionado) & (df_mix['Venda'] > 0)].copy()
        if df_tree.empty:
            df_tree = df_mix[df_mix['Venda'] > 0].nlargest(100, 'Venda')
            
        fig_tree = px.treemap(
            df_tree,
            path=['Descricao'],
            values='Venda',
            color='Venda',
            color_continuous_scale='Blues',
            hover_data=['Hierarquia', 'Part']
        )
        fig_tree.update_traces(textinfo="label+value+percent entry")
        fig_tree = update_fig_layout(fig_tree)
        fig_tree.update_layout(height=600, margin=dict(t=0, l=0, r=0, b=0))
        st.plotly_chart(fig_tree, use_container_width=True)
        
        st.markdown("### Tabela Analítica")
        st.dataframe(df_mix[['Hierarquia', 'Descricao', 'Venda', 'Part']].sort_values('Venda', ascending=False), use_container_width=True)

# --- TAB 3: DETALHES ---
with tab3:
    st.markdown("##### 📋 Detalhamento Operacional")
    if 'Loja' in df_filtered.columns:
        df_table = df_filtered.groupby('Loja')[['Venda', 'Meta', 'Clientes']].sum().reset_index()
        df_table['Atingimento'] = (df_table['Venda'] / df_table['Meta'])
        df_table['Atingimento'] = df_table['Atingimento'].replace([np.inf, -np.inf], 0).fillna(0)
        
        st.dataframe(
            df_table.style.format({
                'Venda': 'R$ {:,.2f}', 
                'Meta': 'R$ {:,.2f}', 
                'Clientes': '{:,.0f}', 
                'Atingimento': '{:.1%}'
            }),
            use_container_width=True,
            column_config={
                "Atingimento": st.column_config.ProgressColumn(
                    "Meta %", 
                    format="%.1f%%", 
                    min_value=0, max_value=1.5
                ),
                "Venda": st.column_config.NumberColumn("Venda Real", format="R$ %.2f")
            },
            hide_index=True
        )
