import streamlit as st
import pandas as pd
import math
import base64
from datetime import datetime, date
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Kão Kente", page_icon="logo.png", layout="wide")

# --- CORES DA MARCA ---
COR_FUNDO = "#946128"
COR_CASTANHO = "#946128"
COR_BOTAO_FUNDO = "#f68625"
COR_BOTAO_TEXTO = "#9dddf9"
COR_VERDE_CLARO = "#8db842"
COR_VERDE_ESCURO = "#0d974d"
COR_BRANCO = "#ffffff"

# --- ACESSO DIRETO (LINK GESTÃO) ---
if "menu" in st.query_params and st.query_params["menu"] == "gest":
    if st.session_state.get('pagina') != 'admin_panel':
        st.session_state['pagina'] = 'admin_login'

# --- FUNÇÃO IMAGEM ---
def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except:
        return "" 

logo_b64 = get_image_base64("logo.png")

# --- CSS (CORREÇÕES VISUAIS DE FUNDO E SELECTBOX) ---
st.markdown(f"""
<style>
/* ---------------- CONTAINER ---------------- */
.block-container {{
    padding-top: 1rem;
    padding-bottom: 5rem;
    max-width: 600px;
    margin: 0 auto;
}}

.stApp {{ background-color: {COR_FUNDO}; }}

#MainMenu, header, footer {{ visibility: hidden; }}

/* ---------------- TEXTO ---------------- */
h1, h2, h3, h4 {{
    color: {COR_BRANCO} !important;
    font-weight: 800 !important;
    text-align: center !important;
    margin-bottom: 20px !important;
}}

p, label {{
    color: {COR_BRANCO} !important;
    font-family: sans-serif;
}}

/* ---------------- BOTÕES (TODOS) ---------------- */
div.stButton,
div[data-testid="stButton"] {{
    width: 100% !important;
    margin: 10px 0 !important;
    display: block !important;
}}

div.stButton > button,
div[data-testid="stButton"] > button {{
    width: 100% !important;
    height: 3.8em !important;
    background-color: {COR_BOTAO_FUNDO} !important;
    color: {COR_BOTAO_TEXTO} !important;
    border: 2px solid {COR_BOTAO_TEXTO} !important;
    border-radius: 12px !important;
    font-weight: 800 !important;
    font-size: 1.1em !important;
    text-transform: uppercase !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
}}

div.stButton > button:active {{
    transform: translateY(2px);
}}

/* -------- BOTÃO VOLTAR -------- */
.nav-btn div.stButton > button {{
    width: auto !important;
    min-width: 100px;
    height: 2.5em !important;
    font-size: 0.9em !important;
    background-color: white !important;
    color: {COR_FUNDO} !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 15px !important;
}}

/* ---------------- INPUTS ---------------- */
.stTextInput input,
.stNumberInput input,
.stDateInput input {{
    background-color: white !important;
    color: {COR_CASTANHO} !important;
    border-radius: 8px !important;
    border: none !important;
}}

/* ---------------- SELECTBOX (STAFF FIX) ---------------- */
.stSelectbox div[data-baseweb="select"] > div {{
    background-color: white !important;
    border-color: white !important;
}}

.stSelectbox span {{
    color: {COR_CASTANHO} !important;
}}

.stSelectbox svg {{
    fill: {COR_CASTANHO} !important;
}}

ul[data-baseweb="menu"] {{
    background-color: white !important;
}}

li[data-baseweb="option"] {{
    color: {COR_CASTANHO} !important;
    background-color: white !important;
}}

li[data-baseweb="option"]:hover,
li[data-baseweb="option"][aria-selected="true"] {{
    background-color: #fce8d4 !important;
    color: {COR_CASTANHO} !important;
}}

/* ---------------- CARDS ---------------- */
.saldo-card {{
    background-color: white;
    border-radius: 20px;
    padding: 20px;
    text-align: center;
    border: 4px solid {COR_BOTAO_TEXTO};
    margin-bottom: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}}

div[data-testid="stImage"] {{
    display: flex;
    justify-content: center;
}}
</style>
""", unsafe_allow_html=True)

# --- LIGAÇÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

PREMIOS_PONTOS = {
    "Dose batatas": 300,
    "Cachorro 3K": 450,
    "Hambúrguer Kão Kente": 500,
    "Kebab de frango": 550,
    "Baconcheeseburger com ovo": 700,
    "Bitoque de frango": 950
}
URL_ENCOMENDAS = "https://www.foodbooking.com/ordering/restaurant/menu?company_uid=e92e9690-8f0b-45e2-acca-6671a872abb9&restaurant_uid=5e09158f-4dc1-4b17-b9d5-687ca8510db8&facebook=true"
URL_LINKTREE = "https://linktr.ee/KaoKente"

