import streamlit as st
import pandas as pd
import math
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Kão Kente", page_icon="logo.png", layout="wide")

# --- LIGAÇÃO AO GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- DEFINIÇÃO DE PRÉMIOS E PREÇOS ---
PREMIOS_PRECO = {
    "Bebida de Cápsula": 0.80,
    "Dose de Batatas Fritas": 1.50,
    "Kebab em Pão": 4.50,
    "Menu Hambúrguer Completo": 6.50,
    "Francesinha Especial": 9.50
}

# --- FUNÇÕES DE LÓGICA ---
def calcular_custo_pontos(preco_euro):
    # Arredonda o preço para o euro acima e multiplica por 100
    return math.ceil(preco_euro) * 100

def calcular_pontos_ganhos(valor_gasto, tipo_cliente):
    # Ignora cêntimos (usa apenas parte inteira)
    valor_inteiro = int(valor_gasto)
    multiplicador = 7.5 if tipo_cliente == "Estudante" else 5.0
    return int(valor_inteiro * multiplicador)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=["Telemovel", "Nome", "Pontos", "Historico", "Password", "Tipo"])
        
        df['Telemovel'] = pd.to_numeric(df['Telemovel'], errors='coerce')
        df['Pontos'] = pd.to_numeric(df['Pontos'], errors='coerce').fillna(0).astype(int)
        df['Historico'] = df['Historico'].astype(str).replace('nan', '')
        df['Password'] = df['Password'].astype(str).replace('nan', '')
        df['Tipo'] = df['Tipo'].astype(str).replace('nan', 'Normal')
        
        df = df.dropna(subset=['Telemovel'])
        return df
    except Exception as e:
        st.error(f"Erro ao ler base de dados: {e}")
        return pd.DataFrame(columns=["Telemovel", "Nome", "Pontos", "Historico", "Password", "Tipo"])

