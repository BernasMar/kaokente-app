import streamlit as st
import pandas as pd
import math
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Kão Kente", page_icon="logo.png", layout="wide")

# --- CORES DA MARCA ---
COR_FUNDO = "#9dddf9"      # Azul claro
COR_LARANJA = "#f68625"
COR_VERDE_CLARO = "#8db842"
COR_VERDE_ESCURO = "#0d974d"
COR_CASTANHO = "#946128"
COR_CINZA = "#aea9a3"

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

    /* Estilo dos Títulos */
    h1, h2, h3 {{
        color: {COR_CASTANHO} !important;
        text-align: center !important;
    }}
    
    p, div, span {{
        color: #333;
    }}

    /* Estilo Geral dos Botões (Removemos o branco) */
    .stButton > button {{
        width: 100%;
        border-radius: 15px;
        height: 3.8em;
        font-weight: bold;
        font-size: 1.1em;
        border: none;
        box-shadow: 0 4px 0px rgba(0,0,0,0.2); /* Efeito 3D subtil */
        transition: all 0.2s;
        color: white !important;
    }}
    
    .stButton > button:active {{
        transform: translateY(2px);
        box-shadow: 0 2px 0px rgba(0,0,0,0.2);
    }}

    /* Classes para injetar cores nos botões via Python */
    /* Nota: O Streamlit não deixa injetar classes diretamente nos botões facilmente,
       então usamos o st.markdown para criar botões HTML ou aceitamos as cores do tema.
       Vou forçar as cores primárias abaixo. */
    
    /* Inputs de texto (Login/Registo) */
    .stTextInput > div > div > input {{
        border-radius: 10px;
        border: 2px solid {COR_CASTANHO};
        color: {COR_CASTANHO};
    }}
    
    /* Métricas */
    div[data-testid="stMetricValue"] {{
        color: {COR_LARANJA} !important;
        font-size: 2.5em !important;
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

# --- GESTÃO DE ESTADO (NAVEGAÇÃO INSTANTÂNEA) ---
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
        
        # Limpeza robusta para garantir que Telemovel é String sem .0
        # Primeiro converte para numerico para tirar lixo, depois int, depois str
        df['Telemovel'] = pd.to_numeric(df['Telemovel'], errors='coerce').fillna(0).astype(int).astype(str)
        df['Telemovel'] = df['Telemovel'].replace('0', '') # Remove zeros gerados por erros
        
        # Outras colunas
        cols_str = ['Nome', 'Apelido', 'Email', 'Historico', 'Password', 'Tipo', 'ComidaFavorita', 'Localidade']
        for c in cols_str:
            if c not in df.columns: df[c] = ""
            df[c] = df[c].astype(str).replace('nan', '')

        if 'Pontos' not in df.columns: df['Pontos'] = 0
        df['Pontos'] = pd.to_numeric(df['Pontos'], errors='coerce').fillna(0).astype(int)
        
        if 'Idade' not in df.columns: df['Idade'] = 0
        df['Idade'] = pd.to_numeric(df['Idade'], errors='coerce').fillna(0).astype(int)
        
        return df[df['Telemovel'].str.len() > 3] # Filtra linhas vazias
    except Exception as e:
        # st.error(f"Debug DB: {e}") # Descomentar para ver erro
        return pd.DataFrame()

def save_data(df):
    try:
        conn.update(worksheet="Sheet1", data=df)
        st.cache_data.clear()
    except Exception as e: st.error(f"Erro ao gravar: {e}")

# --- COMPONENTES VISUAIS ---
def render_logo():
    # Logótipo Grande e Centrado
    try:
        st.image("logo.png", width=180) 
    except:
        st.markdown(f"<h1 style='color:{COR_LARANJA}'>Kão Kente</h1>", unsafe_allow_html=True)

def botao_custom(texto, cor_fundo, key_btn=None, on_click=None):
    # Truque CSS para pintar o botão específico
    st.markdown(f"""
        <style>
        div.stButton > button:first-child {{
            background-color: {cor_fundo} !important;
            color: white !important;
        }}
        </style>""", unsafe_allow_html=True)
    return st.button(texto, key=key_btn, on_click=on_click)

# =========================================================
# PÁGINA: HOME (DINÂMICA)
# =========================================================
def pagina_home(df):
    render_logo()
    
    user = st.session_state['user_logado']
    
    if user is None:
        # VISÃO: NÃO LOGADO
        st.markdown("<h3>Bem vindo ao Kão Kente!<br>Já nos conhecemos?</h3>", unsafe_allow_html=True)
        st.write("")
        st.write("")

        # 1. Botão Encomendar (Laranja)
        st.markdown(f"""<style>div.stButton > button {{background-color: {COR_LARANJA} !important;}}</style>""", unsafe_allow_html=True)
        if st.button("🛵  ENCOMENDAR ON-LINE"):
            navegar("encomendas")

        st.write("")

        # 2. Botão Entrar / Criar Conta (Verde Escuro)
        st.markdown(f"""<style>div.stButton > button {{background-color: {COR_VERDE_ESCURO} !important;}}</style>""", unsafe_allow_html=True)
        if st.button("👤  ENTRAR OU CRIAR CONTA"):
            navegar("login_menu")

        st.write("")
        
        # 3. Botão Linktree (Verde Claro)
        st.markdown(f"""
        <a href="{URL_LINKTREE}" target="_blank" style="text-decoration: none;">
            <div style="background-color: {COR_VERDE_CLARO}; color: white; padding: 15px; border-radius: 15px; text-align: center; font-weight: bold; box-shadow: 0 4px 0px rgba(0,0,0,0.1);">
                🌲 LinkTree Kão Kente
            </div>
        </a>
        """, unsafe_allow_html=True)

        # Rodapé Admin
        st.write("")
        st.write("")
        st.divider()
        col1, col2 = st.columns([1,3])
        with col1:
            if st.button("🔐 Staff"): navegar("admin_login")

    else:
        # VISÃO: LOGADO
        primeiro_nome = user['Nome'].split(" ")[0]
        st.markdown(f"<h3>Bem vindo ao Kão Kente, {primeiro_nome}!<br>O que vai ser hoje?</h3>", unsafe_allow_html=True)
        st.write("")
        
        # 1. Encomendar (Laranja)
        st.markdown(f"""<style>div.stButton > button {{background-color: {COR_LARANJA} !important;}}</style>""", unsafe_allow_html=True)
        if st.button("🛵  ENCOMENDAR ON-LINE"):
            navegar("encomendas")
            
        st.write("")
        
        # 2. Meus Pontos (Verde Escuro)
        st.markdown(f"""<style>div.stButton > button {{background-color: {COR_VERDE_ESCURO} !important;}}</style>""", unsafe_allow_html=True)
        if st.button("🏆  OS MEUS PONTOS"):
            navegar("pontos")

        st.write("")

        # 3. Linktree
        st.markdown(f"""
        <a href="{URL_LINKTREE}" target="_blank" style="text-decoration: none;">
            <div style="background-color: {COR_VERDE_CLARO}; color: white; padding: 15px; border-radius: 15px; text-align: center; font-weight: bold; box-shadow: 0 4px 0px rgba(0,0,0,0.1);">
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
    
    # --- LOGIN ---
    with tab_login:
        st.write("")
        st.info("Podes entrar com Telemóvel ou E-mail.")
        
        login_user = st.text_input("Telemóvel ou E-mail")
        login_pass = st.text_input("Palavra-passe", type="password")
        
        st.markdown(f"""<style>div.stButton > button {{background-color: {COR_VERDE_ESCURO} !important;}}</style>""", unsafe_allow_html=True)
        if st.button("ENTRAR"):
            # Lógica de Login Híbrido
            input_limpo = login_user.strip()
            
            # Tenta encontrar por telemóvel (exato) OU por email (case insensitive)
            u_tel = df[(df['Telemovel'] == input_limpo) & (df['Password'] == login_pass)]
            u_mail = df[(df['Email'].str.lower() == input_limpo.lower()) & (df['Password'] == login_pass)]
            
            user_found = None
            if not u_tel.empty: user_found = u_tel.iloc[0]
            elif not u_mail.empty: user_found = u_mail.iloc[0]
            
            if user_found is not None:
                st.session_state['user_logado'] = user_found
                st.success(f"Olá {user_found['Nome']}!")
                navegar("home")
            else:
                st.error("Dados incorretos. Verifica se já criaste conta nova.")

    # --- REGISTO (NOVO PARADIGMA) ---
    with tab_registo:
        st.write("")
        st.markdown("**Preenche os dados para aderir ao clube:**")
        
        with st.form("form_registo"):
            col_a, col_b = st.columns(2)
            with col_a:
                r_nome = st.text_input("Nome Próprio")
            with col_b:
                r_apelido = st.text_input("Apelido")
            
            r_tel = st.text_input("Número de Telemóvel")
            r_email = st.text_input("E-mail")
            
            c_p1, c_p2 = st.columns(2)
            with c_p1: r_pass1 = st.text_input("Palavra-passe", type="password")
            with c_p2: r_pass2 = st.text_input("Repetir Palavra-passe", type="password")
            
            r_idade = st.number_input("Idade", min_value=5, max_value=100, step=1)
            
            # Lógica Estudante
            is_estudante_check = False
            if r_idade > 0 and r_idade <= 19:
                st.markdown(f"Tens {r_idade} anos. Frequentadora do Agrupamento?")
                is_estudante_check = st.checkbox("Sim, sou estudante do Agrupamento de Escolas de Vila Viçosa")
            
            r_comida = st.text_input("Comida Favorita no Kão Kente")
            r_local = st.text_input("Localidade de Residência")
            
            submitted = st.form_submit_button("CRIAR CONTA")
            
            if submitted:
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
                    # Define Tipo
                    tipo_final = "Estudante" if (is_estudante_check and r_idade <= 19) else "Normal"
                    
                    # Cria novo registo
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
                    st.success("Conta criada com sucesso! Podes fazer login.")

# =========================================================
# PÁGINA: PONTOS (ÁREA PESSOAL)
# =========================================================
def pagina_pontos(df):
    if st.button("⬅ Voltar"): navegar("home")
    
    user = st.session_state['user_logado']
    # Atualiza dados frescos
    user = df[df['Telemovel'] == user['Telemovel']].iloc[0]
    
    st.markdown(f"<h2 style='color:{COR_VERDE_ESCURO}'>Área Pessoal</h2>", unsafe_allow_html=True)
    st.markdown(f"**Cliente:** {user['Nome']} {user['Apelido']}")
    
    # CARD SALDO
    st.markdown(f"""
    <div style="background-color: white; padding: 20px; border-radius: 15px; text-align: center; border: 3px solid {COR_LARANJA}; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="color: {COR_CASTANHO}; font-size: 1.1em; font-weight: bold;">SALDO DISPONÍVEL</div>
        <div style="color: {COR_LARANJA}; font-size: 3.5em; font-weight: bold;">{user['Pontos']}</div>
        <div style="color: {COR_CINZA};">pontos acumulados</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("🎁 **Trocar Pontos por Ofertas:**")
    
    c1, c2 = st.columns(2)
    for i, (p, c) in enumerate(PREMIOS_PONTOS.items()):
        can = user['Pontos'] >= c
        cor_borda = COR_VERDE_ESCURO if can else "#ddd"
        bg_color = "white"
        icon = '✅' if can else '🔒'
        
        html_card = f"""
        <div style="border: 2px solid {cor_borda}; border-radius: 10px; padding: 10px; margin-bottom: 10px; height: 100%; background-color: {bg_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="font-weight: bold; color: {COR_CASTANHO}; font-size: 0.95em; line-height: 1.2;">{p}</div>
            <div style="color: {COR_CINZA}; font-size: 0.9em; margin-top: 5px;">{c} pts</div>
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
    
    st.markdown(f"<h2 style='color:{COR_LARANJA}'>Encomendar Online</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #ffeeba; margin-bottom: 15px; text-align: center;">
        <b>Dica:</b> Se o menu não aparecer em baixo, clica no botão laranja!
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <a href="{URL_ENCOMENDAS}" target="_blank" style="text-decoration: none;">
        <div style="
            background-color: {COR_LARANJA}; color: white; padding: 16px; 
            border-radius: 15px; text-align: center; font-weight: bold; 
            font-size: 1.2em; margin-bottom: 20px; box-shadow: 0 4px 0px rgba(0,0,0,0.2);">
            ABRIR EMENTA COMPLETA ↗
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    try:
        components.iframe(URL_ENCOMENDAS, height=800, scrolling=True)
    except:
        pass

# =========================================================
# PÁGINA: ADMIN (STAFF)
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
    
    # Filtro
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