import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Kão Kente Fidelidade", page_icon="🌭")

# --- LIGAÇÃO AO GOOGLE SHEETS ---
# ttl=0 é o segredo: obriga a ir buscar dados frescos ao Google SEMPRE que a app corre
conn = st.connection("gsheets", type=GSheetsConnection)

PREMIOS = {
    "Bebida de Cápsula": 50,
    "Dose de Batatas Fritas": 100,
    "Kebab em Pão": 250,
    "Menu Hambúrguer Completo": 400,
    "Francesinha Especial": 600
}

def load_data():
    try:
        # Lê a folha "Sheet1". Se der erro, devolve tabela vazia.
        df = conn.read(worksheet="Sheet1", ttl=0)
        
        # Se a folha vier vazia ou nula, cria a estrutura
        if df is None or df.empty:
            return pd.DataFrame(columns=["Telemovel", "Nome", "Pontos", "Historico"])
            
        # Limpeza de dados para garantir que números são números
        df['Telemovel'] = pd.to_numeric(df['Telemovel'], errors='coerce')
        df['Pontos'] = pd.to_numeric(df['Pontos'], errors='coerce').fillna(0).astype(int)
        df['Historico'] = df['Historico'].astype(str).replace('nan', '')
        # Remove linhas vazias que o Google às vezes cria
        df = df.dropna(subset=['Telemovel'])
        return df
    except Exception as e:
        st.error(f"⚠️ Erro ao LER dados: {e}")
        return pd.DataFrame(columns=["Telemovel", "Nome", "Pontos", "Historico"])

def save_data(df):
    try:
        # Escreve os dados na folha "Sheet1"
        conn.update(worksheet="Sheet1", data=df)
        # Limpa a cache para garantir que a próxima leitura vê estes dados novos
        st.cache_data.clear()
    except Exception as e:
        st.error(f"⚠️ Erro ao GRAVAR dados: {e}")

# --- TÍTULO E DEBUG ---
st.title("🌭 Kão Kente - Clube de Pontos (Google)")

# --- DEBUGGER (Só para tu veres se está a funcionar) ---
with st.expander("🔧 Área de Diagnóstico (Dono)"):
    st.write("Se clicares no botão abaixo, vamos tentar escrever uma linha de teste no Google Sheets.")
    if st.button("Testar Gravação no Google Sheets"):
        try:
            # Cria um dado de teste
            teste_df = pd.DataFrame([{
                "Telemovel": 123456789, 
                "Nome": "Teste Conexão", 
                "Pontos": 10, 
                "Historico": "Teste"
            }])
            save_data(teste_df)
            st.success("Comando de gravação enviado! Vai ver o teu Google Sheet agora.")
        except Exception as e:
            st.error(f"Erro no teste: {e}")

# --- LÓGICA DA APP ---
menu = st.sidebar.selectbox("Escolha o Acesso", ["Área do Cliente", "Área do Dono (Admin)"])
df = load_data()

# --- ÁREA DO CLIENTE ---
if menu == "Área do Cliente":
    st.header("Bem-vindo Cliente!")
    phone_input = st.text_input("Insira o seu nº de telemóvel:", max_chars=9)
    
    if st.button("Ver Pontos"):
        if phone_input.isdigit():
            user_data = df[df['Telemovel'] == int(phone_input)]
            if not user_data.empty:
                pontos = user_data.iloc[0]['Pontos']
                nome = user_data.iloc[0]['Nome']
                st.success(f"Olá, {nome}!")
                st.metric(label="Teus Pontos", value=f"{pontos} ⭐")
                st.text(f"Histórico:\n{user_data.iloc[0]['Historico']}")
            else:
                st.error("Cliente não encontrado.")

# --- ÁREA DO DONO ---
elif menu == "Área do Dono (Admin)":
    st.header("Gestão")
    # Tenta ler a password dos segredos, se não existir usa uma default para não crashar
    senha_secreta = st.secrets.get("admin_password", "admin")
    
    password = st.sidebar.text_input("Password", type="password")
    if password == senha_secreta:
        tab1, tab2 = st.tabs(["Criar Cliente", "Adicionar Pontos"])
        
        with tab1:
            st.subheader("Novo Cliente")
            novo_nome = st.text_input("Nome")
            novo_tel = st.text_input("Telemóvel", max_chars=9)
            if st.button("Registar"):
                if novo_tel and novo_nome:
                    # Verifica duplicados
                    if not df.empty and int(novo_tel) in df['Telemovel'].values:
                        st.warning("Já existe!")
                    else:
                        novo_cliente = pd.DataFrame([{
                            "Telemovel": int(novo_tel), 
                            "Nome": novo_nome, 
                            "Pontos": 0, 
                            "Historico": ""
                        }])
                        # Junta o novo cliente à tabela existente
                        df_final = pd.concat([df, novo_cliente], ignore_index=True)
                        save_data(df_final)
                        st.success("Gravado! Verifica o Google Sheets.")
                        st.rerun() # Atualiza a página
        
        with tab2:
            st.write("Lista Atual:")
            st.dataframe(df)