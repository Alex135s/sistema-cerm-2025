import streamlit as st
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Configuración", page_icon="⚙️", layout="wide")
st.title("⚙️ Configuración y Auditoría de Claves")

col_form, col_view = st.columns([1, 1])

with col_form:
    st.subheader("📝 Ingresar Nueva Clave")
    cat_config = st.selectbox("Categoría:", ["A", "B", "C"])
    
    # Formulario con clear_on_submit=True (Punto 2: Limpieza automática)
    with st.form("form_patron", clear_on_submit=True):
        st.caption(f"Ingresa las respuestas para Categoría {cat_config}")
        
        resp_in = {}
        for fila in range(0, 20, 5):
            cols = st.columns(5)
            for i in range(5):
                num = str(fila + i + 1)
                with cols[i]:
                    # Index 0 es "A" por defecto
                    resp_in[num] = st.selectbox(f"P{num}", ["A", "B", "C", "D", "E"], key=f"k{num}")
        
        if st.form_submit_button("💾 GUARDAR CLAVE", type="primary"):
            if utils.guardar_patron_respuestas(cat_config, resp_in):
                st.success(f"Clave {cat_config} guardada.")
                st.rerun() # Recarga para actualizar la tabla de la derecha

with col_view:
    st.subheader("👁️ Historial de Claves (Validación)")
    # Punto 4: Ver historial de respuestas guardadas
    tabs = st.tabs(["Categoría A", "Categoría B", "Categoría C"])
    
    for i, cat in enumerate(["A", "B", "C"]):
        with tabs[i]:
            patron = utils.obtener_patron_respuestas(cat)
            if patron:
                # Convertir a DataFrame para ver bonito
                df_patron = pd.DataFrame(list(patron.items()), columns=["Pregunta", "Respuesta"])
                df_patron["Pregunta"] = df_patron["Pregunta"].astype(int)
                df_patron = df_patron.sort_values("Pregunta")
                
                # Mostrar en una tablita horizontal
                st.dataframe(df_patron.T, use_container_width=True) 
                st.success(f"✅ Clave cargada para Cat {cat}")
            else:
                st.warning(f"⚠️ No hay clave configurada para Cat {cat}")