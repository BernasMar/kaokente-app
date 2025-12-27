import streamlit as st
import pandas as pd
import math
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Programa de Pontos Kão Kente", page_icon="🌭", layout="wide")

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

# --- FUNÇÕES DE LÓGICA DE NEGÓCIO ---

def calcular_custo_pontos(preco_euro):
    # Arredonda o preço para o euro acima e multiplica por 100
    return math.ceil(preco_euro) * 100

def calcular_pontos_ganhos(valor_gasto, tipo_cliente):
    """
    Regra Nova: Ignora os cêntimos (usa apenas a parte inteira).
    Ex: 9.20€ ou 9.99€ contam como 9€.
    """
    valor_inteiro = int(valor_gasto) # Remove a parte decimal
    
    # Define multiplicador
    multiplicador = 7.5 if tipo_cliente == "Estudante" else 5.0
    
    return int(valor_inteiro * multiplicador)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=["Telemovel", "Nome", "Pontos", "Historico", "Password", "Tipo"])
        
        # Limpeza e conversão
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

# --- BARRA LATERAL (NAVEGAÇÃO E LOGO) ---
with st.sidebar:
    # Tenta carregar o logo se ele existir no GitHub/Pasta
    try:
        st.image("logo.png", use_container_width=True)
    except:
        # Se ainda não tiveres feito upload da imagem, mostra texto
        st.header("🌭 Kão Kente")

    st.divider()
    
    # Menu de Navegação para alternar entre Fidelidade e Encomendas
    pagina_selecionada = st.radio("Menu Principal", ["🏆 Programa de Pontos", "🛵 Encomendar Online"])

# =========================================================
# PÁGINA 1: ENCOMENDAR ONLINE (INTEGRADA)
# =========================================================
if pagina_selecionada == "🛵 Encomendar Online":
    st.title("🛵 Encomendar Online")
    
    gloria_url = "https://www.foodbooking.com/ordering/restaurant/menu?company_uid=e92e9690-8f0b-45e2-acca-6671a872abb9&restaurant_uid=5e09158f-4dc1-4b17-b9d5-687ca8510db8&facebook=true"
    
    st.info("Podes fazer o teu pedido diretamente aqui em baixo 👇")
    
    # Iframe ocupando a largura total
    try:
        components.iframe(gloria_url, height=800, scrolling=True)
    except:
        st.error("O teu navegador bloqueou a visualização. Usa o botão abaixo.")
    
    st.link_button("Abrir Ementa em Nova Janela ↗️", gloria_url, type="primary")

