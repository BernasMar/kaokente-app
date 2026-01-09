import streamlit as st
import pandas as pd
import math
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Kão Kente", page_icon="logo.png", layout="wide")

# --- CORES DA MARCA (DEFINIÇÕES CORRIGIDAS) ---
COR_FUNDO = "#8db842"      # Verde Claro (Fundo do site)
COR_AZUL_CLARO = "#9dddf9" # Azul Claro (Fundo dos botões)
COR_LARANJA = "#f68625"    # Laranja Kão Kente (Texto dos botões e Destaques)
COR_VERDE_ESCURO = "#0d974d"
COR_CASTANHO = "#946128"
COR_CINZA = "#aea9a3"
COR_BRANCO = "#ffffff"

# --- CSS PERSONALIZADO (VISUAL COMPLETO) ---
st.markdown(f"""
    <style>
    /* Fundo da Aplicação */
    .stApp {{
        background-color: {COR_FUNDO};
    }}
    
    /* Esconder menus padrão do Streamlit */
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* Estilo dos Títulos e Textos */
    h1, h2, h3, h4 {{
        color: {COR_CASTANHO} !important;
        text-align: center !important;
        font-weight: 800 !important;
    }}
    
    p, label, span, div {{
        color: #2c1e0b; /* Castanho muito escuro para leitura */
        font-weight: 500;
    }}

    /* ESTILO GERAL DOS BOTÕES */
    .stButton > button {{
        width: 100%;
        border-radius: 15px;
        height: 4em;
        background-color: {COR_AZUL_CLARO} !important;
        color: {COR_LARANJA} !important;
        font-weight: 900 !important; /* Negrito extra */
        font-size: 1.2em !important;
        border: 2px solid white !important; /* Borda branca para destacar no verde */
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.2s;
        text-transform: uppercase;
    }}
    
    .stButton > button:hover {{
        transform: scale(1.02);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
        color: {COR_CASTANHO} !important; /* Muda cor ao passar o rato */
    }}

    .stButton > button:active {{
        transform: translateY(2px);
    }}

    /* Inputs de texto (Caixas brancas) */
    .stTextInput > div > div > input, .stNumberInput > div > div > input {{
        border-radius: 10px;
        border: 2px solid white;
        background-color: rgba(255, 255, 255, 0.9);
        color: {COR_CASTANHO};
        font-weight: bold;
    }}
    
    /* Métricas */
    div[data-testid="stMetricValue"] {{
        color: white !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        font-size: 3em !important;
    }}
    div[data-testid="stMetricLabel"] {{
        color: {COR_CASTANHO} !important;
        font-weight: bold;
    }}

    /* Centralização de imagens */
    div[data-testid="stImage"] {{
        display: flex;
        justify-content: center;
    }}
    
    </style>
""", unsafe_allow_html=True)

# --- LIGAÇÃO E DADOS ---
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

# --- GESTÃO DE ESTADO ---
if 'pagina' not in st.session_state:
    st.session_state['pagina'] = "home"
if 'user_logado' not in st.session_state:
    st.session_state['user_logado'] = None

def navegar(destino):
    st.session_state['pagina'] = destino
    st.rerun()

# --- FUNÇÕES LÓGICAS ---
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
        
        df['Telemovel'] = pd.to_numeric(df['Telemovel'], errors='coerce').fillna(0).astype(int).astype(str)
        df['Telemovel'] = df['Telemovel'].replace('0', '')
        
        cols_str = ['Nome', 'Apelido', 'Email', 'Historico', 'Password', 'Tipo', 'ComidaFavorita', 'Localidade']
        for c in cols_str:
            if c not in df.columns: df[c] = ""
            df[c] = df[c].astype(str).replace('nan', '')

        if 'Pontos' not in df.columns: df['Pontos'] = 0
        df['Pontos'] = pd.to_numeric(df['Pontos'], errors='coerce').fillna(0).astype(int)
        
        if 'Idade' not in df.columns: df['Idade'] = 0
        df['Idade'] = pd.to_numeric(df['Idade'], errors='coerce').fillna(0).astype(int)
        
        return df[df['Telemovel'].str.len() > 3]
    except:
        return pd.DataFrame()

