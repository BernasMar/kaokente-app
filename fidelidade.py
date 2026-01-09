import streamlit as st
import pandas as pd
import base64
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Kão Kente", page_icon="logo.png", layout="wide")

# --- FUNÇÃO PARA CARREGAR IMAGEM LOCAL PARA HTML ---
def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except:
        return "" # Retorna vazio se não encontrar a imagem

# Carrega o logo para usar no HTML
logo_b64 = get_image_base64("logo.png")

# --- CSS PERSONALIZADO (A Barra Laranja e Estilos) ---
st.markdown(f"""
    <style>
    /* Remove margens padrão do Streamlit para a barra ficar no topo */
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 5rem;
    }}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* BARRA DE NAVEGAÇÃO SUPERIOR */
    .navbar {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #f68625;
        color: white;
        padding: 10px 20px;
        display: flex;
        align-items: center;
        z-index: 999;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }}
    
    .navbar-logo {{
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: white;
        background-image: url('{logo_b64}');
        background-size: cover;
        background-position: center;
        margin-right: 15px;
        border: 2px solid white;
    }}
    
    .navbar-title {{
        font-size: 1.2rem;
        font-weight: bold;
        letter-spacing: 1px;
    }}

    /* Botões Personalizados */
    .stButton > button {{
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.1s;
    }}
    .stButton > button:active {{
        transform: scale(0.98);
    }}
    
    /* Cores Específicas */
    .laranja-btn > button {{ background-color: #f68625 !important; color: white !important; }}
    .verde-btn > button {{ background-color: #0d974d !important; color: white !important; }}
    
    /* Métricas */
    div[data-testid="stMetricValue"] {{
        color: #f68625;
    }}
    </style>
    
    <div class="navbar">
        <div class="navbar-logo"></div>
        <div class="navbar-title">Kão Kente</div>
    </div>
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

# --- SISTEMA DE NAVEGAÇÃO (URL QUERY PARAMS) ---
# Isto permite usar os botões de voltar do browser
def get_pagina_atual():
    # Lê o parâmetro ?page=... do URL
    params = st.query_params
    return params.get("page", "home")

def navegar_para(pagina):
    # Atualiza o URL e recarrega
    st.query_params["page"] = pagina
    # st.rerun() # Normalmente o update do query param já atualiza, mas forçamos se necessário

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
        if df is None or df.empty: return pd.DataFrame(columns=["Telemovel", "Nome", "Pontos", "Historico", "Password", "Tipo"])
        df['Telemovel'] = df['Telemovel'].astype(str).replace('nan', '')
        df['Pontos'] = pd.to_numeric(df['Pontos'], errors='coerce').fillna(0).astype(int)
        df['Historico'] = df['Historico'].astype(str).replace('nan', '')
        df['Password'] = df['Password'].astype(str).replace('nan', '')
        df['Tipo'] = df['Tipo'].astype(str).replace('nan', 'Normal')
        return df[df['Telemovel'].str.len() > 3]
    except: return pd.DataFrame()

def save_data(df):
    try:
        conn.update(worksheet="Sheet1", data=df)
        st.cache_data.clear()
    except Exception as e: st.error(f"Erro: {e}")

# --- PÁGINAS ---

def pagina_home():
    st.write("") # Espaço para não ficar colado à barra laranja
    st.markdown("<h3 style='text-align: center; color: #946128;'>O que te apetece hoje?</h3>", unsafe_allow_html=True)
    st.write("")
    
    st.markdown('<div class="laranja-btn">', unsafe_allow_html=True)
    if st.button("🛵  ENCOMENDAR ONLINE", key="btn_enc"):
        navegar_para("encomendas")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("")
    
    st.markdown('<div class="verde-btn">', unsafe_allow_html=True)
    if st.button("🏆  MEUS PONTOS E OFERTAS", key="btn_pts"):
        navegar_para("pontos")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Admin Rodapé
    st.write("")
    st.write("")
    st.divider()
    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("🔐 Staff"):
            navegar_para("admin")
            st.rerun()

def pagina_encomendas():
    if st.button("⬅ Voltar ao Menu"):
        navegar_para("home")
        st.rerun()
        
    st.markdown("<h2 style='text-align: center; color: #f68625;'>Encomendar Online</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; border: 1px solid #ffeeba; margin-bottom: 15px; font-size: 0.9em;">
        📱 <b>Utilizadores iPhone / Safari:</b><br>
        Se aparecer um aviso de cookies em baixo, <b>clique no botão laranja</b> para abrir o menu sem erros.
    </div>
    """, unsafe_allow_html=True)

    # Botão Laranja Link Externo
    st.markdown(f"""
    <a href="{URL_ENCOMENDAS}" target="_blank" style="text-decoration: none;">
        <div style="
            background-color: #f68625; color: white; padding: 16px; 
            border-radius: 12px; text-align: center; font-weight: bold; 
            font-size: 1.1em; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            ABRIR EMENTA (NOVO SEPARADOR) ↗
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    try:
        components.iframe(URL_ENCOMENDAS, height=800, scrolling=True)
    except:
        st.warning("Menu indisponível nesta visualização. Use o botão acima.")

def pagina_pontos(df):
    if st.button("⬅ Voltar ao Menu"):
        navegar_para("home")
        st.rerun()
        
    st.markdown("<h2 style='text-align: center; color: #0d974d;'>Clube de Pontos</h2>", unsafe_allow_html=True)

    if 'user_logado' not in st.session_state: st.session_state['user_logado'] = None
    
    if st.session_state['user_logado'] is None:
        st.info("Faz login para veres o teu saldo.")
        lt = st.text_input("Telemóvel")
        lp = st.text_input("Password", type="password")
        st.markdown('<div class="verde-btn">', unsafe_allow_html=True)
        if st.button("Entrar"):
            u = df[(df['Telemovel'].astype(str) == lt.replace(" ", "")) & (df['Password'] == lp)]
            if not u.empty:
                st.session_state['user_logado'] = u.iloc[0]
                st.rerun()
            else: st.error("Dados incorretos.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        user = st.session_state['user_logado']
        # Refresh data
        user = df[df['Telemovel'].astype(str) == str(user['Telemovel'])].iloc[0]
        
        st.markdown(f"**{user['Nome']}** ({user['Tipo']})")
        st.markdown(f"""
        <div style="background-color: #fce8d4; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #f68625; margin-bottom: 20px;">
            <div style="color: #946128;">SALDO DISPONÍVEL</div>
            <div style="color: #f68625; font-size: 2.2em; font-weight: bold;">{user['Pontos']} ⭐</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Sair"):
            st.session_state['user_logado'] = None
            st.rerun()
            
        st.divider()
        st.write("🎁 **Trocar Pontos:**")
        
        c1, c2 = st.columns(2)
        for i, (p, c) in enumerate(PREMIOS_PONTOS.items()):
            can = user['Pontos'] >= c
            with (c1 if i%2==0 else c2):
                st.markdown(f"""
                <div style="border: 1px solid {'#0d974d' if can else '#ddd'}; border-radius: 8px; padding: 10px; margin-bottom: 10px; height: 100%; background-color: {'#e8f5e9' if can else 'white'};">
                    <div style="font-weight: bold; font-size: 0.9em; line-height: 1.2;">{p}</div>
                    <div style="color: #666; font-size: 0.8em;">{c} pts</div>
                    <div style="text-align: right; font-size: 1.2em; margin-top: 5px;">{'✅' if can else '🔒'}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with st.expander("Histórico"): st.text(user['Historico'])

def pagina_admin(df):
    if st.button("⬅ Sair"):
        navegar_para("home")
        st.rerun()
        
    st.title("🔐 Gestão")
    pwd = st.text_input("Password", type="password")
    if pwd == st.secrets.get("admin_password", "kaokente123"):
        q = st.text_input("🔍 Pesquisar")
        lst = df.to_dict('records')
        opts = [str(x['Telemovel']) for x in lst]
        if q: opts = [str(x['Telemovel']) for x in lst if q.lower() in str(x['Nome']).lower() or q in str(x['Telemovel'])]
        
        sel = st.selectbox("Cliente", opts, format_func=lambda x: f"{df[df['Telemovel'].astype(str)==x]['Nome'].values[0]} ({x})") if opts else None
        
        if sel:
            d = df[df['Telemovel'].astype(str) == sel].iloc[0]
            ga, gb = calcular_metricas(d['Historico'])
            st.info(f"{d['Nome']} | {d['Pontos']} pts")
            c1, c2 = st.columns(2)
            c1.metric("Mês Atual", f"{ga}€")
            c2.metric("Mês Passado", f"{gb}€")
            
            t1, t2, t3 = st.tabs(["Lançar", "Resgatar", "Editar"])
            with t1:
                v = st.number_input("Valor €", step=0.5)
                pg = calcular_pontos_ganhos(v, d['Tipo'])
                st.write(f"Ganhará: {pg} pts")
                if st.button("Lançar"):
                    idx = df[df['Telemovel'].astype(str)==sel].index[0]
                    df.at[idx, 'Pontos'] += pg
                    df.at[idx, 'Historico'] = f"{datetime.now().strftime('%d/%m/%Y %H:%M')} | Compra {v}€ | +{pg} pts\n" + str(df.at[idx, 'Historico'])
                    save_data(df)
                    st.success("OK")
            with t2:
                pr = st.selectbox("Prémio", list(PREMIOS_PONTOS.keys()))
                if st.button("Resgatar"):
                    if d['Pontos'] >= PREMIOS_PONTOS[pr]:
                        idx = df[df['Telemovel'].astype(str)==sel].index[0]
                        df.at[idx, 'Pontos'] -= PREMIOS_PONTOS[pr]
                        df.at[idx, 'Historico'] = f"{datetime.now().strftime('%d/%m/%Y %H:%M')} | Resgate {pr} | -{PREMIOS_PONTOS[pr]} pts\n" + str(df.at[idx, 'Historico'])
                        save_data(df)
                        st.success("OK")
                    else: st.error("Sem saldo")
            with t3:
                with st.form("ed"):
                    nn = st.text_input("Nome", value=d['Nome'])
                    np = st.text_input("Pass", value=d['Password'])
                    nt = st.selectbox("Tipo", ["Normal", "Estudante"], index=0 if d['Tipo']=="Normal" else 1)
                    if st.form_submit_button("Guardar"):
                        idx = df[df['Telemovel'].astype(str)==sel].index[0]
                        df.at[idx, 'Nome'] = nn
                        df.at[idx, 'Password'] = np
                        df.at[idx, 'Tipo'] = nt
                        save_data(df)
                        st.success("OK")

        st.divider()
        with st.expander("Novo Cliente"):
            ntel = st.text_input("Novo Tel")
            nnome = st.text_input("Novo Nome")
            npass = st.text_input("Nova Pass")
            ntipo = st.selectbox("Novo Tipo", ["Normal", "Estudante"])
            if st.button("Criar"):
                if ntel and nnome:
                    if ntel in df['Telemovel'].astype(str).values: st.error("Já existe")
                    else:
                        df = pd.concat([df, pd.DataFrame([{"Telemovel": ntel, "Nome": nnome, "Password": npass, "Tipo": ntipo, "Pontos": 0, "Historico": ""}])], ignore_index=True)
                        save_data(df)
                        st.success("Criado")

# --- MAIN LOOP ---
df = load_data()
page = get_pagina_atual()

if page == "home": pagina_home()
elif page == "encomendas": pagina_encomendas()
elif page == "pontos": pagina_pontos(df)
elif page == "admin": pagina_admin(df)