import streamlit as st

st.set_page_config(page_title="Inicio CERM 2025", page_icon="🏠", layout="centered")

st.title("🏠 Sistema de Gestión CERM 2025")
st.image("https://cdn-icons-png.flaticon.com/512/2910/2910768.png", width=100)

st.markdown("""
### Bienvenido al Panel de Control
Selecciona una opción en el menú de la izquierda:

* **📝 Registro:** Para digitar las fichas de los estudiantes.
* **🏆 Resultados:** Para ver el ranking en vivo y descargar reportes.

---
*Sistema desarrollado para la Dirección Regional de Educación.*
""")