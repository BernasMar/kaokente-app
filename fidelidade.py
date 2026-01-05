import streamlit as st
import pandas as pd
import math
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Kão Kente - App Oficial", page_icon="logo.png", layout="wide")

# --- LIGAÇÃO AO GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- NOVA LISTA DE PRÉMIOS (PONTOS FIXOS) ---
PREMIOS_PONTOS = {
    "Dose batatas": 300,
    "Cachorro 3K": 450,
    "Hambúrguer Kão Kente": 500,
    "Kebab de frango": 550,
    "Baconcheeseburger com ovo": 700,
    "Bitoque de frango": 950
}

# --- URL DE ENCOMENDAS ---
URL_ENCOMENDAS = "https://www.foodbooking.com/ordering/restaurant/menu?company_uid=e92e9690-8f0b-45e2-acca-6671a872abb9&restaurant_uid=5e09158f-4dc1-4b17-b9d5-687ca8510db8&facebook=true"

# --- FUNÇÃO PARA CRIAR BOTÃO LARANJA PERSONALIZADO ---
def botao_laranja(texto, link):
    st.markdown(f"""
    <a href="{link}" target="_blank">
        <div style="
            background-color: #F58C21;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 20px;
            text-decoration: none;
            display: inline-block;
            width: 100%;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        ">
            {texto} ↗
        </div>
    </a>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE LÓGICA ---
def calcular_pontos_ganhos(valor_gasto, tipo_cliente):
    valor_inteiro = int(valor_gasto)
    multiplicador = 7.5 if tipo_cliente == "Estudante" else 5.0
    return int(valor_inteiro * multiplicador)

def calcular_metricas_mensais(historico_str):
    agora = datetime.now()
    mes_atual = agora.month
    ano_atual = agora.year
    
    if mes_atual == 1:
        mes_anterior = 12
        ano_anterior = ano_atual - 1
    else:
        mes_anterior = mes_atual - 1
        ano_anterior = ano_atual

    total_atual = 0.0
    total_anterior = 0.0

    if not isinstance(historico_str, str):
        return 0.0, 0.0

    linhas = historico_str.split('\n')
    for linha in linhas:
        if "Compra" in linha:
            try:
                partes = linha.split('|')
                data_str = partes[0].strip()
                desc_str = partes[1].strip()
                
                valor_str = desc_str.replace("Compra", "").replace("€", "").strip()
                valor = float(valor_str)
                
                try:
                    dt = datetime.strptime(data_str, '%d/%m/%Y %H:%M')
                except ValueError:
                    dt_temp = datetime.strptime(data_str, '%d/%m %H:%M')
                    dt = dt_temp.replace(year=ano_atual)

                if dt.month == mes_atual and dt.year == ano_atual:
                    total_atual += valor
                elif dt.month == mes_anterior and dt.year == ano_anterior:
                    total_anterior += valor
            except:
                continue
                
    return total_atual, total_anterior

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
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.header("🌭 Kão Kente")

    st.divider()
    
    pagina_selecionada = st.radio("Navegação", [
        "🏆 Programa de Pontos", 
        "🛵 Encomendar Online", 
        "🔐 Área de Gestão"
    ])

df = load_data()

# =========================================================
# PÁGINA 1: PROGRAMA DE PONTOS (VISÃO CLIENTE)
# =========================================================
if pagina_selecionada == "🏆 Programa de Pontos":
    st.title("🌭 Programa de Pontos Kão Kente")

    # BOTÃO EM DESTAQUE PARA ENCOMENDAR (NOVO)
    st.write("") # Espaçamento
    botao_laranja("🛵 Encomendar Online Agora!", URL_ENCOMENDAS)
    st.write("") # Espaçamento

    if 'user_logado' not in st.session_state:
        st.session_state['user_logado'] = None

    tab_cliente, tab_sobre = st.tabs(["👤 A minha Conta", "ℹ️ Sobre o Programa"])

    with tab_cliente:
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

        else:
            user = st.session_state['user_logado']
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
            items_list = list(PREMIOS_PONTOS.items())
            
            for i, (premio, custo_pts) in enumerate(items_list):
                saldo = user['Pontos']
                percentagem = min(saldo / custo_pts, 1.0)
                pode_comprar = saldo >= custo_pts
                
                col_atual = col_grid1 if i % 2 == 0 else col_grid2
                with col_atual:
                    with st.container(border=True):
                        st.markdown(f"**{premio}**")
                        st.caption(f"Custo: {custo_pts} pts")
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
    
    st.info("Faz o teu pedido aqui em baixo:")
    
    # BOTÃO MOVIDO PARA CIMA E COM A COR LARANJA
    botao_laranja("Abrir Ementa em Nova Janela", URL_ENCOMENDAS)
    
    try:
        components.iframe(URL_ENCOMENDAS, height=800, scrolling=True)
    except:
        st.error("Erro ao carregar menu.")

# =========================================================
# PÁGINA 3: ÁREA DE GESTÃO (ADMIN)
# =========================================================
elif pagina_selecionada == "🔐 Área de Gestão":
    st.title("🔐 Gestão Kão Kente")
    
    senha_input = st.text_input("Insira a Password de Admin", type="password")
    
    if senha_input == st.secrets.get("admin_password", "kaokente123"):
        st.divider()
        
        col_search, col_info = st.columns([2, 1])
        with col_search:
            filtro_nome = st.text_input("🔍 Pesquisar Cliente (Nome ou Telemóvel):")
        
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
            sel_cliente = st.selectbox("Selecionar Cliente:", opcoes_filtradas, 
                                     format_func=lambda x: f"{df[df['Telemovel']==x]['Nome'].values[0]} ({x})")
        else:
            st.warning("Nenhum cliente encontrado.")

        # MOSTRAR DADOS E MÉTRICAS MENSAIS
        if sel_cliente:
            dados_cli = df[df['Telemovel'] == sel_cliente].iloc[0]
            gasto_atual, gasto_anterior = calcular_metricas_mensais(dados_cli['Historico'])
            
            with col_info:
                st.success(f"**{dados_cli['Nome']}**")
                st.caption(f"Tipo: {dados_cli['Tipo']}")
                m1, m2, m3 = st.columns(3)
                m1.metric("Saldo Pontos", f"{dados_cli['Pontos']}")
                m2.metric("Gasto Mês Atual", f"{gasto_atual:.1f}€")
                m3.metric("Gasto Mês Anterior", f"{gasto_anterior:.1f}€")

        st.markdown("---")

        tab_lanc, tab_resg, tab_cri, tab_edit, tab_bd = st.tabs(["💰 Lançar", "🎁 Resgatar", "🆕 Criar", "✏️ Editar/Apagar", "📊 Ver Tudo"])

        with tab_lanc:
            if sel_cliente:
                val_eur = st.number_input("Valor da Venda (€)", min_value=0.0, step=0.5)
                pts_ganhar = calcular_pontos_ganhos(val_eur, dados_cli['Tipo'])
                st.write(f"Vai ganhar: **{pts_ganhar}** pontos (Base: {int(val_eur)}€)")
                
                if st.button("Confirmar Lançamento"):
                    idx = df[df['Telemovel'] == sel_cliente].index[0]
                    df.at[idx, 'Pontos'] += pts_ganhar
                    log = f"{datetime.now().strftime('%d/%m/%Y %H:%M')} | Compra {val_eur}€ | +{pts_ganhar} pts\n"
                    df.at[idx, 'Historico'] = log + str(df.at[idx, 'Historico'])
                    save_data(df)
                    st.success("Pontos adicionados!")
            else:
                st.info("Selecione um cliente.")

        with tab_resg:
            if sel_cliente:
                premio = st.selectbox("Escolher Oferta", list(PREMIOS_PONTOS.keys()))
                custo = PREMIOS_PONTOS[premio]
                st.write(f"Custo: **{custo}** pts")
                if st.button("Confirmar Resgate"):
                    if dados_cli['Pontos'] >= custo:
                        idx = df[df['Telemovel'] == sel_cliente].index[0]
                        df.at[idx, 'Pontos'] -= custo
                        log = f"{datetime.now().strftime('%d/%m/%Y %H:%M')} | Resgate {premio} | -{custo} pts\n"
                        df.at[idx, 'Historico'] = log + str(df.at[idx, 'Historico'])
                        save_data(df)
                        st.balloons()
                        st.success("Oferta entregue!")
                    else:
                        st.error("Saldo insuficiente.")
            else:
                st.info("Selecione um cliente.")

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
        
        with tab_edit:
            if sel_cliente:
                st.subheader(f"Editar dados de {dados_cli['Nome']}")
                with st.form("form_edicao"):
                    edit_nome = st.text_input("Nome", value=dados_cli['Nome'])
                    idx_tipo = 0 if dados_cli['Tipo'] == "Normal" else 1
                    edit_tipo = st.selectbox("Tipo", ["Normal", "Estudante"], index=idx_tipo)
                    edit_pass = st.text_input("Password", value=dados_cli['Password'])
                    edit_pontos = st.number_input("Correção Manual de Pontos", value=int(dados_cli['Pontos']), step=1)
                    
                    col_save, col_del = st.columns([1, 4])
                    with col_save:
                        submit_edit = st.form_submit_button("💾 Guardar")
                    
                    if submit_edit:
                        idx = df[df['Telemovel'] == sel_cliente].index[0]
                        df.at[idx, 'Nome'] = edit_nome
                        df.at[idx, 'Tipo'] = edit_tipo
                        df.at[idx, 'Password'] = edit_pass
                        df.at[idx, 'Pontos'] = edit_pontos
                        save_data(df)
                        st.success("Dados atualizados!")
                
                st.divider()
                with st.expander("Apagar Cliente"):
                    st.warning("Ação irreversível.")
                    if st.button("Sim, APAGAR Cliente"):
                        idx = df[df['Telemovel'] == sel_cliente].index[0]
                        df = df.drop(idx)
                        save_data(df)
                        st.error("Apagado.")
                        st.rerun()
            else:
                st.info("Selecione um cliente.")

        with tab_bd:
            st.dataframe(df)

    elif senha_input:
        st.error("Password errada.")