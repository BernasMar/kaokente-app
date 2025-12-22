import streamlit as st
import pandas as pd
import math
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA (LAYOUT WIDE PARA O IFRAME FICAR MELHOR) ---
st.set_page_config(page_title="Kão Kente Rewards", page_icon="🌭", layout="wide")

# --- LIGAÇÃO AO GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- DEFINIÇÃO DE PRÉMIOS E PREÇOS (EM EUROS) ---
# O sistema vai converter isto para pontos automaticamente
PREMIOS_PRECO = {
    "Bebida de Cápsula": 0.80,
    "Dose de Batatas Fritas": 1.50,
    "Kebab em Pão": 4.50,
    "Menu Hambúrguer Completo": 6.50,
    "Francesinha Especial": 9.50
}

# --- FUNÇÕES DE LÓGICA DE NEGÓCIO ---

def calcular_custo_pontos(preco_euro):
    """
    Regra: Arredonda o preço à centena mais alta (unidade de euro superior) e multiplica por 100.
    Ex: 4.80 -> Teto é 5 -> 500 pontos.
    """
    return math.ceil(preco_euro) * 100

def calcular_pontos_ganhos(valor_gasto, tipo_cliente):
    """
    Regra: 
    - Estudante: 7.5% (7.5 pts por euro)
    - Normal: 5% (5 pts por euro)
    """
    multiplicador = 7.5 if tipo_cliente == "Estudante" else 5.0
    return int(valor_gasto * multiplicador)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=["Telemovel", "Nome", "Pontos", "Historico", "Password", "Tipo"])
        
        # Conversão e limpeza de tipos
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

# --- BARRA LATERAL (EMENTA ONLINE) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=100) # Exemplo de logo
    st.title("Kão Kente")
    st.write("📍 O melhor Kebab da cidade!")
    st.divider()
    
    st.subheader("📲 Encomendar Online")
    st.write("Não queres esperar? Pede aqui:")
    
    # URL da GloriaFood
    gloria_url = "https://www.foodbooking.com/ordering/restaurant/menu?company_uid=e92e9690-8f0b-45e2-acca-6671a872abb9&restaurant_uid=5e09158f-4dc1-4b17-b9d5-687ca8510db8&facebook=true"
    
    # Tentativa de Iframe (Mirror)
    # Nota: Alguns sites bloqueiam iframes. Se ficar branco, usamos o botão.
    try:
        components.iframe(gloria_url, height=600, scrolling=True)
    except:
        st.write("Visualização indisponível aqui.")
        
    st.link_button("Abrir Ementa em Ecrã Cheio", gloria_url)

# --- CORPO PRINCIPAL ---
st.title("🌭 Kão Kente Rewards")

df = load_data()

# Variável de estado para controlar se o utilizador fez login
if 'user_logado' not in st.session_state:
    st.session_state['user_logado'] = None

# --- SEPARADORES PRINCIPAIS ---
# Usamos Tabs para separar visualmente, mas o Admin está escondido noutro sítio
tab_cliente, tab_sobre = st.tabs(["👤 A minha Conta", "ℹ️ Sobre o Programa"])

with tab_cliente:
    # SE NÃO ESTIVER LOGADO
    if st.session_state['user_logado'] is None:
        st.subheader("Login de Cliente")
        col1, col2 = st.columns(2)
        with col1:
            login_tel = st.text_input("Telemóvel", max_chars=9)
        with col2:
            login_pass = st.text_input("Password", type="password")
        
        if st.button("Entrar"):
            if login_tel.isdigit():
                # Procura cliente
                user = df[(df['Telemovel'] == int(login_tel)) & (df['Password'] == login_pass)]
                if not user.empty:
                    st.session_state['user_logado'] = user.iloc[0]
                    st.success("Login efetuado!")
                    st.rerun()
                else:
                    st.error("Dados incorretos ou conta inexistente.")
            else:
                st.error("Número inválido.")

    # SE JÁ ESTIVER LOGADO
    else:
        user = st.session_state['user_logado']
        # Atualiza os dados do user com o que está na BD mais recente
        user = df[df['Telemovel'] == user['Telemovel']].iloc[0]
        
        # Cabeçalho do Cliente
        st.info(f"Bem-vindo, **{user['Nome']}** ({user['Tipo']})")
        
        col_pts, col_logout = st.columns([3, 1])
        with col_pts:
            st.metric("O teu Saldo", f"{user['Pontos']} Pontos")
        with col_logout:
            if st.button("Sair"):
                st.session_state['user_logado'] = None
                st.rerun()

        st.divider()
        st.subheader("🎁 O que podes pedir?")
        
        # Lista de Prémios com Barras de Progresso
        for premio, preco_eur in PREMIOS_PRECO.items():
            custo_pts = calcular_custo_pontos(preco_eur)
            saldo = user['Pontos']
            
            # Cálculo da percentagem (máximo 100%)
            percentagem = min(saldo / custo_pts, 1.0)
            pode_comprar = saldo >= custo_pts
            
            # Layout do Cartão de Prémio
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1:
                    st.markdown(f"**{premio}**")
                    st.caption(f"Preço Menu: {preco_eur}0€")
                with c2:
                    st.progress(percentagem, text=f"{saldo}/{custo_pts} pts")
                with c3:
                    if pode_comprar:
                        st.markdown("✅ **Podes!**")
                    else:
                        st.markdown("❌ Ainda não")

        with st.expander("Ver meu histórico"):
            st.text(user['Historico'])

