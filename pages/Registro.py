import streamlit as st
from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Registro de Fichas", page_icon="📝", layout="wide")

# --- ESTILOS CSS PROFESIONALES ---
# Esto hace que los botones se centren y se vean como una ficha óptica
st.markdown("""
    <style>
    .stRadio [role=radiogroup] {
        justify-content: center;
        gap: 10px;
    }
    .bloque-pregunta {
        text-align: center;
        font-weight: bold;
        color: #555;
        margin-bottom: 5px;
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 2px;
    }
    div[data-testid="stContainer"] {
        background-color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📝 Módulo de Digitación Profesional")

# 1. CONFIGURACIÓN (Fuera del form para recarga en vivo)
col_cat, col_msg = st.columns([1, 4])
with col_cat:
    categoria = st.radio("Categoría:", ["A", "B", "C"], horizontal=True)

opciones_grado = []
if categoria == "A":
    opciones_grado = ["1ro Secundaria", "2do Secundaria"]
elif categoria == "B":
    opciones_grado = ["3ro Secundaria", "4to Secundaria"]
elif categoria == "C":
    opciones_grado = ["5to Secundaria"]

# --- FORMULARIO ---
with st.form("form_registro", clear_on_submit=True):
    
    # SECCIÓN 1: DATOS
    st.markdown("### 1. 👤 Datos del Estudiante")
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
        with c1:
            dni = st.text_input("DNI", max_chars=8, placeholder="Ej: 7216...")
        with c2:
            apellidos = st.text_input("Apellidos", placeholder="Paterno Materno")
        with c3:
            nombres = st.text_input("Nombres", placeholder="Nombres Completos")
        with c4:
            hora = st.time_input("Hora", value=datetime.strptime("10:00", "%H:%M"))

        c5, c6 = st.columns([2, 1])
        with c5:
            colegio = st.text_input("Institución Educativa")
        with c6:
            grado = st.selectbox("Grado Escolar", opciones_grado)

    st.write("") # Espacio

    # SECCIÓN 2: RESPUESTAS (ESTILO FICHA ÓPTICA)
    st.markdown("### 2. 📝 Hoja de Respuestas")
    
    respuestas_input = {}
    
    # Creamos 4 filas (Bloques)
    for bloque in range(0, 20, 5):
        # Usamos un contenedor con borde para cada fila de 5 preguntas
        with st.container(border=True):
            cols = st.columns(5)
            for i in range(5):
                num_preg = bloque + i + 1
                with cols[i]:
                    # Encabezado visual de la pregunta (Centrado)
                    st.markdown(f"<div class='bloque-pregunta'>PREGUNTA {num_preg}</div>", unsafe_allow_html=True)
                    
                    # Radio button limpio y centrado
                    respuestas_input[str(num_preg)] = st.radio(
                        f"p_{num_preg}", 
                        ["-", "A", "B", "C", "D", "E"], 
                        horizontal=True,
                        label_visibility="collapsed", # Ocultamos la etiqueta fea
                        key=f"rad_{num_preg}"
                    )
    
    st.markdown("---")
    
    # Botón grande y ancho
    col_izq, col_btn, col_der = st.columns([1, 2, 1])
    with col_btn:
        submitted = st.form_submit_button("💾  GUARDAR Y CALIFICAR  💾", type="primary", use_container_width=True)
    
    # LÓGICA DE GUARDADO
    if submitted:
        if not dni or not nombres:
            st.error("⚠️ Faltan datos obligatorios (DNI, Nombre).")
        else:
            patron_actual = utils.obtener_patron_respuestas(categoria)
            
            if not patron_actual:
                st.error(f"❌ ERROR: No hay clave de respuestas para Categoría {categoria}. Ve a Configuración.")
            else:
                respuestas_limpias = {k: (v if v != "-" else "") for k, v in respuestas_input.items()}
                ptj, ok, bad, blk, validacion = utils.calcular_nota(respuestas_limpias, patron_actual)
                
                datos = {
                    "alumno": {
                        "dni": dni,
                        "nombres": f"{apellidos}, {nombres}".upper(),
                        "nombres_raw": nombres,
                        "apellidos_raw": apellidos,
                        "colegio": colegio.upper(),
                        "categoria": categoria,
                        "grado": grado
                    },
                    "examen": {"respuestas": respuestas_limpias, "validacion": validacion},
                    "metricas": {"total_puntos": ptj, "correctas": ok, "incorrectas": bad, "en_blanco": blk},
                    "info_registro": {
                        "fecha_carga": datetime.now(),
                        "hora_entrega": hora.strftime("%H:%M"),
                        "digitador": "Web"
                    }
                }
                
                if utils.guardar_alumno(datos):
                    st.success(f"✅ ¡REGISTRADO! Nota: {ptj} | Aciertos: {ok}")
                    st.toast(f"Alumno {nombres} guardado correctamente.", icon="✅")