# --- NAVEGAÇÃO ---
if 'pagina' not in st.session_state: st.session_state['pagina'] = "home"
if 'user_logado' not in st.session_state: st.session_state['user_logado'] = None

def navegar(destino):
    st.query_params.clear()
    st.session_state['pagina'] = destino
    st.rerun()

# --- LÓGICA ---
def calcular_idade(data_nascimento):
    if not data_nascimento: return 0
    hoje = date.today()
    return hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))

def calcular_pontos_ganhos(valor, tipo):
    mult = 7.5 if tipo == "Estudante" else 5.0
    return int(int(valor) * mult)

def calcular_metricas(hist_str):
    agora = datetime.now()
    mes, ano = agora.month, agora.year
    mes_ant = 12 if mes == 1 else mes - 1
    ano_ant = ano - 1 if mes == 1 else ano
    curr, prev = 0.0, 0.0
    if not isinstance(hist_str, str): return 0.0, 0.0
    for linha in hist_str.split('\n'):
        if "Compra" in linha:
            try:
                pt = linha.split('|')
                val = float(pt[1].replace("Compra", "").replace("€", "").strip())
                dt_str = pt[0].strip()
                try: dt = datetime.strptime(dt_str, '%d/%m/%Y %H:%M')
                except: dt = datetime.strptime(dt_str, '%d/%m %H:%M').replace(year=ano)
                if dt.month == mes and dt.year == ano: curr += val
                elif dt.month == mes_ant and dt.year == ano_ant: prev += val
            except: continue
    return curr, prev

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        if df is None or df.empty: 
            return pd.DataFrame(columns=["Telemovel", "Nome", "Apelido", "Email", "Pontos", "Historico", "Password", "Tipo", "Idade", "ComidaFavorita", "Localidade"])
        df['Telemovel'] = pd.to_numeric(df['Telemovel'], errors='coerce').fillna(0).astype(int).astype(str).replace('0', '')
        cols_str = ['Nome', 'Apelido', 'Email', 'Historico', 'Password', 'Tipo', 'ComidaFavorita', 'Localidade']
        for c in cols_str:
            if c not in df.columns: df[c] = ""
            df[c] = df[c].astype(str).replace('nan', '')
        if 'Pontos' not in df.columns: df['Pontos'] = 0
        df['Pontos'] = pd.to_numeric(df['Pontos'], errors='coerce').fillna(0).astype(int)
        if 'Idade' not in df.columns: df['Idade'] = 0
        df['Idade'] = pd.to_numeric(df['Idade'], errors='coerce').fillna(0).astype(int)
        return df[df['Telemovel'].str.len() > 3]
    except: return pd.DataFrame()

def save_data(df):
    try:
        conn.update(worksheet="Sheet1", data=df)
        st.cache_data.clear()
    except Exception as e: st.error(f"Erro: {e}")

# --- COMPONENTES VISUAIS ---
def render_logo_big():
    st.markdown(f"""
        <div style="display: flex; justify-content: center; margin-bottom: 10px;">
            <div style="background-color: white; border-radius: 50%; padding: 5px; width: 165px; height: 165px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                <a href="https://kaokente.streamlit.app/" target="_self">
                    <img src="{logo_b64}" width="160" style="border-radius: 50%;">
                </a>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_navigation(show_logo=True):
    # APENAS BOTÃO VOLTAR (Sem logo pequeno)
    st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
    if st.button("⬅ VOLTAR"):
        navegar("home")
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# PÁGINA: HOME
# =========================================================
def pagina_home(df):
    render_logo_big()
    
    user = st.session_state['user_logado']
    
    if user is None:
        st.markdown("<h3 style='text-align: center; margin-top: 10px;'>Bem vindo ao Kão Kente!<br>Já nos conhecemos?</h3>", unsafe_allow_html=True)
    else:
        primeiro_nome = user['Nome'].split(" ")[0]
        st.markdown(f"<h3 style='text-align: center; margin-top: 10px;'>Bem vindo ao Kão Kente, {primeiro_nome}!<br>O que vai ser hoje?</h3>", unsafe_allow_html=True)

    st.write("") 

    if st.button("🛵 ENCOMENDAR ON-LINE"):
        navegar("encomendas")

    st.write("")

    if user is None:
        if st.button("👤 ENTRAR OU CRIAR CONTA"):
            navegar("login_menu")
    else:
        if st.button("🏆 OS MEUS PONTOS"):
            navegar("pontos")

    st.write("")

    st.markdown(f"""
    <a href="{URL_LINKTREE}" target="_blank" style="text-decoration: none;">
        <div style="
            background-color: {COR_VERDE_CLARO}; 
            color: white; 
            line-height: 3.8em;
            height: 3.8em;
            border-radius: 12px; 
            text-align: center; 
            font-weight: 800; 
            font-size: 1.1em;
            border: 2px solid white; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.2); 
            text-transform: uppercase; 
            display: block; 
            width: 100%;
            margin-top: 10px;">
            🌲 LinkTree Kão Kente
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    if user is not None:
        st.write("")
        st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
        if st.button("Sair"):
            st.session_state['user_logado'] = None
            navegar("home")
        st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# PÁGINA: ENCOMENDAS