# =========================================================
# PÁGINA 2: PROGRAMA DE PONTOS (FIDELIDADE)
# =========================================================
elif pagina_selecionada == "🏆 Programa de Pontos":
    st.title("🌭 Programa de Pontos Kão Kente")

    df = load_data()

    if 'user_logado' not in st.session_state:
        st.session_state['user_logado'] = None

    # TABS DO PROGRAMA
    tab_cliente, tab_sobre = st.tabs(["👤 A minha Conta", "ℹ️ Sobre o Programa"])

    with tab_cliente:
        # LOGIN
        if st.session_state['user_logado'] is None:
            st.subheader("Login de Cliente")
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
                        st.success("Login efetuado!")
                        st.rerun()
                    else:
                        st.error("Dados incorretos.")
                else:
                    st.error("Número inválido.")

        # ÁREA PESSOAL
        else:
            user = st.session_state['user_logado']
            # Refresh dos dados
            user = df[df['Telemovel'] == user['Telemovel']].iloc[0]
            
            st.info(f"Bem-vindo, **{user['Nome']}** ({user['Tipo']})")
            
            c_pts, c_btn = st.columns([3, 1])
            with c_pts:
                st.metric("Saldo Disponível", f"{user['Pontos']} Pontos")
            with c_btn:
                if st.button("Sair"):
                    st.session_state['user_logado'] = None
                    st.rerun()

            st.divider()
            st.subheader("🎁 O que podes pedir?")
            
            col_grid1, col_grid2 = st.columns(2)
            
            # Mostra prémios
            items_list = list(PREMIOS_PRECO.items())
            
            for i, (premio, preco_eur) in enumerate(items_list):
                custo_pts = calcular_custo_pontos(preco_eur)
                saldo = user['Pontos']
                percentagem = min(saldo / custo_pts, 1.0)
                pode_comprar = saldo >= custo_pts
                
                # Alterna colunas para ficar grelha
                col_atual = col_grid1 if i % 2 == 0 else col_grid2
                
                with col_atual:
                    with st.container(border=True):
                        st.markdown(f"**{premio}**")
                        st.caption(f"Valor: {preco_eur:.2f}€ | Custo: {custo_pts} pts")
                        st.progress(percentagem)
                        if pode_comprar:
                            st.success("✅ Podes pedir!")
                        else:
                            st.write(f"🔒 Faltam {custo_pts - saldo}")

            with st.expander("Ver histórico de movimentos"):
                st.text(user['Historico'])

    with tab_sobre:
        st.markdown("""
        ### 🌭 Regras do Clube Kão Kente
        1. **Ganha Pontos:** Recebes pontos por cada Euro inteiro gasto.
           - Cêntimos não contam (ex: 9.90€ conta como 9€).
        2. **Tipos de Cliente:**
           - 🎓 **Estudantes:** Ganham 7.5 pontos por Euro.
           - 👤 **Normal:** Ganham 5 pontos por Euro.
        3. **Troca Pontos:**
           - Acumula e troca por comida grátis ao balcão!
        """)

    # --- ÁREA DE ADMINISTRAÇÃO ---
    st.divider()
    with st.expander("🔐 Acesso Staff (Admin)"):
        senha_admin = st.text_input("Password Admin", type="password", key="admin_pass")
        
        if senha_admin == st.secrets.get("admin_password", "kaokente123"):
            st.success("Modo Admin Ativo")
            
            tab_add, tab_redeem, tab_new = st.tabs(["💰 Lançar", "🎁 Resgatar", "🆕 Criar"])
            
            # FILTRO DE PESQUISA INTELIGENTE
            st.markdown("---")
            filtro_nome = st.text_input("🔍 Filtrar cliente por nome ou telemóvel:", placeholder="Ex: Bernardo")
            
            # Cria lista filtrada para facilitar a pesquisa
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

            # Função auxiliar para mostrar nome na caixa de seleção
            def formatar_cliente(tel):
                nome = df[df['Telemovel'] == tel]['Nome'].values[0]
                return f"{nome} ({tel})"

            # Se houver clientes compatíveis com a pesquisa
            sel_cliente = None
            if opcoes_filtradas:
                sel_cliente = st.selectbox("Selecione o Cliente:", opcoes_filtradas, format_func=formatar_cliente)
            else:
                st.warning("Nenhum cliente encontrado com esse nome.")

            st.markdown("---")

            # ABA 1: LANÇAR PONTOS
            with tab_add:
                if sel_cliente:
                    valor_eur = st.number_input("Valor Pago (€)", min_value=0.0, step=0.5)
                    
                    dados_cli = df[df['Telemovel'] == sel_cliente].iloc[0]
                    tipo_cli = dados_cli['Tipo']
                    
                    # Nova lógica (usa int() para ignorar decimais)
                    pontos_ganhar = calcular_pontos_ganhos(valor_eur, tipo_cli)
                    
                    st.info(f"Cliente **{tipo_cli}**. Compra de {int(valor_eur)}€ efetivos = **{pontos_ganhar}** pontos.")
                    
                    if st.button("Lançar Pontos"):
                        idx = df[df['Telemovel'] == sel_cliente].index[0]
                        df.at[idx, 'Pontos'] += pontos_ganhar
                        
                        log = f"{datetime.now().strftime('%d/%m %H:%M')} | Compra {valor_eur}€ | +{pontos_ganhar} pts\n"
                        df.at[idx, 'Historico'] = log + str(df.at[idx, 'Historico'])
                        
                        save_data(df)
                        st.success("Registado!")

            # ABA 2: RESGATAR
            with tab_redeem:
                if sel_cliente: # Usa a mesma seleção do filtro de cima
                    dados_redem = df[df['Telemovel'] == sel_cliente].iloc[0]
                    st.metric(f"Saldo de {dados_redem['Nome']}", dados_redem['Pontos'])
                    
                    premio = st.selectbox("Oferta a abater", list(PREMIOS_PRECO.keys()))
                    custo = calcular_custo_pontos(PREMIOS_PRECO[premio])
                    
                    if st.button("Confirmar Resgate"):
                        if dados_redem['Pontos'] >= custo:
                            idx = df[df['Telemovel'] == sel_cliente].index[0]
                            df.at[idx, 'Pontos'] -= custo
                            
                            log = f"{datetime.now().strftime('%d/%m %H:%M')} | Resgate {premio} | -{custo} pts\n"
                            df.at[idx, 'Historico'] = log + str(df.at[idx, 'Historico'])
                            
                            save_data(df)
                            st.balloons()
                            st.success("Oferta redimida!")
                        else:
                            st.error("Saldo insuficiente.")

            # ABA 3: CRIAR NOVO (Independente da pesquisa)
            with tab_new:
                st.write("Registar nova ficha de cliente")
                n_nome = st.text_input("Nome")
                n_tel = st.text_input("Telemóvel", max_chars=9)
                n_pass = st.text_input("Password Inicial")
                n_tipo = st.selectbox("Tipo", ["Normal", "Estudante"])
                
                if st.button("Criar Ficha"):
                    if n_tel and n_nome and n_pass:
                        if int(n_tel) in df['Telemovel'].values:
                            st.error("Número já existe!")
                        else:
                            novo = pd.DataFrame([{
                                "Telemovel": int(n_tel), "Nome": n_nome, "Pontos": 0,
                                "Historico": "", "Password": n_pass, "Tipo": n_tipo
                            }])
                            df = pd.concat([df, novo], ignore_index=True)
                            save_data(df)
                            st.success("Criado com sucesso!")