def save_data(df):
    try:
        conn.update(worksheet="Sheet1", data=df)
        st.cache_data.clear()
    except Exception as e: st.error(f"Erro ao gravar: {e}")

# --- COMPONENTES VISUAIS ---
def render_logo():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("logo.png", width=200) 
        except:
            st.markdown(f"<h1>Kão Kente</h1>", unsafe_allow_html=True)

# =========================================================
# PÁGINA: HOME
# =========================================================
def pagina_home(df):
    render_logo()
    
    user = st.session_state['user_logado']
    
    if user is None:
        st.markdown("<h3>Bem vindo ao Kão Kente!<br>Já nos conhecemos?</h3>", unsafe_allow_html=True)
        st.write("")
        st.write("")

        if st.button("🛵  ENCOMENDAR ON-LINE"):
            navegar("encomendas")

        st.write("")

        if st.button("👤  ENTRAR OU CRIAR CONTA"):
            navegar("login_menu")

        st.write("")
        
        st.markdown(f"""
        <a href="{URL_LINKTREE}" target="_blank" style="text-decoration: none;">
            <div style="background-color: {COR_AZUL_CLARO}; color: {COR_LARANJA}; padding: 18px; border-radius: 15px; text-align: center; font-weight: 900; font-size: 1.2em; border: 2px solid white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-transform: uppercase;">
                🌲 LinkTree Kão Kente
            </div>
        </a>
        """, unsafe_allow_html=True)

        st.write("")
        st.write("")
        st.divider()
        col1, col2 = st.columns([1,3])
        with col1:
            if st.button("🔐 Staff"): navegar("admin_login")

    else:
        primeiro_nome = user['Nome'].split(" ")[0]
        st.markdown(f"<h3>Bem vindo ao Kão Kente, {primeiro_nome}!<br>O que vai ser hoje?</h3>", unsafe_allow_html=True)
        st.write("")
        
        if st.button("🛵  ENCOMENDAR ON-LINE"):
            navegar("encomendas")
            
        st.write("")
        
        if st.button("🏆  OS MEUS PONTOS"):
            navegar("pontos")

        st.write("")

        st.markdown(f"""
        <a href="{URL_LINKTREE}" target="_blank" style="text-decoration: none;">
            <div style="background-color: {COR_AZUL_CLARO}; color: {COR_LARANJA}; padding: 18px; border-radius: 15px; text-align: center; font-weight: 900; font-size: 1.2em; border: 2px solid white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-transform: uppercase;">
                🌲 LinkTree Kão Kente
            </div>
        </a>
        """, unsafe_allow_html=True)
        
        st.write("")
        if st.button("Sair / Logout"):
            st.session_state['user_logado'] = None
            st.rerun()