# =========================================================
def pagina_encomendas():
    render_navigation(show_logo=False)
    
    st.markdown(f"<h2>Encomendar Online</h2>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <a href="?menu=gest" target="_self" style="text-decoration: none;">
        <div style="
            background-color: white; color: #856404; padding: 15px;
            border-radius: 10px; border: 1px solid #ffeeba;
            margin-bottom: 15px; text-align: center; font-size: 0.9em;
        ">
            Dica: Se a nossa plataforma de pedidos on-line não aparecer nesta página devido a um aviso de cookies (ou se a quiseres utilizar numa nova janela dedicada), basta clicar no botão abaixo!
        </div>
    </a>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <a href="{URL_ENCOMENDAS}" target="_blank" style="text-decoration: none;">
        <div style="
            background-color: {COR_BOTAO_FUNDO}; color: {COR_BOTAO_TEXTO}; 
            line-height: 3.8em; height: 3.8em; border-radius: 12px; 
            text-align: center; font-weight: 800; font-size: 1.1em;
            border: 2px solid {COR_BOTAO_TEXTO}; box-shadow: 0 4px 6px rgba(0,0,0,0.2); 
            text-transform: uppercase; display: block; width: 100%;">
            ABRIR EMENTA COMPLETA ↗
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True) 
    
    try:
        components.iframe(URL_ENCOMENDAS, height=800, scrolling=True)
    except:
        pass

