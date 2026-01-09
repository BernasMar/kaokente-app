import streamlit as st
import pandas as pd
import math
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA (LAYOUT MOBILE FRIENDLY) ---
st.set_page_config(page_title="Kão Kente", page_icon="logo.png", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS (A "PINTURA" DO SITE) ---
st.markdown("""
    <style>
    /* Esconder Menu Hamburger e Rodapé do Streamlit para parecer App nativa */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Cores da Marca Kão Kente */
    :root {
        --orange-kk: #f68625;
        --green-light: #8db842;
        --green-dark: #0d974d;
        --blue-kk: #9dddf9;
        --brown-kk: #946128;
    }

    /* Estilo dos Botões Principais */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    /* Botão Primário (Laranja) */
    .botao-laranja > button {
        background-color: #f68625 !important;
        color: white !important;
    }

    /* Botão Secundário (Verde) */
    .botao-verde > button {
        background-color: #0d974d !important;
        color: white !important;
    }
    
    /* Títulos e Textos */
    h1, h2, h3 {
        color: #946128; /* Castanho Kão Kente */
    }
    
    /* Cards de Prémios */
    div[data-testid="stMetricValue"] {
        color: #f68625;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LIGAÇÃO AO GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CONSTANTES E DADOS ---
PREMIOS_PONTOS = {
    "Dose batatas": 300,
    "Cachorro 3K": 450,
    "Hambúrguer Kão Kente": 500,
    "Kebab de frango": 550,
    "Baconcheeseburger com ovo": 700,
    "Bitoque de frango": 950
}

URL_ENCOMENDAS = "https://www.foodbooking.com/ordering/restaurant/menu?company_uid=e92e9690-8f0b-45e2-acca-6671a872abb9&restaurant_uid=5e09158f-4dc1-4b17-b9d5-687ca8510db8&facebook=true"

# --- GESTÃO DE NAVEGAÇÃO (SUBSTITUI A SIDEBAR) ---
if 'pagina_atual' not in st.session_state:
    st.session_state['pagina_atual'] = "home"

def navegar_para(pagina):
    st.session_state['pagina_atual'] = pagina

# --- FUNÇÕES DE LÓGICA ---
def calcular_pontos_ganhos(valor_gasto, tipo_cliente):
    valor_inteiro = int(valor_gasto)
    multiplicador = 7.5 if tipo_cliente == "Estudante" else 5.0
    return int(valor_inteiro * multiplicador)

def calcular_metricas_mensais(historico_str):
    agora = datetime.now()
    mes_atual = agora.month
    ano_atual = agora.year
    
    mes_anterior = 12 if mes_atual == 1 else mes_atual - 1
    ano_anterior = ano_atual - 1 if mes_atual == 1 else ano_atual

    total_atual = 0.0
    total_anterior = 0.0

    if not isinstance(historico_str, str): return 0.0, 0.0

    for linha in historico_str.split('\n'):
        if "Compra" in linha:
            try:
                partes = linha.split('|')
                data_str = partes[0].strip()
                valor = float(partes[1].strip().replace("Compra", "").replace("€", "").strip())
                
                try:
                    dt = datetime.strptime(data_str, '%d/%m/%Y %H:%M')
                except:
                    dt = datetime.strptime(data_str, '%d/%m %H:%M').replace(year=ano_atual)

                if dt.month == mes_atual and dt.year == ano_atual:
                    total_atual += valor
                elif dt.month == mes_anterior and dt.year == ano_anterior:
                    total_anterior += valor
            except: continue
    return total_atual, total_anterior

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=["Telemovel", "Nome", "Pontos", "Historico", "Password", "Tipo"])
        
        # Conversões
        df['Telemovel'] = df['Telemovel'].astype(str).replace('nan', '') # Agora é String para aceitar internacionais
        df['Pontos'] = pd.to_numeric(df['Pontos'], errors='coerce').fillna(0).astype(int)
        df['Historico'] = df['Historico'].astype(str).replace('nan', '')
        df['Password'] = df['Password'].astype(str).replace('nan', '')
        df['Tipo'] = df['Tipo'].astype(str).replace('nan', 'Normal')
        
        # Remove linhas vazias
        df = df[df['Telemovel'].str.len() > 3] 
        return df
    except Exception as e:
        st.error(f"Erro BD: {e}")
        return pd.DataFrame(columns=["Telemovel", "Nome", "Pontos", "Historico", "Password", "Tipo"])

def save_data(df):
    try:
        conn.update(worksheet="Sheet1", data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erro ao gravar: {e}")

# --- CABEÇALHO COMUM (HEADER) ---
def render_header():
    col_back, col_logo, col_void = st.columns([1, 2, 1])
    
    with col_back:
        # Mostra botão de voltar se não estivermos na home
        if st.session_state['pagina_atual'] != "home":
            if st.button("⬅ Voltar"):
                navegar_para("home")
                st.rerun()
    
    with col_logo:
        # Tenta carregar logo centralizado
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.markdown("<h2 style='text-align: center; color:#f68625;'>Kão Kente</h2>", unsafe_allow_html=True)
            
    st.markdown("---")

# =========================================================
# PÁGINA: HOME (MENU PRINCIPAL)
# =========================================================
def pagina_home():
    st.markdown("<h3 style='text-align: center;'>O que te apetece hoje?</h3>", unsafe_allow_html=True)
    st.write("")
    st.write("")
    
    # Botão Encomendar (Laranja - #f68625)
    st.markdown('<div class="botao-laranja">', unsafe_allow_html=True)
    if st.button("🛵  ENCOMENDAR ONLINE", use_container_width=True):
        navegar_para("encomendas")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("") # Espaçamento
    
    # Botão Pontos (Verde - #0d974d)
    st.markdown('<div class="botao-verde">', unsafe_allow_html=True)
    if st.button("🏆  MEUS PONTOS E OFERTAS", use_container_width=True):
        navegar_para("pontos")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Área de Acesso Reservado (Admin) - Discreto no rodapé
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.divider()
    col_admin, _ = st.columns([1, 4])
    with col_admin:
        if st.button("🔐 Área Reservada", type="secondary"):
            navegar_para("admin")
            st.rerun()

# =========================================================
# PÁGINA: ENCOMENDAS
# =========================================================
def pagina_encomendas():
    st.markdown("<h2 style='text-align: center; color: #f68625;'>Encomendar Online</h2>", unsafe_allow_html=True)
    
    # Botão Link Externo (Laranja)
    st.markdown(f"""
    <a href="{URL_ENCOMENDAS}" target="_blank" style="text-decoration: none;">
        <div style="background-color: #f68625; color: white; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 1.1em; margin-bottom: 15px;">
            Abrir Ementa em Ecrã Cheio ↗
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    try:
        components.iframe(URL_ENCOMENDAS, height=800, scrolling=True)
    except:
        st.error("Não foi possível carregar o menu aqui. Use o botão acima.")

# =========================================================
# PÁGINA: PROGRAMA DE PONTOS
# =========================================================
def pagina_pontos(df):
    st.markdown("<h2 style='text-align: center; color: #0d974d;'>Clube de Pontos</h2>", unsafe_allow_html=True)

    if 'user_logado' not in st.session_state:
        st.session_state['user_logado'] = None

    if st.session_state['user_logado'] is None:
        st.info("Faz login para veres o teu saldo.")
        
        # Formulário de Login
        # Removemos max_chars para permitir internacionais
        login_tel = st.text_input("Telemóvel (ex: 911222333)")
        login_pass = st.text_input("Password", type="password")
        
        if st.button("Entrar", type="primary"):
            # Limpeza do número para comparação (remove espaços)
            tel_limpo = login_tel.replace(" ", "")
            
            # Tenta encontrar string exata ou número
            user = df[(df['Telemovel'].astype(str) == tel_limpo) & (df['Password'] == login_pass)]
            
            if not user.empty:
                st.session_state['user_logado'] = user.iloc[0]
                st.success("Login efetuado!")
                st.rerun()
            else:
                st.error("Dados incorretos.")
    else:
        # CLIENTE LOGADO
        user = st.session_state['user_logado']
        user_atualizado = df[df['Telemovel'].astype(str) == str(user['Telemovel'])]
        if not user_atualizado.empty:
            user = user_atualizado.iloc[0]
        
        st.markdown(f"👋 Olá, **{user['Nome']}**")
        
        # Card de Saldo
        st.markdown("""
        <div style="background-color: #fce8d4; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #f68625;">
            <span style="color: #946128; font-size: 0.9em;">SALDO DISPONÍVEL</span><br>
            <span style="color: #f68625; font-size: 2.5em; font-weight: bold;">{} ⭐</span>
        </div>
        """.format(user['Pontos']), unsafe_allow_html=True)
        
        st.write("")
        
        if st.button("Terminar Sessão"):
            st.session_state['user_logado'] = None
            st.rerun()

        st.divider()
        st.subheader("🎁 Prémios Disponíveis")
        
        col1, col2 = st.columns(2)
        items = list(PREMIOS_PONTOS.items())
        
        for i, (premio, custo) in enumerate(items):
            saldo = user['Pontos']
            progresso = min(saldo / custo, 1.0)
            cor_barra = "green" if saldo >= custo else "orange"
            
            with (col1 if i % 2 == 0 else col2):
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 10px; padding: 10px; margin-bottom: 10px; height: 100%;">
                    <div style="font-weight: bold; color: #946128; font-size: 0.9em;">{premio}</div>
                    <div style="font-size: 0.8em; color: #828388;">{custo} pts</div>
                    <progress value="{progresso}" max="1" style="width:100%; height: 8px;"></progress>
                    <div style="text-align: right; font-size: 1.2em;">
                        {'✅' if saldo >= custo else '🔒'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with st.expander("Ver Histórico"):
            st.text(user['Historico'])

# =========================================================
# PÁGINA: ADMIN (ÁREA DE GESTÃO)
# =========================================================
def pagina_admin(df):
    st.markdown("<h2 style='text-align: center;'>🔐 Gestão Kão Kente</h2>", unsafe_allow_html=True)
    
    senha_input = st.text_input("Password Staff", type="password")
    
    if senha_input == st.secrets.get("admin_password", "kaokente123"):
        
        filtro = st.text_input("🔍 Pesquisar Cliente:")
        
        lista_clientes = df.to_dict('records')
        opcoes = [str(c['Telemovel']) for c in lista_clientes]
        
        if filtro:
            filtro = filtro.lower()
            opcoes = [str(c['Telemovel']) for c in lista_clientes if filtro in str(c['Nome']).lower() or filtro in str(c['Telemovel'])]
        
        if not opcoes:
            st.warning("Sem resultados.")
            sel_tel = None
        else:
            sel_tel = st.selectbox("Selecione:", opcoes, format_func=lambda x: f"{df[df['Telemovel'].astype(str)==x]['Nome'].values[0]} ({x})")
        
        # MOSTRAR MÉTRICAS
        if sel_tel:
            dados = df[df['Telemovel'].astype(str) == sel_tel].iloc[0]
            g_atual, g_ant = calcular_metricas_mensais(dados['Historico'])
            
            st.info(f"Cliente: **{dados['Nome']}** ({dados['Tipo']})")
            c1, c2, c3 = st.columns(3)
            c1.metric("Pontos", dados['Pontos'])
            c2.metric("Gasto Mês", f"{g_atual:.1f}€")
            c3.metric("Gasto Mês Ant.", f"{g_ant:.1f}€")

            # ABAS
            tab1, tab2, tab3, tab4 = st.tabs(["💰 Lançar", "🎁 Resgatar", "✏️ Editar", "🆕 Novo"])
            
            with tab1: # LANÇAR
                val = st.number_input("Valor (€)", min_value=0.0, step=0.5)
                pts = calcular_pontos_ganhos(val, dados['Tipo'])
                st.write(f"Ganha: **{pts}** pts")
                if st.button("Lançar"):
                    idx = df[df['Telemovel'].astype(str) == sel_tel].index[0]
                    df.at[idx, 'Pontos'] += pts
                    log = f"{datetime.now().strftime('%d/%m/%Y %H:%M')} | Compra {val}€ | +{pts} pts\n"
                    df.at[idx, 'Historico'] = log + str(df.at[idx, 'Historico'])
                    save_data(df)
                    st.success("Feito!")
            
            with tab2: # RESGATAR
                premio = st.selectbox("Oferta", list(PREMIOS_PONTOS.keys()))
                custo = PREMIOS_PONTOS[premio]
                st.write(f"Custo: **{custo}** pts")
                if st.button("Resgatar"):
                    if dados['Pontos'] >= custo:
                        idx = df[df['Telemovel'].astype(str) == sel_tel].index[0]
                        df.at[idx, 'Pontos'] -= custo
                        log = f"{datetime.now().strftime('%d/%m/%Y %H:%M')} | Resgate {premio} | -{custo} pts\n"
                        df.at[idx, 'Historico'] = log + str(df.at[idx, 'Historico'])
                        save_data(df)
                        st.balloons()
                        st.success("Resgatado!")
                    else:
                        st.error("Saldo Insuficiente")

            with tab3: # EDITAR
                with st.form("edit_form"):
                    n_nome = st.text_input("Nome", value=dados['Nome'])
                    n_pass = st.text_input("Pass", value=dados['Password'])
                    n_tipo = st.selectbox("Tipo", ["Normal", "Estudante"], index=0 if dados['Tipo']=="Normal" else 1)
                    n_pts = st.number_input("Pontos", value=int(dados['Pontos']))
                    if st.form_submit_button("Guardar"):
                        idx = df[df['Telemovel'].astype(str) == sel_tel].index[0]
                        df.at[idx, 'Nome'] = n_nome
                        df.at[idx, 'Password'] = n_pass
                        df.at[idx, 'Tipo'] = n_tipo
                        df.at[idx, 'Pontos'] = n_pts
                        save_data(df)
                        st.success("Atualizado!")
                
                with st.expander("Apagar Cliente"):
                    if st.button("Apagar Definitivamente"):
                        idx = df[df['Telemovel'].astype(str) == sel_tel].index[0]
                        df = df.drop(idx)
                        save_data(df)
                        st.rerun()

            with tab4: # NOVO
                st.write("Use a aba Novo Cliente fora da seleção.")

        st.divider()
        with st.expander("➕ Registar Novo Cliente (Geral)"):
            nn_tel = st.text_input("Telemóvel Novo")
            nn_nome = st.text_input("Nome Novo")
            nn_pass = st.text_input("Password Nova")
            nn_tipo = st.selectbox("Tipo Novo", ["Normal", "Estudante"])
            if st.button("Criar Ficha"):
                if nn_tel and nn_nome and nn_pass:
                    # Verifica se existe (agora comparando strings)
                    if nn_tel in df['Telemovel'].astype(str).values:
                        st.error("Já existe!")
                    else:
                        novo = pd.DataFrame([{
                            "Telemovel": str(nn_tel), "Nome": nn_nome, "Pontos": 0,
                            "Historico": "", "Password": nn_pass, "Tipo": nn_tipo
                        }])
                        df = pd.concat([df, novo], ignore_index=True)
                        save_data(df)
                        st.success("Criado!")

# --- FLUXO PRINCIPAL DA APP (MAIN LOOP) ---

# 1. Carrega dados
df = load_data()

# 2. Mostra Cabeçalho (Logo + Botão Voltar)
render_header()

# 3. Encaminha para a página certa
pagina = st.session_state['pagina_atual']

if pagina == "home":
    pagina_home()
elif pagina == "encomendas":
    pagina_encomendas()
elif pagina == "pontos":
    pagina_pontos(df)
elif pagina == "admin":
    pagina_admin(df)