# =========================================================
# PÁGINA: LOGIN & REGISTO
# =========================================================
def pagina_login_menu(df):
    render_logo()
    
    if st.button("⬅ Voltar"): navegar("home")
    
    tab_login, tab_registo = st.tabs(["ENTRAR", "CRIAR CONTA NOVA"])
    
    with tab_login:
        st.write("")
        st.info("Podes entrar com Telemóvel ou E-mail.")
        
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
            else:
                st.error("Dados incorretos.")

    with tab_registo:
        st.write("")
        st.markdown("**Preenche os dados para aderir ao clube:**")
        
        col_a, col_b = st.columns(2)
        with col_a:
            r_nome = st.text_input("Nome Próprio")
        with col_b:
            r_apelido = st.text_input("Apelido")
        
        r_tel = st.text_input("Número de Telemóvel")
        r_email = st.text_input("E-mail")
        
        c_p1, c_p2 = st.columns(2)
        with c_p1: r_pass1 = st.text_input("Palavra-passe", type="password", key="p1")
        with c_p2: r_pass2 = st.text_input("Repetir Palavra-passe", type="password", key="p2")
        
        # IDADE REATIVA
        r_idade = st.number_input("Idade", min_value=0, max_value=100, step=1, value=0)
        
        is_estudante_check = False
        
        if r_idade > 0:
            if r_idade <= 19:
                st.markdown(f"**Tens {r_idade} anos. És aluno do Agrupamento de Escolas de Vila Viçosa?**")
                is_estudante_check = st.checkbox("Sim, sou aluno do Agrupamento de Escolas de Vila Viçosa.")
            else:
                st.markdown(f"Tens {r_idade} anos. (Tipo: Normal)")
        
        r_comida = st.text_input("Comida Favorita no Kão Kente")
        r_local = st.text_input("Localidade de Residência")
        
        st.write("")
        # Botão final de submissão
        if st.button("CRIAR CONTA AGORA"):
            # Validações
            if not (r_nome and r_tel and r_email and r_pass1):
                st.error("Preenche os campos obrigatórios.")
            elif r_pass1 != r_pass2:
                st.error("As palavras-passe não coincidem.")
            elif r_tel in df['Telemovel'].values:
                st.error("Este número de telemóvel já está registado.")
            elif r_email in df['Email'].values and r_email != "":
                st.error("Este e-mail já está registado.")
            else:
                tipo_final = "Estudante" if (is_estudante_check and r_idade <= 19) else "Normal"
                
                novo_user = pd.DataFrame([{
                    "Telemovel": str(r_tel),
                    "Nome": r_nome,
                    "Apelido": r_apelido,
                    "Email": r_email,
                    "Pontos": 0,
                    "Historico": f"Conta criada em {datetime.now().strftime('%d/%m/%Y')}",
                    "Password": r_pass1,
                    "Tipo": tipo_final,
                    "Idade": r_idade,
                    "ComidaFavorita": r_comida,
                    "Localidade": r_local
                }])
                
                df = pd.concat([df, novo_user], ignore_index=True)
                save_data(df)
                st.balloons()
                st.success("Conta criada com sucesso! Podes fazer login.")