# =========================================================
# PÁGINA: LOGIN & REGISTO
# =========================================================
def pagina_login_menu(df):
    render_logo_big() 
    render_navigation(show_logo=False)
    
    st.markdown("""<style>.stTabs [data-baseweb="tab-list"] button {color: white !important;}</style>""", unsafe_allow_html=True)
    
    tab_login, tab_registo = st.tabs(["ENTRAR", "CRIAR CONTA NOVA"])
    
    with tab_login:
        st.write("")
        st.markdown("<p style='text-align: center'>Podes entrar com Telemóvel ou E-mail.</p>", unsafe_allow_html=True)
        login_user = st.text_input("Telemóvel ou E-mail")
        login_pass = st.text_input("Palavra-passe", type="password")
        if st.button("ENTRAR"):
            input_limpo = login_user.strip()
            u_tel = df[(df['Telemovel'] == input_limpo) & (df['Password'] == login_pass)]
            u_mail = df[(df['Email'].str.lower() == input_limpo.lower()) & (df['Password'] == login_pass)]
            user_found = None
            if not u_tel.empty: user_found = u_tel.iloc[0]
            elif not u_mail.empty: user_found = u_mail.iloc[0]
            if user_found is not None:
                st.session_state['user_logado'] = user_found
                navegar("home")
            else: st.error("Dados incorretos.")

    with tab_registo:
        st.write("")
        st.markdown("**Preenche os dados para aderir ao clube:**")
        r_nome = st.text_input("Nome próprio")
        r_apelido = st.text_input("Apelido")
        r_tel = st.text_input("Número de telemóvel")
        r_email = st.text_input("E-mail")
        r_pass1 = st.text_input("Palavra-passe", type="password", key="p1")
        r_pass2 = st.text_input("Repetir Palavra-passe", type="password", key="p2")
        
        r_nascimento = st.date_input("Data de Nascimento", min_value=date(1920, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
        idade_calc = calcular_idade(r_nascimento)
        
        tipo_final = "Normal"
        if idade_calc > 0 and idade_calc <= 19:
            resp_escola = st.radio("És aluno do Agrupamento de Escolas de Vila Viçosa?", ["Não", "Sim"], horizontal=True)
            if resp_escola == "Sim":
                tipo_final = "Estudante"
        
        r_comida = st.text_input("Comida Favorita no Kão Kente")
        r_local = st.text_input("Localidade de Residência")
        
        st.write("")
        if st.button("CRIAR CONTA AGORA"):
            if not (r_nome and r_tel and r_email and r_pass1):
                st.error("Preenche os campos obrigatórios.")
            elif r_pass1 != r_pass2:
                st.error("As palavras-passe não coincidem.")
            elif r_tel in df['Telemovel'].values:
                st.error("Este número de telemóvel já está registado.")
            elif r_email in df['Email'].values and r_email != "":
                st.error("Este e-mail já está registado.")
            else:
                novo = pd.DataFrame([{
                    "Telemovel": str(r_tel), "Nome": r_nome, "Apelido": r_apelido,
                    "Email": r_email, "Pontos": 0, "Historico": f"Conta criada em {datetime.now().strftime('%d/%m/%Y')}",
                    "Password": r_pass1, "Tipo": tipo_final, "Idade": idade_calc, 
                    "ComidaFavorita": r_comida, "Localidade": r_local
                }])
                df = pd.concat([df, novo], ignore_index=True)
                save_data(df)
                st.balloons()
                st.success("Conta criada! Podes fazer login.")

# =========================================================
# PÁGINA: PONTOS
# =========================================================
def pagina_pontos(df):
    render_navigation(show_logo=False)
    user = st.session_state['user_logado']
    user = df[df['Telemovel'] == user['Telemovel']].iloc[0]
    
    st.markdown(f"<h2>Área Pessoal</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3>{user['Nome']} {user['Apelido']}</h3>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="saldo-card">
        <div style="color: {COR_CASTANHO}; font-size: 1.1em; font-weight: bold; letter-spacing: 1px;">SALDO DISPONÍVEL</div>
        <div style="color: {COR_BOTAO_FUNDO}; font-size: 4em; font-weight: 900;">{user['Pontos']}</div>
        <div style="color: #888;">pontos acumulados</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("🎁 **Progresso para Recompensas:**")
    for p, custo in PREMIOS_PONTOS.items():
        percentagem = min(user['Pontos'] / custo, 1.0)
        percentagem_txt = int(percentagem * 100)
        can = percentagem >= 1.0
        icon = '✅' if can else '🔒'
        cor_barra = COR_VERDE_ESCURO if can else COR_BOTAO_FUNDO
        
        st.markdown(f"""
        <div style="background-color: white; border-radius: 15px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                <div style="font-weight: bold; color: {COR_CASTANHO}; font-size: 1.1em;">{p}</div>
                <div style="font-size: 1.5em;">{icon}</div>
            </div>
            <div style="color: #666; font-size: 0.9em; margin-bottom: 8px; text-align: left;">
                {user['Pontos']} / {custo} pts ({percentagem_txt}%)
            </div>
            <div style="width: 100%; background-color: #eee; border-radius: 10px; height: 12px; overflow: hidden;">
                <div style="width: {percentagem_txt}%; background-color: {cor_barra}; height: 100%; border-radius: 10px; transition: width 0.5s;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# PÁGINA: ADMIN
# =========================================================
def pagina_admin_login():
    render_navigation(show_logo=False)
    st.markdown("<h2>Acesso Staff</h2>", unsafe_allow_html=True)
    pwd = st.text_input("Password", type="password")
    if pwd == st.secrets.get("admin_password", "kaokente123"):
        st.session_state['admin_ok'] = True
        navegar("admin_panel")
    elif pwd:
        st.error("Errado")

def pagina_admin_panel(df):
    st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
    if st.button("⬅ Sair"): 
        st.session_state['admin_ok'] = False
        navegar("home")
    st.markdown('</div>', unsafe_allow_html=True)
        
    st.title("🔐 Gestão")
    q = st.text_input("🔍 Pesquisar")
    df_show = df.copy()
    if q: df_show = df[df['Nome'].str.lower().str.contains(q.lower()) | df['Telemovel'].str.contains(q)]
    opcoes = df_show['Telemovel'].tolist()
    sel = st.selectbox("Selecionar Cliente", opcoes, format_func=lambda x: f"{df[df['Telemovel']==x]['Nome'].values[0]} {df[df['Telemovel']==x]['Apelido'].values[0]} ({x})") if opcoes else None
    
    if sel:
        d = df[df['Telemovel'] == sel].iloc[0]
        ga, gb = calcular_metricas(d['Historico'])
        st.info(f"**{d['Nome']} {d['Apelido']}** | {d['Tipo']} | {d['Idade']} Anos")
        c1, c2, c3 = st.columns(3)
        c1.metric("Pontos", d['Pontos'])
        c2.metric("Mês Atual", f"{ga}€")
        c3.metric("Mês Pass.", f"{gb}€")
        
        st.markdown("""<style>.stTabs [data-baseweb="tab-list"] button {color: white !important;}</style>""", unsafe_allow_html=True)
        t1, t2, t3, t4 = st.tabs(["💰 Lançar", "🎁 Resgatar", "✏️ Editar", "📊 Tabela"])
        
        with t1:
            v = st.number_input("Valor €", step=0.5)
            pg = calcular_pontos_ganhos(v, d['Tipo'])
            st.write(f"Ganha: **{pg}** pts")
            if st.button("Lançar"):
                idx = df[df['Telemovel']==sel].index[0]
                df.at[idx, 'Pontos'] += pg
                df.at[idx, 'Historico'] = f"{datetime.now().strftime('%d/%m/%Y %H:%M')} | Compra {v}€ | +{pg} pts\n" + str(df.at[idx, 'Historico'])
                save_data(df)
                st.success("OK")
        with t2:
            pr = st.selectbox("Prémio", list(PREMIOS_PONTOS.keys()))
            if st.button("Resgatar"):
                custo = PREMIOS_PONTOS[pr]
                if d['Pontos'] >= custo:
                    idx = df[df['Telemovel']==sel].index[0]
                    df.at[idx, 'Pontos'] -= custo
                    df.at[idx, 'Historico'] = f"{datetime.now().strftime('%d/%m/%Y %H:%M')} | Resgate {pr} | -{custo} pts\n" + str(df.at[idx, 'Historico'])
                    save_data(df)
                    st.success("OK")
                else: st.error("Falta saldo")
        with t3:
            st.markdown("### Editar Dados")
            with st.form("edit"):
                c_a, c_b = st.columns(2)
                with c_a: en = st.text_input("Nome", value=d['Nome'])
                with c_b: ea = st.text_input("Apelido", value=d['Apelido'])
                c_c, c_d = st.columns(2)
                with c_c: em = st.text_input("Email", value=d['Email'])
                with c_d: etel = st.text_input("Telemóvel", value=d['Telemovel'])
                et = st.selectbox("Tipo", ["Normal", "Estudante"], index=0 if d['Tipo']=="Normal" else 1)
                ei = st.number_input("Idade", value=int(d['Idade']) if d['Idade']!="" else 0)
                ep = st.number_input("Pontos (Manual)", value=int(d['Pontos']))
                eloc = st.text_input("Localidade", value=d['Localidade'])
                efood = st.text_input("Comida Fav.", value=d['ComidaFavorita'])
                if st.form_submit_button("💾 Guardar"):
                    idx = df[df['Telemovel']==sel].index[0]
                    df.at[idx, 'Nome'] = en; df.at[idx, 'Apelido'] = ea; df.at[idx, 'Email'] = em; df.at[idx, 'Telemovel'] = etel
                    df.at[idx, 'Tipo'] = et; df.at[idx, 'Idade'] = ei; df.at[idx, 'Pontos'] = ep; df.at[idx, 'Localidade'] = eloc; df.at[idx, 'ComidaFavorita'] = efood
                    save_data(df); st.success("Guardado")
            st.divider()
            with st.expander("🗑️ Apagar Cliente"):
                st.markdown(f"""
                <div style="background-color: #ffcdd2; padding: 20px; border-radius: 10px; border: 3px solid #b71c1c; text-align: center;">
                    <h3 style="color: #b71c1c !important;">⚠️ ATENÇÃO ⚠️</h3>
                    <p style="color: black; font-weight: bold;">Este cliente tem:</p>
                    <h1 style="color: #b71c1c !important; font-size: 3em !important;">{d['Pontos']} PONTOS</h1>
                    <p style="color: black;">MEMORIZE ESTE VALOR ANTES DE APAGAR!</p>
                </div>""", unsafe_allow_html=True)
                if st.button("CONFIRMAR: APAGAR PERMANENTEMENTE"):
                    idx = df[df['Telemovel']==sel].index[0]
                    df = df.drop(idx)
                    save_data(df)
                    st.success("Apagado.")
                    st.rerun()
        with t4:
            st.warning("Área Restrita")
            pass_master = st.text_input("Password Mestra", type="password")
            if pass_master == "masterkk": st.dataframe(df)

# --- MAIN LOOP ---
df = load_data()
p = st.session_state['pagina']
if p == "home": pagina_home(df)
elif p == "encomendas": pagina_encomendas()
elif p == "login_menu": pagina_login_menu(df)
elif p == "pontos": pagina_pontos(df)
elif p == "admin_login": pagina_admin_login()
elif p == "admin_panel": pagina_admin_panel(df)