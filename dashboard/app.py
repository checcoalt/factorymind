import streamlit as st
import pandas as pd
import streamlit_option_menu
from streamlit_option_menu import option_menu
from db_reader import fetch_mongo_data  # import dalla tua utility

# --- Sidebar ---
with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",
        options=["Home", "Chat", "Contact Us"],
        icons=["house", "chat-left-dots", "envelope"],
        menu_icon="clipboard2",
        default_index=0,
    )

# --- Home Page ---
if selected == "Home":
    st.header('FactoryMind Dashboard')

    # --- MongoDB Configuration ---
    DB_NAME = "FactoryMindDB"
    DATA_COLLECTION = "data"

    # Fetch data from MongoDB via db_reader.py
    try:
        data_chart_data = fetch_mongo_data(DB_NAME, DATA_COLLECTION)
    except Exception as e:
        st.error(f"Errore durante il fetch dei dati: {e}")
        data_chart_data = pd.DataFrame()

    if data_chart_data.empty:
        st.info(f"Nessun dato disponibile per '{DATA_COLLECTION}'.")
    else:
        # Seleziona i nomi delle colonne numeriche
        numeric_cols = data_chart_data.select_dtypes(include=['int64', 'float64']).columns
        
        if numeric_cols.empty:
            st.warning("Nessuna colonna numerica disponibile per i grafici")
        else:
            # Rimosso st.columns(4) per disporre i grafici in verticale
            
            # Limita i parametri da visualizzare ai primi 4
            parameters_to_plot = numeric_cols[:4]
            
            # Itera sui parametri e crea un line chart per ciascuno
            for param in parameters_to_plot:
                # Titolo e grafico si dispongono automaticamente in verticale
                st.subheader(f"📈 {param}")
                st.line_chart(data_chart_data[[param]])
            
            # Se ci sono più di 4 colonne numeriche, avvisa l'utente
            if len(numeric_cols) > 4:
                 st.caption(f"Visualizzate le prime 4 colonne numeriche. Rimanenti: {len(numeric_cols) - 4}")

            

# --- Chat Page ---
if selected == "Chat":
    st.subheader("💬 Chatbot")
    st.caption("🚀 A chatbot powered by FactoryMind Framework")
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

# --- Contact Page ---
if selected == "Contact Us":
    st.subheader(f"**You Have selected {selected}**")