import streamlit as st
from datetime import datetime
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Rectificar Notas", page_icon="✏️", layout="wide")

st.title("✏️ Rectificación y Edición")
st.markdown("Utiliza los filtros para encontrar al estudiante.")

# --- 1. BUSCADOR AVANZADO ---
# Cargamos el directorio completo (esto es rápido)
if "df_directorio" not in st.session_state:
    st.session_state.df_directorio = utils.obtener_directorio_completo()

# Botón para refrescar la lista (por si acabas de registrar a alguien)
if st.button("🔄 Actualizar Lista de Alumnos"):
    st.session_state.df_directorio = utils.obtener_directorio_completo()

df = st.session_state.df_directorio

if not df.empty:
    # FILTROS VISUALES
    st.markdown("### 🔍 Buscar por:")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        f_nombre = st.text_input("Apellidos o Nombres:", placeholder="Ej: Perez").upper()
    with col_f2:
        lista_coles = ["Todos"] + sorted(df["Colegio"].unique().tolist())
        f_cole = st.selectbox("Colegio:", lista_coles)
    with col_f3:
        lista_grados = ["Todos"] + sorted(df["Grado"].unique().tolist())
        f_grado = st.selectbox("Grado:", lista_grados)

    # APLICAR FILTROS (Lógica de Pandas)
    df_filtrado = df.copy()
    
    if f_nombre:
        # Busca si el texto está en el nombre (ignora mayúsculas/minúsculas)
        df_filtrado = df_filtrado[df_filtrado["Nombre Completo"].str.contains(f_nombre, case=False, na=False)]
    
    if f_cole != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Colegio"] == f_cole]
        
    if f_grado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Grado"] == f_grado]

    # MOSTRAR RESULTADOS
    st.divider()
    
    if df_filtrado.empty:
        st.warning("No se encontraron alumnos con esos filtros.")
        st.session_state.alumno_edit_dni = None
    else:
        st.success(f"Se encontraron {len(df_filtrado)} coincidencias.")
        
        # Selector final
        # Creamos una etiqueta amigable: "PEREZ, JUAN (San Luis - 5to)"
        opciones_visuales = df_filtrado.apply(
            lambda x: f"{x['Nombre Completo']} | {x['Colegio']} ({x['Grado']}) - DNI:{x['DNI']}", axis=1
        ).tolist()
        
        seleccion = st.selectbox("👇 Selecciona al alumno a editar:", opciones_visuales)
        
        # Extraer DNI de la selección
        dni_seleccionado = seleccion.split("DNI:")[1]
        
        if st.button("✏️ EDITAR ESTE ALUMNO"):
            st.session_state.alumno_edit_dni = dni_seleccionado
            st.rerun()

else:
    st.info("No hay alumnos registrados en el sistema.")

# --- 2. FORMULARIO DE EDICIÓN (Se abre al seleccionar) ---
if st.session_state.get("alumno_edit_dni"):
    dni_edit = st.session_state.alumno_edit_dni
    
    # Buscamos los datos COMPLETOS en Firebase
    data_full = utils.obtener_alumno_por_dni(dni_edit)
    
    if data_full:
        alum = data_full["alumno"]
        resps_guardadas = data_full["examen"]["respuestas"]
        hora_guardada = data_full["info_registro"].get("hora_entrega", "10:00")

        st.markdown("---")
        st.markdown(f"### 📝 Editando a: {alum['nombres']}")
        
        with st.form("form_edicion"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.text_input("DNI (No editable)", value=alum['dni'], disabled=True)
                # Recuperamos el índice de la categoría actual
                idx_cat = ["A", "B", "C"].index(alum['categoria']) if alum['categoria'] in ["A", "B", "C"] else 0
                nueva_cat = st.selectbox("Categoría", ["A", "B", "C"], index=idx_cat)
                
            with c2:
                # Separamos nombre para editar si es posible, si no, todo junto
                nuevos_nombres = st.text_input("Apellidos y Nombres", value=alum['nombres'])
                nuevo_colegio = st.text_input("Colegio", value=alum['colegio'])
                
            with c3:
                nuevo_grado = st.text_input("Grado", value=alum['grado'])
                try:
                    hora_obj = datetime.strptime(hora_guardada, "%H:%M")
                except:
                    hora_obj = datetime.strptime("10:00", "%H:%M")
                nueva_hora = st.time_input("Hora Entrega", value=hora_obj)

            st.subheader("Corregir Respuestas")
            st.caption("Modifica solo lo necesario.")
            
            nuevas_respuestas = {}
            # Grid de Respuestas
            for fila in range(0, 20, 5):
                cols = st.columns(5)
                for i in range(5):
                    num = str(fila + i + 1)
                    val_actual = resps_guardadas.get(num, "-")
                    try:
                        idx_resp = ["-", "A", "B", "C", "D", "E"].index(val_actual)
                    except:
                        idx_resp = 0
                    
                    with cols[i]:
                        nuevas_respuestas[num] = st.selectbox(
                            f"P{num}", ["-", "A", "B", "C", "D", "E"], 
                            index=idx_resp, 
                            key=f"edit_p{num}",
                            label_visibility="collapsed"
                        )
                        st.caption(f"**P{num}**")

            st.markdown("---")
            if st.form_submit_button("💾 GUARDAR CAMBIOS Y RECALCULAR", type="primary", use_container_width=True):
                
                # 1. Buscamos patrón correcto
                patron = utils.obtener_patron_respuestas(nueva_cat)
                
                if not patron:
                    st.error(f"⚠️ No hay clave de respuestas para Categoría {nueva_cat}.")
                else:
                    # 2. Recalcular Nota
                    r_limpias = {k: (v if v != "-" else "") for k, v in nuevas_respuestas.items()}
                    ptj, ok, bad, blk, val = utils.calcular_nota(r_limpias, patron)
                    
                    # 3. Empaquetar
                    datos_update = {
                        "alumno": {
                            "dni": alum['dni'],
                            "nombres": nuevos_nombres.upper(),
                            "colegio": nuevo_colegio.upper(),
                            "categoria": nueva_cat,
                            "grado": nuevo_grado
                        },
                        "examen": {"respuestas": r_limpias, "validacion": val},
                        "metricas": {"total_puntos": ptj, "correctas": ok, "incorrectas": bad, "en_blanco": blk},
                        "info_registro": {
                            "fecha_carga": datetime.now(),
                            "hora_entrega": nueva_hora.strftime("%H:%M"),
                            "digitador": "Rectificación"
                        }
                    }
                    
                    # 4. Guardar
                    if utils.guardar_alumno(datos_update):
                        st.success(f"✅ ¡Datos actualizados correctamente! Nueva Nota: {ptj}")
                        # Limpiamos caché para que el buscador se actualice
                        st.session_state.df_directorio = utils.obtener_directorio_completo()
                        st.session_state.alumno_edit_dni = None # Cerrar editor