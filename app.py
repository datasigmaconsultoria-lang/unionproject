import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# --- CONFIGURAÇÃO DA PÁGINA (WIDE & M3 TITLE) ---
st.set_page_config(
    layout="wide", 
    page_title="Union | Larissa Supermercados", 
    page_icon="🛍️",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS AVANÇADA (GOOGLE MATERIAL 3) ---
st.markdown("""
<style>
    /* Importando Fontes Google */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    /* Variáveis de Cor M3 */
    :root {
        --md-sys-color-primary: #6750A4;
        --md-sys-color-on-primary: #FFFFFF;
        --md-sys-color-surface: #F3F4F6;
        --md-sys-color-surface-container: #FFFFFF;
        --md-sys-color-on-surface: #1C1B1F;
        --md-sys-color-outline: #E0E3E7;
        --chart-color-1: #6750A4;
        --chart-color-2: #9C27B0;
        --chart-color-3: #E91E63;
        --chart-color-4: #3F51B5;
        --chart-color-5: #2196F3;
    }

    /* Reset Geral */
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        color: var(--md-sys-color-on-surface);
        background-color: var(--md-sys-color-surface);
    }

    /* Fundo do App */
    .stApp {
        background-color: #F0F2F5;
    }

    /* CARDS (Big Numbers) */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        height: 100%;
    }
    
    div[data-testid="metric-container"]:hover {
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }

    div[data-testid="metric-container"] label {
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #6B7280;
    }
    
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: #111827;
        margin-top: 4px;
    }

    /* Sidebar Customizada */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E5E7EB;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #111827;
        font-weight: 700;
        letter-spacing: -0.025em;
    }

    /* Tabs (Abas) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 20px;
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        padding: 0 24px;
        font-weight: 500;
        font-size: 14px;
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--md-sys-color-primary);
        color: #FFFFFF;
        border: none;
    }

    /* Ajuste de Padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE LIMPEZA ROBUSTAS ---
def clean_currency_br(x):
    """Limpeza extrema para evitar erros de conversão"""
    if pd.isna(x) or x == "": return 0.0
    if isinstance(x, (int, float)): return float(x)
    # Remove aspas, R$, espaços
    s = str(x).strip().replace('"', '').replace("'", "").replace('R$', '').replace(' ', '')
    # Remove pontos de milhar e troca vírgula decimal
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
    
    # 1. BASE GERAL (VENDAS/METAS)
    try:
        files = [f for f in os.listdir('.') if f.endswith('.csv') or f.endswith('.CSV')]
        base_file = next((f for f in files if 'base' in f.lower() or 'dados' in f.lower()), None)
        
        if base_file:
            # Lê com encoding latin1 ou utf-8 dependendo do arquivo (utf-8 é padrão, mas latin1 é comum em excel BR)
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

    # 2. CLASSIFICAÇÃO MERCADOLÓGICA (NOVA)
    try:
        # Procura arquivo que tenha 'classificacao' no nome
        class_file = next((f for f in files if 'classificacao' in f.lower()), None)
        
        if class_file:
            # Tenta ler pulando a primeira linha se ela for vazia (comum no seu arquivo)
            try:
                # Tenta ler normal primeiro
                df_test = pd.read_csv(class_file, encoding='utf-8', on_bad_lines='skip', nrows=5)
                if 'Classificação' in df_test.columns or 'Código' in df_test.columns:
                    df_class = pd.read_csv(class_file, encoding='utf-8', on_bad_lines='skip')
                else:
                    # Se não achar header na linha 0, tenta skiprows=1 (padrão do seu arquivo)
                    df_class = pd.read_csv(class_file, encoding='utf-8', on_bad_lines='skip', skiprows=1)
            except:
                df_class = pd.read_csv(class_file, encoding='latin1', on_bad_lines='skip', skiprows=1)

            df_class.columns = df_class.columns.str.strip()
            
            # Mapeamento
            class_map = {
                'Classificação': 'Hierarquia', 'Grupo': 'Descricao', 
                'Valor': 'Venda', '% Partic': 'Part', '% Lucro': 'Lucro'
            }
            cols_found = {}
            for k, v in class_map.items():
                match = next((c for c in df_class.columns if k.lower() in c.lower()), None)
                if match: cols_found[match] = v
            
            df_class = df_class.rename(columns=cols_found)
            
            # Limpeza Numérica
            if 'Venda' in df_class.columns:
                df_class['Venda'] = df_class['Venda'].apply(clean_currency_br)
            
            # Filtra linhas válidas
            if 'Hierarquia' in df_class.columns:
                df_class = df_class.dropna(subset=['Hierarquia'])
                # Garante que hierarquia é string para contar pontos
                df_class['Hierarquia'] = df_class['Hierarquia'].astype(str)
                # Cria Nível baseado na hierarquia (ex: 1.10.100 -> Nível 3)
                df_class['Nivel'] = df_class['Hierarquia'].apply(lambda x: x.count('.') + 1 if '.' in x else 1)
                
            datasets['mix'] = df_class
    except Exception as e:
        # Apenas loga no console para não assustar o user se não tiver o arquivo ainda
        print(f"Erro classificacao: {e}")

    return datasets

data = load_data()
df = data.get('base', pd.DataFrame())
df_mix = data.get('mix', pd.DataFrame())

if df.empty:
    st.warning("⚠️ Arquivo 'base.csv' não encontrado ou vazio. Faça upload no GitHub.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3144/3144456.png", width=60)
st.sidebar.markdown("### Filtros Globais")

# Filtros
sel_mes = 'Todos'
sel_loja = 'Todas'

if 'Mes' in df.columns:
    meses_unicos = df['Mes'].unique()
    ordem_meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    meses_sorted = sorted([m for m in meses_unicos if isinstance(m, str)], 
                          key=lambda x: ordem_meses.index(x.upper()) if x.upper() in ordem_meses else 99)
    sel_mes = st.sidebar.selectbox("Mês", ['Todos'] + meses_sorted)

if 'Loja' in df.columns:
    lojas = sorted([l for l in df['Loja'].unique() if isinstance(l, str)])
    sel_loja = st.sidebar.selectbox("Loja", ['Todas'] + lojas)

# Aplica Filtros
df_filtered = df.copy()
if sel_mes != 'Todos': df_filtered = df_filtered[df_filtered['Mes'] == sel_mes]
if sel_loja != 'Todas': df_filtered = df_filtered[df_filtered['Loja'] == sel_loja]

# --- APP ---
st.title("Union | Analytics")
st.markdown(f"Visão consolidada • **{sel_mes}** • **{sel_loja}**")

tab1, tab2, tab3 = st.tabs(["📊 Visão Executiva", "📦 Análise de Mix", "📋 Detalhes Operacionais"])

# --- TAB 1: EXECUTIVA ---
with tab1:
    # 1. KPIs
    venda = df_filtered['Venda'].sum() if 'Venda' in df_filtered.columns else 0
    meta = df_filtered['Meta'].sum() if 'Meta' in df_filtered.columns else 0
    clientes = df_filtered['Clientes'].sum() if 'Clientes' in df_filtered.columns else 0
    
    # Tratamento para evitar Divisão por Zero
    ticket = venda / clientes if clientes > 0 else 0
    
    if 'Margem_Perc' in df_filtered.columns:
        margem = df_filtered['Margem_Perc'].mean() # Média simples
    else: margem = 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Venda Total", f"R$ {venda:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with c2: st.metric("Margem", f"{margem:.1f}%")
    with c3: st.metric("Ticket Médio", f"R$ {ticket:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with c4: st.metric("Clientes", f"{clientes:,.0f}".replace(",", "."))
    
    st.markdown("###")

    # 2. LINHA 1 DE GRÁFICOS
    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        st.markdown("##### Evolução vs Metas")
        if 'Mes' in df_filtered.columns:
            # Prepara dados
            idx_col = 'Mes' if sel_mes == 'Todos' else 'Loja'
            df_chart = df_filtered.groupby(idx_col)[['Venda', 'Meta']].sum().reset_index()
            
            # Ordenação Temporal se for Mês
            if idx_col == 'Mes':
                df_chart['sort'] = df_chart['Mes'].apply(lambda x: ordem_meses.index(x.upper()) if x.upper() in ordem_meses else 99)
                df_chart = df_chart.sort_values('sort')
            else:
                df_chart = df_chart.sort_values('Venda', ascending=False)

            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_chart[idx_col], y=df_chart['Venda'], name='Realizado', marker_color='#6750A4', radius=5))
            fig.add_trace(go.Scatter(x=df_chart[idx_col], y=df_chart['Meta'], name='Meta', mode='lines+markers', line=dict(color='#00C853', width=3)))
            
            fig.update_layout(height=350, margin=dict(l=0,r=0,t=30,b=0), legend=dict(orientation="h", y=1.1), plot_bgcolor='white', yaxis=dict(showgrid=True, gridcolor='#F3F4F6'))
            st.plotly_chart(fig, use_container_width=True)
            
    with col_g2:
        st.markdown("##### Atingimento Global")
        # Tratamento para Divisão por Zero no Gauge
        perc = (venda / meta * 100) if meta > 0 else 0
        perc_visual = min(perc, 999) # Trava visual para não quebrar se for absurdo
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=perc_visual,
            number={'suffix': "%", 'font': {'size': 40}},
            gauge={'axis': {'range': [0, 120]}, 'bar': {'color': "#6750A4"}, 'steps': [{'range': [0, 100], 'color': "#EADDFF"}]}
        ))
        fig_gauge.update_layout(height=350, margin=dict(t=40,b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

    # 3. LINHA 2 DE GRÁFICOS (DISTRIBUIÇÃO POR CATEGORIA)
    col_g3, col_g4 = st.columns(2)
    
    with col_g3:
        st.markdown("##### Distribuição por Departamento (Top 5)")
        # Usa base de MIX se existir
        if not df_mix.empty and 'Descricao' in df_mix.columns:
            # Pega Nível 1 (Departamentos). Se não achar Nível, pega top vendas geral.
            if 'Nivel' in df_mix.columns:
                df_depto = df_mix[df_mix['Nivel'] == 1].copy()
                if df_depto.empty: df_depto = df_mix.copy()
            else:
                df_depto = df_mix.copy()
            
            df_depto = df_depto.sort_values('Venda', ascending=False).head(5)
            
            fig_donut = px.pie(df_depto, values='Venda', names='Descricao', hole=0.6, color_discrete_sequence=px.colors.sequential.Purples_r)
            fig_donut.update_layout(height=350, margin=dict(t=0,b=0,l=0,r=0), showlegend=True)
            fig_donut.update_traces(textinfo='percent+label', textposition='inside')
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("Gráfico requer arquivo 'classificacao_mercadologica.csv'")
            
    with col_g4:
        st.markdown("##### Ranking de Lojas")
        if 'Loja' in df_filtered.columns:
            df_rank = df_filtered.groupby('Loja')['Venda'].sum().sort_values(ascending=True).reset_index()
            fig_bar = px.bar(df_rank, x='Venda', y='Loja', orientation='h', text_auto='.2s', color_discrete_sequence=['#6750A4'])
            fig_bar.update_layout(height=350, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(showgrid=False), plot_bgcolor='white')
            st.plotly_chart(fig_bar, use_container_width=True)

# --- TAB 2: MIX (CLASSIFICAÇÃO) ---
with tab2:
    if df_mix.empty:
        st.warning("⚠️ Arquivo de Classificação Mercadológica não encontrado.")
        st.markdown("Faça o upload do arquivo **`classificacao_mercadologica.csv`** no GitHub para ver a análise de mix.")
    else:
        st.markdown("##### Árvore de Produtos (Bill of Materials)")
        st.caption("Navegue pela hierarquia: Departamento > Seção > Grupo > Subgrupo")
        
        # Filtros de visualização
        nivel_selecionado = st.slider("Explodir até o Nível:", 1, 4, 2)
        
        # Filtra base por nível e elimina Vendas zero/negativas para o Treemap não quebrar
        df_tree = df_mix[(df_mix['Nivel'] == nivel_selecionado) & (df_mix['Venda'] > 0)].copy()
        
        if df_tree.empty:
            df_tree = df_mix[df_mix['Venda'] > 0].nlargest(100, 'Venda')
            
        fig_tree = px.treemap(
            df_tree,
            path=['Descricao'],
            values='Venda',
            color='Venda',
            color_continuous_scale='Purples',
            hover_data=['Hierarquia', 'Part']
        )
        fig_tree.update_traces(textinfo="label+value+percent entry")
        fig_tree.update_layout(height=600, margin=dict(t=0, l=0, r=0, b=0))
        st.plotly_chart(fig_tree, use_container_width=True)
        
        st.markdown("### Tabela de Mix")
        st.dataframe(df_mix[['Hierarquia', 'Descricao', 'Venda', 'Part']].sort_values('Venda', ascending=False), use_container_width=True)

# --- TAB 3: DETALHES ---
with tab3:
    st.markdown("##### Detalhamento Consolidado")
    if 'Loja' in df_filtered.columns:
        df_table = df_filtered.groupby('Loja')[['Venda', 'Meta', 'Clientes']].sum().reset_index()
        
        # Cálculo Seguro do Atingimento
        # Substitui Infinito por 0
        df_table['Atingimento'] = (df_table['Venda'] / df_table['Meta'])
        df_table['Atingimento'] = df_table['Atingimento'].replace([np.inf, -np.inf], 0).fillna(0)
        
        st.dataframe(
            df_table.style.format({'Venda': 'R$ {:,.2f}', 'Meta': 'R$ {:,.2f}', 'Clientes': '{:,.0f}', 'Atingimento': '{:.1%}'}),
            use_container_width=True,
            column_config={
                "Atingimento": st.column_config.ProgressColumn("Meta %", format="%.1f%%", min_value=0, max_value=1.5),
                "Venda": st.column_config.NumberColumn("Venda Real", format="R$ %.2f")
            },
            hide_index=True
        )
