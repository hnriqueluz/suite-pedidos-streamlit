import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import base64

# Configuração da página
st.set_page_config(
    page_title="Suíte de Controle de Pedidos",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para design minimalista
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 300;
        color: #ffffff;
        margin-bottom: 2rem;
    }
    .kpi-card {
        background: #2d2d2d;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #404040;
        text-align: center;
        height: 120px;
    }
    .kpi-number {
        font-size: 2rem;
        font-weight: 600;
        margin: 0;
    }
    .kpi-label {
        color: #cccccc;
        font-size: 0.9rem;
        margin: 0;
    }
    .success { color: #28a745; }
    .warning { color: #ffc107; }
    .danger { color: #dc3545; }
    .info { color: #007bff; }
    .attention-box {
        background: #2d2d2d;
        border: 1px solid #007bff;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #ffffff;
    }
    .backup-section {
        background: #1e1e1e;
        border: 1px solid #007bff;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #ffffff;
    }
    .data-status {
        background: #2d2d2d;
        border: 1px solid #28a745;
        color: #ffffff;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin: 0.5rem 0;
    }
    .stApp {
        background-color: #0e1117;
    }
    .stApp > header {
        background-color: transparent;
    }
    .stApp > div > div > div > div {
        background-color: #0e1117;
    }
</style>
""", unsafe_allow_html=True)

# Função para salvar dados como Excel
def save_data_to_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Salvar cada aba em uma planilha separada
        st.session_state.pedidos_df.to_excel(writer, sheet_name='Pedidos', index=False)
        st.session_state.followup_df.to_excel(writer, sheet_name='Follow-ups', index=False)
        st.session_state.pagamentos_df.to_excel(writer, sheet_name='Pagamentos', index=False)
        
        # Criar aba de informações
        info_df = pd.DataFrame({
            'Informação': ['Última atualização', 'Total de pedidos', 'Total de follow-ups', 'Total de pagamentos'],
            'Valor': [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                len(st.session_state.pedidos_df),
                len(st.session_state.followup_df),
                len(st.session_state.pagamentos_df)
            ]
        })
        info_df.to_excel(writer, sheet_name='Info', index=False)
    
    output.seek(0)
    return output.getvalue()

# Função para carregar dados do Excel
def load_data_from_excel(excel_file):
    try:
        # Carregar pedidos
        try:
            st.session_state.pedidos_df = pd.read_excel(excel_file, sheet_name='Pedidos')
        except:
            st.session_state.pedidos_df = pd.DataFrame(columns=[
                'Nº Pedido', 'Fornecedor', 'País', 'Produto', 'Valor', 'Condição Pagamento',
                'Data Pedido', 'Leadtime Prometido', 'Data Prometida', 'Data Real', 'Status',
                'Pagamento', 'Observações'
            ])
        
        # Carregar follow-ups
        try:
            st.session_state.followup_df = pd.read_excel(excel_file, sheet_name='Follow-ups')
        except:
            st.session_state.followup_df = pd.DataFrame(columns=[
                'Data', 'Fornecedor', 'Pedido', 'Meio', 'SLA Resposta'
            ])
        
        # Carregar pagamentos
        try:
            st.session_state.pagamentos_df = pd.read_excel(excel_file, sheet_name='Pagamentos')
        except:
            st.session_state.pagamentos_df = pd.DataFrame(columns=[
                'Pedido', 'Fornecedor', 'Valor Total', 'Valor Pago', 'Data Prevista Pagamento', 'Status'
            ])
        
        # Buscar data da última atualização
        try:
            info_df = pd.read_excel(excel_file, sheet_name='Info')
            ultima_atualizacao = info_df[info_df['Informação'] == 'Última atualização']['Valor'].iloc[0]
        except:
            ultima_atualizacao = 'Data desconhecida'
        
        return True, ultima_atualizacao
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return False, None

# Inicialização dos dados de sessão
def init_session_data():
    if 'pedidos_df' not in st.session_state:
        st.session_state.pedidos_df = pd.DataFrame(columns=[
            'Nº Pedido', 'Fornecedor', 'País', 'Produto', 'Valor', 'Condição Pagamento',
            'Data Pedido', 'Leadtime Prometido', 'Data Prometida', 'Data Real', 'Status',
            'Pagamento', 'Observações'
        ])

    if 'followup_df' not in st.session_state:
        st.session_state.followup_df = pd.DataFrame(columns=[
            'Data', 'Fornecedor', 'Pedido', 'Meio', 'SLA Resposta'
        ])

    if 'pagamentos_df' not in st.session_state:
        st.session_state.pagamentos_df = pd.DataFrame(columns=[
            'Pedido', 'Fornecedor', 'Valor Total', 'Valor Pago', 'Data Prevista Pagamento', 'Status'
        ])

init_session_data()

# Dados de transit time
TRANSIT_TIMES = {
    'China': {'Marítimo': '35-45 dias', 'Aéreo': '7-10 dias'},
    'EUA': {'Marítimo': '15-20 dias', 'Aéreo': '5-7 dias'},
    'México': {'Marítimo': '12-18 dias', 'Aéreo': '3-5 dias'},
    'Inglaterra': {'Marítimo': '20-25 dias', 'Aéreo': '5-6 dias'},
    'Índia': {'Marítimo': '28-35 dias', 'Aéreo': '6-8 dias'}
}

# ========== SEÇÃO DE BACKUP E RESTAURAÇÃO ==========
st.sidebar.markdown("---")
st.sidebar.markdown("### 💾 **Gerenciar Dados**")

# Status dos dados
total_pedidos = len(st.session_state.pedidos_df)
total_followups = len(st.session_state.followup_df)
total_pagamentos = len(st.session_state.pagamentos_df)

st.sidebar.markdown(f"""
<div class="data-status">
📦 {total_pedidos} pedidos<br>
📞 {total_followups} follow-ups<br>
💰 {total_pagamentos} pagamentos
</div>
""", unsafe_allow_html=True)

# Upload de dados
st.sidebar.markdown("#### 📁 **Carregar Dados Salvos**")
uploaded_file = st.sidebar.file_uploader("Selecione seu arquivo de backup:", type=['xlsx', 'xls'], key="data_upload")

if uploaded_file is not None:
    success, ultima_atualizacao = load_data_from_excel(uploaded_file)
    if success:
        st.sidebar.success(f"✅ Dados carregados!\nÚltima atualização: {ultima_atualizacao}")
        st.experimental_rerun()

# Download de dados
st.sidebar.markdown("#### 💾 **Salvar Dados**")
if st.sidebar.button("📥 Baixar Backup Completo"):
    excel_data = save_data_to_excel()
    filename = f"pedidos_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    
    st.sidebar.download_button(
        label="⬇️ Download Excel",
        data=excel_data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.sidebar.success("✅ Clique no botão acima para baixar!")

# Sidebar para navegação
st.sidebar.markdown("---")
st.sidebar.title("📦 Navegação")
page = st.sidebar.selectbox(
    "Selecione a aba:",
    ["🏠 Cockpit Diário", "📋 Controle de Pedidos", "📞 Follow Up Tracker", 
     "💰 Controle de Pagamentos", "🚢 Calculadora Transit Time", "📏 Conversor de Medidas"]
)

# Instruções de uso
with st.sidebar.expander("❓ Como Usar"):
    st.markdown("""
    **📋 Rotina Diária:**
    
    🌅 **Manhã:**
    - Faça upload do seu backup Excel
    - Trabalhe normalmente
    
    🌆 **Fim do dia:**
    - Baixe o backup Excel atual
    - Salve no email/drive
    
    **💡 Dicas:**
    - Dados salvos apenas na sessão
    - Sempre faça backup!
    - Arquivos em formato Excel (.xlsx)
    """)

# Função para saudação automática
def get_greeting():
    now = datetime.now()
    hour = now.hour
    if 5 <= hour < 12:
        return "☀️ Bom dia, Henri!"
    elif 12 <= hour < 18:
        return "🌤️ Boa tarde, Henri!"
    else:
        return "🌙 Boa noite, Henri!"

# Função para calcular KPIs
def calculate_kpis():
    if st.session_state.pedidos_df.empty:
        return {'no_prazo': 0, 'atrasados': 0, 'pag_pendente': 0, 'sla_medio': 0}
    
    df = st.session_state.pedidos_df.copy()
    hoje = datetime.now().date()
    
    # Converter datas
    if 'Data Prometida' in df.columns and not df.empty:
        df['Data Prometida'] = pd.to_datetime(df['Data Prometida'], errors='coerce').dt.date
        df['Data Real'] = pd.to_datetime(df['Data Real'], errors='coerce').dt.date
    
    no_prazo = len(df[df['Status'] == 'Entregue'])
    atrasados = len(df[(df['Data Prometida'] < hoje) & (df['Status'] != 'Entregue')])
    pag_pendente = len(df[df['Pagamento'].isin(['Não', 'Adiantamento'])])
    
    # SLA médio
    if not st.session_state.followup_df.empty:
        sla_medio = st.session_state.followup_df['SLA Resposta'].mean()
    else:
        sla_medio = 0
    
    return {
        'no_prazo': no_prazo,
        'atrasados': atrasados, 
        'pag_pendente': pag_pendente,
        'sla_medio': round(sla_medio, 1)
    }

# ABA 1: COCKPIT DIÁRIO
if page == "🏠 Cockpit Diário":
    st.markdown(f'<h1 class="main-header">{get_greeting()}</h1>', unsafe_allow_html=True)
    
    # Aviso sobre dados
    if total_pedidos == 0 and total_followups == 0 and total_pagamentos == 0:
        st.markdown('''
        <div class="backup-section">
            <h4>🚀 Primeiros Passos:</h4>
            <p><strong>1.</strong> Carregue um backup existente (sidebar) OU</p>
            <p><strong>2.</strong> Comece adicionando pedidos na aba "Controle de Pedidos"</p>
            <p><strong>💡 Lembre-se:</strong> Sempre baixe seu backup Excel no fim do dia!</p>
        </div>
        ''', unsafe_allow_html=True)
    
    # KPIs
    kpis = calculate_kpis()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'''
        <div class="kpi-card">
            <p class="kpi-number success">{kpis["no_prazo"]}</p>
            <p class="kpi-label">Pedidos no Prazo</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="kpi-card">
            <p class="kpi-number danger">{kpis["atrasados"]}</p>
            <p class="kpi-label">Pedidos em Atraso</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="kpi-card">
            <p class="kpi-number warning">{kpis["pag_pendente"]}</p>
            <p class="kpi-label">Pagamento Pendente</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
        <div class="kpi-card">
            <p class="kpi-number info">{kpis["sla_medio"]}</p>
            <p class="kpi-label">SLA Médio (dias)</p>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Kanban Visual")
        if not st.session_state.pedidos_df.empty:
            df = st.session_state.pedidos_df
            kanban_data = df['Status'].value_counts()
            fig = px.pie(values=kanban_data.values, names=kanban_data.index, 
                        color_discrete_sequence=['#28a745', '#ffc107', '#dc3545', '#007bff'])
            fig.update_layout(height=300, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Adicione pedidos para visualizar o kanban")
    
    with col2:
        st.subheader("🌍 Lead Time por País")
        if not st.session_state.pedidos_df.empty:
            df = st.session_state.pedidos_df
            if 'País' in df.columns and 'Leadtime Prometido' in df.columns:
                country_data = df.groupby('País')['Leadtime Prometido'].mean()
                if not country_data.empty:
                    fig = px.bar(x=country_data.index, y=country_data.values,
                               color_discrete_sequence=['#007bff'])
                    fig.update_layout(height=300, xaxis_title="País", yaxis_title="Lead Time (dias)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Dados insuficientes para gráfico")
            else:
                st.info("Dados insuficientes")
        else:
            st.info("Adicione pedidos para visualizar lead times")
    
    # Atenção Hoje
    st.markdown('''
    <div class="attention-box">
        <h3>⚠️ Atenção Hoje</h3>
        <p>Pedidos que exigem follow-up:</p>
    </div>
    ''', unsafe_allow_html=True)
    
    if not st.session_state.pedidos_df.empty:
        hoje = datetime.now().date()
        df = st.session_state.pedidos_df.copy()
        if 'Data Prometida' in df.columns:
            df['Data Prometida'] = pd.to_datetime(df['Data Prometida'], errors='coerce').dt.date
            atencao_hoje = df[
                (df['Data Prometida'] <= hoje + timedelta(days=2)) & 
                (df['Status'] != 'Entregue')
            ]
            if not atencao_hoje.empty:
                st.dataframe(atencao_hoje[['Nº Pedido', 'Fornecedor', 'Data Prometida', 'Status']], 
                           use_container_width=True)
            else:
                st.success("✅ Nenhum pedido exige atenção especial hoje!")
    else:
        st.info("Nenhum pedido cadastrado ainda.")

# ABA 2: CONTROLE DE PEDIDOS
elif page == "📋 Controle de Pedidos":
    st.header("📋 Controle de Pedidos")
    
    # Formulário para adicionar pedidos
    with st.expander("➕ Adicionar Novo Pedido", expanded=False):
        with st.form("novo_pedido"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                num_pedido = st.text_input("Nº Pedido")
                fornecedor = st.text_input("Fornecedor")
                pais = st.selectbox("País", ["China", "EUA", "México", "Inglaterra", "Índia"])
            
            with col2:
                produto = st.text_input("Produto")
                valor = st.number_input("Valor", min_value=0.0, step=0.01)
                condicao_pag = st.selectbox("Condição Pagamento", 
                                          ["À vista", "30 dias", "60 dias", "90 dias"])
            
            with col3:
                data_pedido = st.date_input("Data Pedido")
                leadtime_prometido = st.number_input("Lead Time Prometido (dias)", min_value=1)
                data_prometida = st.date_input("Data Prometida")
            
            col4, col5 = st.columns(2)
            with col4:
                data_real = st.date_input("Data Real (opcional)", value=None)
                status = st.selectbox("Status", ["Pendente", "Em Produção", "Despachado", "Entregue"])
            
            with col5:
                pagamento = st.selectbox("Pagamento", ["Não", "Sim", "Adiantamento"])
                observacoes = st.text_area("Observações")
            
            if st.form_submit_button("💾 Salvar Pedido"):
                if num_pedido and fornecedor:
                    novo_pedido = {
                        'Nº Pedido': num_pedido,
                        'Fornecedor': fornecedor,
                        'País': pais,
                        'Produto': produto,
                        'Valor': valor,
                        'Condição Pagamento': condicao_pag,
                        'Data Pedido': data_pedido,
                        'Leadtime Prometido': leadtime_prometido,
                        'Data Prometida': data_prometida,
                        'Data Real': data_real,
                        'Status': status,
                        'Pagamento': pagamento,
                        'Observações': observacoes
                    }
                    st.session_state.pedidos_df = pd.concat([
                        st.session_state.pedidos_df, 
                        pd.DataFrame([novo_pedido])
                    ], ignore_index=True)
                    st.success("✅ Pedido adicionado! Lembre-se de fazer backup depois.")
                    st.experimental_rerun()
                else:
                    st.error("❌ Preencha pelo menos Nº Pedido e Fornecedor")
    
    # Exibir tabela de pedidos
    if not st.session_state.pedidos_df.empty:
        st.subheader("📊 Lista de Pedidos")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            fornecedores = ["Todos"] + list(st.session_state.pedidos_df['Fornecedor'].unique())
            filtro_fornecedor = st.selectbox("Filtrar por Fornecedor", fornecedores)
        with col2:
            status_list = ["Todos"] + list(st.session_state.pedidos_df['Status'].unique())
            filtro_status = st.selectbox("Filtrar por Status", status_list)
        with col3:
            paises = ["Todos"] + list(st.session_state.pedidos_df['País'].unique())
            filtro_pais = st.selectbox("Filtrar por País", paises)
        
        # Aplicar filtros
        df_filtrado = st.session_state.pedidos_df.copy()
        if filtro_fornecedor != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Fornecedor'] == filtro_fornecedor]
        if filtro_status != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Status'] == filtro_status]
        if filtro_pais != "Todos":
            df_filtrado = df_filtrado[df_filtrado['País'] == filtro_pais]
        
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Botões de ação
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Exportar para CSV"):
                csv = df_filtrado.to_csv(index=False)
                st.download_button(
                    "⬇️ Download CSV",
                    csv,
                    f"pedidos_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
        
        with col2:
            if st.button("🗑️ Limpar Todos os Pedidos"):
                st.session_state.pedidos_df = pd.DataFrame(columns=[
                    'Nº Pedido', 'Fornecedor', 'País', 'Produto', 'Valor', 'Condição Pagamento',
                    'Data Pedido', 'Leadtime Prometido', 'Data Prometida', 'Data Real', 'Status',
                    'Pagamento', 'Observações'
                ])
                st.success("✅ Pedidos limpos!")
                st.experimental_rerun()
    else:
        st.info("Nenhum pedido cadastrado. Use o formulário acima para adicionar.")

# ABA 3: FOLLOW UP TRACKER
elif page == "📞 Follow Up Tracker":
    st.header("📞 Follow Up Tracker")
    
    # Formulário para adicionar follow-up
    with st.expander("➕ Registrar Follow-Up", expanded=False):
        with st.form("novo_followup"):
            col1, col2 = st.columns(2)
            
            with col1:
                data_followup = st.date_input("Data")
                fornecedor_fu = st.text_input("Fornecedor")
                pedido_fu = st.text_input("Pedido")
            
            with col2:
                meio = st.selectbox("Meio", ["E-mail", "WhatsApp", "Telefone", "Presencial"])
                sla_resposta = st.number_input("SLA Resposta (dias)", min_value=0, max_value=30)
            
            if st.form_submit_button("💾 Registrar Follow-Up"):
                if fornecedor_fu:
                    novo_followup = {
                        'Data': data_followup,
                        'Fornecedor': fornecedor_fu,
                        'Pedido': pedido_fu,
                        'Meio': meio,
                        'SLA Resposta': sla_resposta
                    }
                    st.session_state.followup_df = pd.concat([
                        st.session_state.followup_df,
                        pd.DataFrame([novo_followup])
                    ], ignore_index=True)
                    st.success("✅ Follow-up registrado!")
                    st.experimental_rerun()
                else:
                    st.error("❌ Preencha pelo menos o Fornecedor")
    
    # Exibir tabela e estatísticas
    if not st.session_state.followup_df.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 Histórico de Follow-Ups")
            st.dataframe(st.session_state.followup_df, use_container_width=True)
        
        with col2:
            st.subheader("📈 SLA Médio por Fornecedor")
            if 'SLA Resposta' in st.session_state.followup_df.columns:
                sla_medio = st.session_state.followup_df.groupby('Fornecedor')['SLA Resposta'].mean()
                for fornecedor, sla in sla_medio.items():
                    st.metric(fornecedor, f"{sla:.1f} dias")
    else:
        st.info("Nenhum follow-up registrado ainda.")

# ABA 4: CONTROLE DE PAGAMENTOS
elif page == "💰 Controle de Pagamentos":
    st.header("💰 Controle de Pagamentos")
    
    # Formulário para adicionar pagamento
    with st.expander("➕ Registrar Pagamento", expanded=False):
        with st.form("novo_pagamento"):
            col1, col2 = st.columns(2)
            
            with col1:
                pedido_pag = st.text_input("Pedido")
                fornecedor_pag = st.text_input("Fornecedor")
                valor_total = st.number_input("Valor Total", min_value=0.0, step=0.01)
            
            with col2:
                valor_pago = st.number_input("Valor Pago", min_value=0.0, step=0.01)
                data_prevista = st.date_input("Data Prevista Pagamento")
                status_pag = st.selectbox("Status", ["Pendente", "Pago Parcial", "Pago"])
            
            if st.form_submit_button("💾 Registrar Pagamento"):
                if pedido_pag and fornecedor_pag:
                    perc_pago = (valor_pago / valor_total * 100) if valor_total > 0 else 0
                    novo_pagamento = {
                        'Pedido': pedido_pag,
                        'Fornecedor': fornecedor_pag,
                        'Valor Total': valor_total,
                        'Valor Pago': valor_pago,
                        '% Pago': round(perc_pago, 2),
                        'Data Prevista Pagamento': data_prevista,
                        'Status': status_pag
                    }
                    st.session_state.pagamentos_df = pd.concat([
                        st.session_state.pagamentos_df,
                        pd.DataFrame([novo_pagamento])
                    ], ignore_index=True)
                    st.success("✅ Pagamento registrado!")
                    st.experimental_rerun()
                else:
                    st.error("❌ Preencha pelo menos Pedido e Fornecedor")
    
    # Exibir informações de pagamentos
    if not st.session_state.pagamentos_df.empty:
        # Métricas de exposição financeira
        df_pag = st.session_state.pagamentos_df
        total_adiantado = df_pag[df_pag['Status'].isin(['Pago Parcial', 'Pago'])]['Valor Pago'].sum()
        total_pendente = df_pag[df_pag['Status'] == 'Pendente']['Valor Total'].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total Adiantado", f"R$ {total_adiantado:,.2f}")
        with col2:
            st.metric("⏳ Total Pendente", f"R$ {total_pendente:,.2f}")
        with col3:
            st.metric("📊 Exposição Financeira", f"R$ {total_adiantado:,.2f}")
        
        st.subheader("📊 Lista de Pagamentos")
        st.dataframe(df_pag, use_container_width=True)
    else:
        st.info("Nenhum pagamento registrado ainda.")

# ABA 5: CALCULADORA TRANSIT TIME
elif page == "🚢 Calculadora Transit Time":
    st.header("🚢 Calculadora de Transit Time")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🌍 Consultar Prazo")
        
        pais_selecionado = st.selectbox("País de Origem:", list(TRANSIT_TIMES.keys()))
        modal_selecionado = st.selectbox("Modal de Transporte:", ["Marítimo", "Aéreo"])
        porto_destino = st.selectbox("Porto de Destino:", ["Santos", "Itapoá"])
        
        if st.button("🔍 Consultar Prazo"):
            prazo = TRANSIT_TIMES[pais_selecionado][modal_selecionado]
            st.success(f"📅 **Transit Time**: {prazo}")
            st.info(f"🚢 **Rota**: {pais_selecionado} → {porto_destino} ({modal_selecionado})")
    
    with col2:
        st.subheader("📊 Tabela de Prazos")
        
        # Criar tabela formatada dos prazos
        tabela_prazos = []
        for pais, modais in TRANSIT_TIMES.items():
            for modal, prazo in modais.items():
                tabela_prazos.append({
                    'País': pais,
                    'Modal': modal,
                    'Prazo': prazo
                })
        
        df_prazos = pd.DataFrame(tabela_prazos)
        st.dataframe(df_prazos, use_container_width=True)

# ABA 6: CONVERSOR DE MEDIDAS
elif page == "📏 Conversor de Medidas":
    st.header("📏 Conversor de Medidas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📐 Metros → Pés")
        metros_para_pes = st.number_input("Digite o valor em metros:", min_value=0.0, step=0.01, key="m_to_ft")
        if metros_para_pes > 0:
            pes = metros_para_pes * 3.28084
            st.success(f"📏 **{metros_para_pes} m** = **{pes:.2f} ft**")
    
    with col2:
        st.subheader("📐 Metros → Polegadas")
        metros_para_pol = st.number_input("Digite o valor em metros:", min_value=0.0, step=0.01, key="m_to_in")
        if metros_para_pol > 0:
            polegadas = metros_para_pol * 39.3701
            st.success(f"📏 **{metros_para_pol} m** = **{polegadas:.2f} in**")
    
    st.markdown("---")
    
    # Calculadora adicional
    st.subheader("🧮 Calculadora Rápida")
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Pés → Metros")
        pes_para_metros = st.number_input("Digite o valor em pés:", min_value=0.0, step=0.01)
        if pes_para_metros > 0:
            metros = pes_para_metros / 3.28084
            st.info(f"📏 **{pes_para_metros} ft** = **{metros:.2f} m**")
    
    with col4:
        st.subheader("Polegadas → Metros")
        pol_para_metros = st.number_input("Digite o valor em polegadas:", min_value=0.0, step=0.01)
        if pol_para_metros > 0:
            metros = pol_para_metros / 39.3701
            st.info(f"📏 **{pol_para_metros} in** = **{metros:.2f} m**")

# Instruções de Backup no final da página
if page != "🏠 Cockpit Diário":
    st.markdown("---")
    st.markdown('''
    <div class="backup-section">
        <h4>💡 Lembrete Importante:</h4>
        <p>📥 Use o <strong>sidebar</strong> para fazer backup Excel dos seus dados no final do dia</p>
        <p>📤 Carregue seu backup sempre que abrir o app em um novo computador/sessão</p>
    </div>
    ''', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #6c757d; font-size: 0.9rem;'>
        📦 Suíte de Controle de Pedidos | Dados: {total_pedidos} pedidos, {total_followups} follow-ups, {total_pagamentos} pagamentos
    </div>
    """, 
    unsafe_allow_html=True
)