# =========================================================
# PÁGINA: PONTOS
# =========================================================
def pagina_pontos(df):
    if st.button("⬅ Voltar"): navegar("home")
    
    user = st.session_state['user_logado']
    # Atualiza dados
    user = df[df['Telemovel'] == user['Telemovel']].iloc[0]
    
    st.markdown(f"<h2>Área Pessoal</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center'>{user['Nome']} {user['Apelido']}</h3>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="background-color: #2c1e0b; padding: 20px; border-radius: 20px; text-align: center; border: 4px solid {COR_LARANJA}; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
        <div style="color: white; font-size: 1.1em; font-weight: bold; letter-spacing: 1px;">SALDO DISPONÍVEL</div>
        <div style="color: {COR_LARANJA}; font-size: 4em; font-weight: 900;">{user['Pontos']}</div>
        <div style="color: #ccc;">pontos acumulados</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("🎁 **Trocar Pontos por Ofertas:**")
    
    c1, c2 = st.columns(2)
    for i, (p, c) in enumerate(PREMIOS_PONTOS.items()):
        can = user['Pontos'] >= c
        cor_borda = COR_VERDE_ESCURO if can else "#ddd"
        bg_color = "rgba(255,255,255,0.9)"
        icon = '✅' if can else '🔒'
        
        html_card = f"""
        <div style="border: 3px solid {cor_borda}; border-radius: 12px; padding: 12px; margin-bottom: 12px; height: 100%; background-color: {bg_color};">
            <div style="font-weight: 800; color: {COR_CASTANHO}; font-size: 1em; line-height: 1.1;">{p}</div>
            <div style="color: #555; font-size: 0.9em; margin-top: 5px; font-weight: bold;">{c} pts</div>
            <div style="text-align: right; font-size: 1.5em; margin-top: -10px;">{icon}</div>
        </div>
        """
        with (c1 if i%2==0 else c2):
            st.markdown(html_card, unsafe_allow_html=True)

# =========================================================
# PÁGINA: ENCOMENDAS
# =========================================================
def pagina_encomendas():
    if st.button("⬅ Voltar"): navegar("home")
    
    st.markdown(f"<h2>Encomendar Online</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: white; color: #856404; padding: 15px; border-radius: 10px; border: 2px solid #ffeeba; margin-bottom: 15px; text-align: center;">
        <b>Dica:</b> Se o menu não aparecer em baixo, clica no botão abaixo!
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <a href="{URL_ENCOMENDAS}" target="_blank" style="text-decoration: none;">
        <div style="
            background-color: {COR_AZUL_CLARO}; color: {COR_LARANJA}; padding: 16px; 
            border-radius: 15px; text-align: center; font-weight: 900; 
            font-size: 1.2em; margin-bottom: 20px; box-shadow: 0 4px 0px rgba(0,0,0,0.2); border: 2px solid white; text-transform: uppercase;">
            ABRIR EMENTA COMPLETA ↗
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    try:
        components.iframe(URL_ENCOMENDAS, height=800, scrolling=True)
    except:
        pass

# =========================================================
# PÁGINA: ADMIN
# =========================================================
def pagina_admin_login():
    if st.button("⬅ Voltar"): navegar("home")
    st.markdown("<h2>Acesso Staff</h2>", unsafe_allow_html=True)
    pwd = st.text_input("Password", type="password")
    if pwd == st.secrets.get("admin_password", "kaokente123"):
        st.session_state['admin_ok'] = True
        navegar("admin_panel")
    elif pwd:
        st.error("Errado")

def pagina_admin_panel(df):
    if st.button("⬅ Sair"): 
        st.session_state['admin_ok'] = False
        navegar("home")
        
    st.title("🔐 Gestão")
    
    q = st.text_input("🔍 Pesquisar (Nome ou Telemóvel)")
    
    df_show = df.copy()
    if q:
        df_show = df[df['Nome'].str.lower().str.contains(q.lower()) | df['Telemovel'].str.contains(q)]
    
    opcoes = df_show['Telemovel'].tolist()
    
    sel = st.selectbox("Selecionar Cliente", opcoes, format_func=lambda x: f"{df[df['Telemovel']==x]['Nome'].values[0]} {df[df['Telemovel']==x]['Apelido'].values[0]} ({x})") if opcoes else None
    
    if sel:
        d = df[df['Telemovel'] == sel].iloc[0]
        ga, gb = calcular_metricas(d['Historico'])
        
        st.info(f"**{d['Nome']} {d['Apelido']}** | Tipo: {d['Tipo']} | Idade: {d['Idade']}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Pontos", d['Pontos'])
        c2.metric("Mês Atual", f"{ga}€")
        c3.metric("Mês Pass.", f"{gb}€")
        
        t1, t2, t3 = st.tabs(["Lançar", "Resgatar", "Editar"])
        
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
            with st.form("edit"):
                en = st.text_input("Nome", value=d['Nome'])
                ea = st.text_input("Apelido", value=d['Apelido'])
                ep = st.text_input("Pass", value=d['Password'])
                et = st.selectbox("Tipo", ["Normal", "Estudante"], index=0 if d['Tipo']=="Normal" else 1)
                ei = st.number_input("Idade", value=int(d['Idade']) if d['Idade']!="" else 0)
                if st.form_submit_button("Guardar"):
                    idx = df[df['Telemovel']==sel].index[0]
                    df.at[idx, 'Nome'] = en
                    df.at[idx, 'Apelido'] = ea
                    df.at[idx, 'Password'] = ep
                    df.at[idx, 'Tipo'] = et
                    df.at[idx, 'Idade'] = ei
                    save_data(df)
                    st.success("Guardado")

# --- MAIN LOOP ---
df = load_data()
p = st.session_state['pagina']

if p == "home": pagina_home(df)
elif p == "encomendas": pagina_encomendas()
elif p == "login_menu": pagina_login_menu(df)
elif p == "pontos": pagina_pontos(df)
elif p == "admin_login": pagina_admin_login()
elif p == "admin_panel": pagina_admin_panel(df)