def save_data(df):
    try:
        conn.update(worksheet="Sheet1", data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erro ao gravar: {e}")

# --- BARRA LATERAL (MENU) ---
with st.sidebar:
    # Logo
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.header("🌭 Kão Kente")

    st.divider()
    
    # MENU DE NAVEGAÇÃO COM 3 OPÇÕES
    pagina_selecionada = st.radio("Navegação", [
        "🏆 Programa de Pontos", 
        "🛵 Encomendar Online", 
        "🔐 Área de Gestão"
    ])

# Carregar dados (necessário em quase todas as páginas)
df = load_data()

# =========================================================
# PÁGINA 1: PROGRAMA DE PONTOS (VISÃO CLIENTE)
# =========================================================
if pagina_selecionada == "🏆 Programa de Pontos":
    st.title("🌭 Programa de Pontos Kão Kente")

    if 'user_logado' not in st.session_state:
        st.session_state['user_logado'] = None

    tab_cliente, tab_sobre = st.tabs(["👤 A minha Conta", "ℹ️ Sobre o Programa"])

    with tab_cliente:
        # LOGIN
        if st.session_state['user_logado'] is None:
            st.info("Faz login para veres o teu saldo e ofertas.")
            col1, col2 = st.columns(2)
            with col1:
                login_tel = st.text_input("Telemóvel", max_chars=9)
            with col2:
                login_pass = st.text_input("Password", type="password")
            
            if st.button("Entrar"):
                if login_tel.isdigit():
                    user = df[(df['Telemovel'] == int(login_tel)) & (df['Password'] == login_pass)]
                    if not user.empty:
                        st.session_state['user_logado'] = user.iloc[0]
                        st.success("Bem-vindo de volta!")
                        st.rerun()
                    else:
                        st.error("Dados incorretos.")
                else:
                    st.error("Número inválido.")

        # ÁREA PESSOAL (LOGADO)
        else:
            user = st.session_state['user_logado']
            # Garante dados frescos
            user_atualizado = df[df['Telemovel'] == user['Telemovel']]
            if not user_atualizado.empty:
                user = user_atualizado.iloc[0]
            
            st.success(f"Olá, **{user['Nome']}**! (Conta {user['Tipo']})")
            
            c_pts, c_btn = st.columns([3, 1])
            with c_pts:
                st.metric("O teu Saldo", f"{user['Pontos']} Pontos")
            with c_btn:
                if st.button("Sair"):
                    st.session_state['user_logado'] = None
                    st.rerun()

            st.markdown("### 🎁 Prémios Disponíveis")
            col_grid1, col_grid2 = st.columns(2)
            items_list = list(PREMIOS_PRECO.items())
            
            for i, (premio, preco_eur) in enumerate(items_list):
                custo_pts = calcular_custo_pontos(preco_eur)
                saldo = user['Pontos']
                percentagem = min(saldo / custo_pts, 1.0)
                pode_comprar = saldo >= custo_pts
                
                col_atual = col_grid1 if i % 2 == 0 else col_grid2
                with col_atual:
                    with st.container(border=True):
                        st.markdown(f"**{premio}**")
                        st.caption(f"Valor: {preco_eur:.2f}€ | Custo: {custo_pts} pts")
                        st.progress(percentagem)
                        if pode_comprar:
                            st.write("✅ **Podes pedir!**")
                        else:
                            st.write(f"🔒 Faltam {custo_pts - saldo}")

            with st.expander("Ver histórico de movimentos"):
                st.text(user['Historico'])

    with tab_sobre:
        st.markdown("""
        ### Regras do Clube
        * **Estudantes:** 7.5 pts por cada 1€ (apenas parte inteira).
        * **Normal:** 5 pts por cada 1€ (apenas parte inteira).
        * Troca pontos por refeições grátis!
        """)

# =========================================================
# PÁGINA 2: ENCOMENDAR ONLINE
# =========================================================
elif pagina_selecionada == "🛵 Encomendar Online":
    st.title("🛵 Encomendar Online")
    gloria_url = "https://www.foodbooking.com/ordering/restaurant/menu?company_uid=e92e9690-8f0b-45e2-acca-6671a872abb9&restaurant_uid=5e09158f-4dc1-4b17-b9d5-687ca8510db8&facebook=true"
    
    st.info("Faz o teu pedido aqui em baixo:")
    try:
        components.iframe(gloria_url, height=800, scrolling=True)
    except:
        st.error("Erro ao carregar menu.")
    
    st.link_button("Abrir Menu em Nova Janela ↗️", gloria_url, type="primary")

# =========================================================
# PÁGINA 3: ÁREA DE GESTÃO (ADMIN)
# =========================================================
elif pagina_selecionada == "🔐 Área de Gestão":
    st.title("🔐 Gestão Kão Kente")
    
    # Password check
    senha_input = st.text_input("Insira a Password de Admin", type="password")
    
    if senha_input == st.secrets.get("admin_password", "kaokente123"):
        st.divider()
        
        # FILTRO DE PESQUISA (COMO PEDISTE)
        col_search, col_info = st.columns([2, 1])
        with col_search:
            filtro_nome = st.text_input("🔍 Pesquisar Cliente (Nome ou Telemóvel):")
        
        # Lógica de filtro
        lista_completa = df.to_dict('records')
        opcoes_filtradas = []
        if filtro_nome:
            filtro_nome = filtro_nome.lower()
            opcoes_filtradas = [
                c['Telemovel'] for c in lista_completa 
                if filtro_nome in str(c['Nome']).lower() or filtro_nome in str(c['Telemovel'])
            ]
        else:
            opcoes_filtradas = df['Telemovel'].tolist()

        sel_cliente = None
        if opcoes_filtradas:
            sel_cliente = st.selectbox("Selecionar Cliente da Lista:", opcoes_filtradas, 
                                     format_func=lambda x: f"{df[df['Telemovel']==x]['Nome'].values[0]} ({x})")
        else:
            st.warning("Nenhum cliente encontrado.")

        # MOSTRAR DADOS DO CLIENTE SELECIONADO
        if sel_cliente:
            dados_cli = df[df['Telemovel'] == sel_cliente].iloc[0]
            with col_info:
                st.success(f"**{dados_cli['Nome']}**")
                st.metric("Saldo Atual", f"{dados_cli['Pontos']} pts")
                st.caption(f"Tipo: {dados_cli['Tipo']}")

        st.markdown("---")

        # ABAS DE AÇÃO
        tab_lanc, tab_resg, tab_cri, tab_bd = st.tabs(["💰 Lançar Venda", "🎁 Resgatar Oferta", "🆕 Criar Cliente", "📊 Ver Tudo"])

        with tab_lanc:
            if sel_cliente:
                val_eur = st.number_input("Valor da Venda (€)", min_value=0.0, step=0.5)
                pts_ganhar = calcular_pontos_ganhos(val_eur, dados_cli['Tipo'])
                
                st.write(f"Vai ganhar: **{pts_ganhar}** pontos (Base: {int(val_eur)}€)")
                
                if st.button("Confirmar Lançamento"):
                    idx = df[df['Telemovel'] == sel_cliente].index[0]
                    df.at[idx, 'Pontos'] += pts_ganhar
                    
                    log = f"{datetime.now().strftime('%d/%m %H:%M')} | Compra {val_eur}€ | +{pts_ganhar} pts\n"
                    df.at[idx, 'Historico'] = log + str(df.at[idx, 'Historico'])
                    
                    save_data(df)
                    st.success("Pontos adicionados!")
            else:
                st.info("Selecione um cliente acima para lançar pontos.")

        with tab_resg:
            if sel_cliente:
                premio = st.selectbox("Escolher Oferta", list(PREMIOS_PRECO.keys()))
                custo = calcular_custo_pontos(PREMIOS_PRECO[premio])
                st.write(f"Custo: **{custo}** pts")
                
                if st.button("Confirmar Resgate"):
                    if dados_cli['Pontos'] >= custo:
                        idx = df[df['Telemovel'] == sel_cliente].index[0]
                        df.at[idx, 'Pontos'] -= custo
                        
                        log = f"{datetime.now().strftime('%d/%m %H:%M')} | Resgate {premio} | -{custo} pts\n"
                        df.at[idx, 'Historico'] = log + str(df.at[idx, 'Historico'])
                        
                        save_data(df)
                        st.balloons()
                        st.success("Oferta entregue!")
                    else:
                        st.error("Saldo insuficiente.")
            else:
                st.info("Selecione um cliente acima para resgatar.")

        with tab_cri:
            st.write("Novo Registo")
            n_nome = st.text_input("Nome")
            n_tel = st.text_input("Telemóvel")
            n_pass = st.text_input("Password Inicial")
            n_tipo = st.selectbox("Tipo", ["Normal", "Estudante"])
            
            if st.button("Criar Ficha"):
                if n_tel and n_nome and n_pass:
                    if n_tel.isdigit() and int(n_tel) in df['Telemovel'].values:
                        st.error("Esse número já existe.")
                    else:
                        novo = pd.DataFrame([{
                            "Telemovel": int(n_tel), "Nome": n_nome, "Pontos": 0,
                            "Historico": "", "Password": n_pass, "Tipo": n_tipo
                        }])
                        df = pd.concat([df, novo], ignore_index=True)
                        save_data(df)
                        st.success("Cliente criado!")
                else:
                    st.warning("Preencha todos os campos.")

        with tab_bd:
            st.dataframe(df)

    elif senha_input:
        st.error("Password errada.")