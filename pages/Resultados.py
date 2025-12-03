import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Resultados", page_icon="🏆", layout="wide")

st.title("🏆 Resultados y Premiación")

# Filtro global
cat_sel = st.selectbox("Selecciona Categoría:", ["A", "B", "C"])
df = utils.obtener_data(cat_sel)

if not df.empty:
    df = df.sort_values(by=["Puntaje", "Hora"], ascending=[False, True]).reset_index(drop=True)
    df.index += 1
    
    # --- PESTAÑAS: GENERAL vs PREMIACIÓN ---
    tab_general, tab_premiacion = st.tabs(["📊 Tabla General", "🏅 Premiación Oficial"])
    
    with tab_general:
        st.dataframe(df[["Estudiante", "Colegio", "Grado", "Puntaje", "Hora", "Correctas"]], use_container_width=True)
        
        if st.button("📥 Descargar PDF General"):
            pdf_bytes = utils.generar_pdf_bytes(df.head(20), cat_sel)
            st.download_button("Descargar", pdf_bytes, f"Top20_Cat{cat_sel}.pdf", "application/pdf")
            
    with tab_premiacion:
        st.subheader(f"🎖️ Cuadro de Honor - Categoría {cat_sel}")
        
        # 1. TOP 20
        col_top, col_cole = st.columns([2, 1])
        
        with col_top:
            st.markdown("### Top 20 Estudiantes")
            top20 = df.head(20)[["Estudiante", "Colegio", "Puntaje"]]
            st.table(top20) # st.table se ve más "impreso" y formal
            
        # 2. MEJOR INSTITUCIÓN (Punto 3)
        with col_cole:
            st.markdown("### 🏫 Mejor Institución")
            st.caption("Basado en la suma de puntajes de sus alumnos en esta categoría.")
            
            # Cálculo: Agrupar por colegio y sumar puntajes
            ranking_coles = df.groupby("Colegio")["Puntaje"].sum().reset_index()
            ranking_coles = ranking_coles.sort_values("Puntaje", ascending=False).reset_index(drop=True)
            ranking_coles.index += 1
            
            if not ranking_coles.empty:
                ganador = ranking_coles.iloc[0]
                st.success(f"🏆 1° Puesto: **{ganador['Colegio']}**")
                st.metric("Puntaje Acumulado", ganador["Puntaje"])
                
                st.markdown("#### Ranking de Colegios")
                st.dataframe(ranking_coles.head(5), hide_index=True)
            else:
                st.write("Sin datos.")

else:
    st.info("No hay datos registrados.")