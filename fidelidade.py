import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURAÇÃO E DADOS ---
# Nome do ficheiro onde guardamos os dados (funciona como base de dados simples)
DATA_FILE = 'kaokente_data.csv'

# Ementa de Prémios (Exemplos baseados no teu restaurante)
PREMIOS = {
    "Bebida de Cápsula": 50,
    "Dose de Batatas Fritas": 100,
    "Kebab em Pão": 250,
    "Menu Hambúrguer Completo": 400,
    "Francesinha Especial": 600
}

# Função para carregar dados
def load_data():
    if not os.path.exists(DATA_FILE):
        # Cria um ficheiro vazio se não existir
        df = pd.DataFrame(columns=["Telemovel", "Nome", "Pontos", "Historico"])
        df.to_csv(DATA_FILE, index=False)
        return df
    return pd.read_csv(DATA_FILE)

# Função para salvar dados
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Função para registar transação no histórico
def log_transaction(df, telemovel, desc, valor):
    idx = df[df['Telemovel'] == telemovel].index[0]
    hist_atual = str(df.at[idx, 'Historico'])
    if hist_atual == "nan": hist_atual = ""
    
    data_hoje = datetime.now().strftime("%d/%m %H:%M")
    novo_log = f"{data_hoje} | {desc} | {valor} pts"
    
    # Adiciona ao histórico (separado por quebra de linha)
    df.at[idx, 'Historico'] = novo_log + "\n" + hist_atual
    return df

# --- INTERFACE DA APLICAÇÃO ---
st.set_page_config(page_title="Kão Kente Fidelidade", page_icon="🌭")

# Título e Logo (Simulado com texto)
st.title("🌭 Kão Kente - Clube de Pontos (Google)")

# Menu lateral para escolher o modo (Cliente ou Dono)
menu = st.sidebar.selectbox("Escolha o Acesso", ["Área do Cliente", "Área do Dono (Admin)"])

df = load_data()

# --- ÁREA DO CLIENTE ---
if menu == "Área do Cliente":
    st.header("Bem-vindo Cliente!")
    phone_input = st.text_input("Insira o seu nº de telemóvel para entrar:", max_chars=9)
    
    if st.button("Ver Meus Pontos"):
        user_data = df[df['Telemovel'] == int(phone_input)] if phone_input.isdigit() else pd.DataFrame()
        
        if not user_data.empty:
            pontos = user_data.iloc[0]['Pontos']
            nome = user_data.iloc[0]['Nome']
            historico = user_data.iloc[0]['Historico']
            
            st.success(f"Olá, {nome}!")
            
            # Mostrar saldo em destaque
            st.metric(label="O teu Saldo de Pontos", value=f"{pontos} ⭐")
            
            # Barra de progresso para o próximo prémio grande
            st.write("Progresso para Menu Hambúrguer (400 pts):")
            progresso = min(pontos / 400, 1.0)
            st.progress(progresso)
            
            # Tabela de Prémios
            st.subheader("🎁 O que podes trocar:")
            for premio, custo in PREMIOS.items():
                if pontos >= custo:
                    st.write(f"✅ **{premio}** ({custo} pts) - Podes pedir!")
                else:
                    st.write(f"🔒 {premio} ({custo} pts) - Faltam {custo - pontos}")
            
            st.info("ℹ️ Para trocar pontos, mostra este ecrã ao balcão!")
            
            # Histórico
            with st.expander("Ver meu histórico de movimentos"):
                st.text(historico)
                
        else:
            st.error("Cliente não encontrado. Peça ao staff para criar conta na sua próxima encomenda!")

# --- ÁREA DO DONO (ADMIN) ---
elif menu == "Área do Dono (Admin)":
    st.header("Gestão Kão Kente")
    password = st.sidebar.text_input("Password Admin", type="password")
    
    if password == st.secrets["admin_password"]:
        
        tab1, tab2, tab3 = st.tabs(["Lançar Pontos", "Resgatar Oferta", "Criar Cliente"])
        
        # ABA 1: LANÇAR PONTOS (Quando o cliente gasta €)
        with tab1:
            st.subheader("Adicionar Pontos (Venda)")
            clientes_list = df['Telemovel'].tolist()
            cliente_sel = st.selectbox("Selecione o Cliente", clientes_list, format_func=lambda x: f"{x} - {df[df['Telemovel']==x]['Nome'].values[0]}")
            
            # Regra simples: 1 Euro = 10 Pontos (ajustável)
            valor_gasto = st.number_input("Valor da conta (€):", min_value=0.0, step=0.5)
            pontos_a_somar = int(valor_gasto * 10)
            
            if st.button("Lançar Pontos"):
                idx = df[df['Telemovel'] == cliente_sel].index[0]
                df.at[idx, 'Pontos'] += pontos_a_somar
                df = log_transaction(df, cliente_sel, "Compra Loja/GloriaFood", f"+{pontos_a_somar}")
                save_data(df)
                st.success(f"Adicionados {pontos_a_somar} pontos ao cliente!")

        # ABA 2: RESGATAR (Quando o cliente troca pontos por comida)
        with tab2:
            st.subheader("Abater Pontos (Oferta)")
            cliente_redem = st.selectbox("Cliente a resgatar", clientes_list, key="redeem")
            
            # Mostra saldo atual
            if cliente_redem:
                saldo_atual = df[df['Telemovel'] == cliente_redem]['Pontos'].values[0]
                st.write(f"Saldo atual: **{saldo_atual}** pts")
            
            premio_escolhido = st.selectbox("Prémio a oferecer", list(PREMIOS.keys()))
            custo_premio = PREMIOS[premio_escolhido]
            
            if st.button("Confirmar Troca"):
                if saldo_atual >= custo_premio:
                    idx = df[df['Telemovel'] == cliente_redem].index[0]
                    df.at[idx, 'Pontos'] -= custo_premio
                    df = log_transaction(df, cliente_redem, f"Resgate: {premio_escolhido}", f"-{custo_premio}")
                    save_data(df)
                    st.balloons()
                    st.success("Oferta redimida com sucesso!")
                else:
                    st.error("Saldo insuficiente!")

        # ABA 3: CRIAR NOVO CLIENTE
        with tab3:
            st.subheader("Novo Registo")
            novo_nome = st.text_input("Nome do Cliente")
            novo_tel = st.text_input("Telemóvel", max_chars=9)
            
            if st.button("Registar Cliente"):
                if novo_tel and novo_nome:
                    if int(novo_tel) in df['Telemovel'].values:
                        st.warning("Este número já existe!")
                    else:
                        novo_cliente = pd.DataFrame({"Telemovel": [int(novo_tel)], "Nome": [novo_nome], "Pontos": [0], "Historico": [""]})
                        df = pd.concat([df, novo_cliente], ignore_index=True)
                        save_data(df)
                        st.success("Cliente criado!")
                else:
                    st.warning("Preencha todos os dados.")
        
        st.divider()
        st.write("📊 **Lista Geral de Clientes**")
        st.dataframe(df)
        
    else:
        st.warning("Insira a password de administrador.")