with tab_sobre:
    st.markdown("""
    ### Como funciona?
    1. Fazes o teu pedido (aqui ou no restaurante).
    2. Ganhas pontos por cada Euro gasto.
    3. **Estudantes:** Ganham 7.5 pts por cada 1€.
    4. **Não Estudantes:** Ganham 5 pts por cada 1€.
    
    ### Como descontar?
    Basta mostrares o teu saldo ao balcão na hora de pagar!
    """)

# --- ADMINISTRAÇÃO (RODAPÉ) ---
st.write("")
st.write("")
st.write("")
st.divider()

# Escondido num expander no fundo da página
with st.expander("🔐 Acesso Staff (Admin)"):
    senha_admin = st.text_input("Password Admin", type="password", key="admin_pass")
    
    # Valida senha (lê dos secrets ou usa padrão)
    if senha_admin == st.secrets.get("admin_password", "kaokente123"):
        st.success("Modo Admin Ativo")
        
        tab_add, tab_redeem, tab_new = st.tabs(["💰 Lançar Pontos", "🎁 Descontar Pontos", "🆕 Criar Cliente"])
        
        # ABA 1: LANÇAR PONTOS
        with tab_add:
            lista_clientes = df['Telemovel'].unique()
            sel_cliente = st.selectbox("Cliente", lista_clientes, format_func=lambda x: f"{x} - {df[df['Telemovel']==x]['Nome'].values[0]}")
            
            valor_eur = st.number_input("Valor da Conta (€)", min_value=0.0, step=0.5)
            
            if sel_cliente:
                # Determina se é estudante ou não
                dados_cli = df[df['Telemovel'] == sel_cliente].iloc[0]
                tipo_cli = dados_cli['Tipo']
                
                pontos_ganhar = calcular_pontos_ganhos(valor_eur, tipo_cli)
                
                st.write(f"Cliente **{tipo_cli}**. Vai ganhar: **{pontos_ganhar}** pontos.")
                
                if st.button("Lançar"):
                    idx = df[df['Telemovel'] == sel_cliente].index[0]
                    df.at[idx, 'Pontos'] += pontos_ganhar
                    
                    # Log
                    data_hoje = datetime.now().strftime("%d/%m %H:%M")
                    log = f"{data_hoje} | Compra {valor_eur}€ | +{pontos_ganhar} pts\n"
                    df.at[idx, 'Historico'] = log + str(df.at[idx, 'Historico'])
                    
                    save_data(df)
                    st.success("Pontos lançados!")

        # ABA 2: DESCONTAR
        with tab_redeem:
            sel_redem = st.selectbox("Cliente a Resgatar", lista_clientes, key="redeem_user")
            if sel_redem:
                dados_redem = df[df['Telemovel'] == sel_redem].iloc[0]
                saldo_atual = dados_redem['Pontos']
                st.metric("Saldo Atual", saldo_atual)
                
                # Escolher prémio
                premio_escolhido = st.selectbox("Oferta", list(PREMIOS_PRECO.keys()))
                custo = calcular_custo_pontos(PREMIOS_PRECO[premio_escolhido])
                
                st.write(f"Custo: **{custo}** pontos")
                
                if st.button("Confirmar Resgate"):
                    if saldo_atual >= custo:
                        idx = df[df['Telemovel'] == sel_redem].index[0]
                        df.at[idx, 'Pontos'] -= custo
                        
                        # Log
                        data_hoje = datetime.now().strftime("%d/%m %H:%M")
                        log = f"{data_hoje} | Resgate {premio_escolhido} | -{custo} pts\n"
                        df.at[idx, 'Historico'] = log + str(df.at[idx, 'Historico'])
                        
                        save_data(df)
                        st.balloons()
                        st.success("Resgatado!")
                    else:
                        st.error("Saldo insuficiente.")

        # ABA 3: CRIAR CLIENTE
        with tab_new:
            c_nome = st.text_input("Nome Cliente")
            c_tel = st.text_input("Telemóvel (Login)", max_chars=9)
            c_pass = st.text_input("Definir Password Inicial")
            c_tipo = st.selectbox("Tipo de Cliente", ["Normal", "Estudante"])
            
            if st.button("Registar Novo Cliente"):
                if c_tel and c_nome and c_pass:
                    if not df.empty and int(c_tel) in df['Telemovel'].values:
                        st.error("Número já existe.")
                    else:
                        novo = pd.DataFrame([{
                            "Telemovel": int(c_tel),
                            "Nome": c_nome,
                            "Pontos": 0,
                            "Historico": "",
                            "Password": c_pass,
                            "Tipo": c_tipo
                        }])
                        df = pd.concat([df, novo], ignore_index=True)
                        save_data(df)
                        st.success(f"Cliente {c_nome} criado como {c_tipo}!")
                else:
                    st.warning("Preenche tudo.")
            
        st.write("Base de Dados Completa:")
        st.dataframe(df)