import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from fpdf import FPDF

# --- CONEXIÓN ---
@st.cache_resource
def conectar_firebase():
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate("CERM_Backend/serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
        except:
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
    return firestore.client()

db = conectar_firebase()

# --- GESTIÓN DE RESPUESTAS ---
def guardar_patron_respuestas(categoria, respuestas_dict):
    try:
        db.collection("configuracion").document("respuestas").set({
            f"cat_{categoria}": respuestas_dict
        }, merge=True)
        return True
    except Exception as e:
        return False

def obtener_patron_respuestas(categoria):
    try:
        doc = db.collection("configuracion").document("respuestas").get()
        if doc.exists:
            return doc.to_dict().get(f"cat_{categoria}", {})
        return {}
    except:
        return {}

# --- LÓGICA DE ALUMNOS ---
def obtener_alumno_por_dni(dni):
    """Busca un alumno para editarlo"""
    try:
        doc = db.collection("participantes").document(dni).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except:
        return None

def calcular_nota(respuestas_usuario, patron_dict):
    puntaje = 0
    correctas = 0
    incorrectas = 0
    blanco = 0
    detalle_validacion = {}

    if not patron_dict: return -1, 0, 0, 0, {}

    for i in range(1, 21):
        num = str(i)
        marca = respuestas_usuario.get(num, "")
        correcta = patron_dict.get(num)

        if marca == "" or marca == "-":
            blanco += 1
            detalle_validacion[num] = "BLANCO"
        elif marca == correcta:
            puntaje += 5
            correctas += 1
            detalle_validacion[num] = "CORRECTA"
        else:
            puntaje -= 2
            incorrectas += 1
            detalle_validacion[num] = "INCORRECTA"
            
    if puntaje < 0: puntaje = 0
    return puntaje, correctas, incorrectas, blanco, detalle_validacion

def guardar_alumno(datos):
    try:
        db.collection("participantes").document(datos["alumno"]["dni"]).set(datos)
        return True
    except:
        return False

def obtener_data(categoria):
    docs = db.collection("participantes").where("alumno.categoria", "==", categoria).stream()
    lista = []
    for doc in docs:
        d = doc.to_dict()
        lista.append({
            "DNI": d["alumno"].get("dni"),
            "Estudiante": d["alumno"].get("nombres"),
            "Colegio": d["alumno"].get("colegio"),
            "Grado": d["alumno"].get("grado"),
            "Puntaje": d["metricas"].get("total_puntos", 0),
            "Hora": d["info_registro"].get("hora_entrega", "00:00"),
            "Correctas": d["metricas"].get("correctas", 0),
            "Validacion": d.get("examen", {}).get("validacion", {}),
            "Respuestas": d.get("examen", {}).get("respuestas", {})
        })
    return pd.DataFrame(lista)

# --- PDF (Con Colegio y Hora) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Reporte Oficial de Resultados - CERM 2025', 0, 1, 'C')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generar_pdf_bytes(df_top, categoria):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"CUADRO DE MERITO - CATEGORIA {categoria}", 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_fill_color(220, 230, 255)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(10, 8, "#", 1, 0, 'C', 1)
    pdf.cell(85, 8, "Estudiante", 1, 0, 'L', 1)
    pdf.cell(55, 8, "Colegio", 1, 0, 'L', 1)
    pdf.cell(20, 8, "Hora", 1, 0, 'C', 1)
    pdf.cell(15, 8, "Nota", 1, 1, 'C', 1)
    
    pdf.set_font('Arial', '', 8)
    for i, row in df_top.iterrows():
        est = row['Estudiante'][:40].encode('latin-1', 'replace').decode('latin-1')
        cole = row['Colegio'][:25].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(10, 8, str(i+1), 1, 0, 'C')
        pdf.cell(85, 8, est, 1, 0, 'L')
        pdf.cell(55, 8, cole, 1, 0, 'L')
        pdf.cell(20, 8, str(row['Hora']), 1, 0, 'C')
        pdf.cell(15, 8, str(row['Puntaje']), 1, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')
# ... (MANTEN TUS OTRAS FUNCIONES ARRIBA: conectar, calcular_nota, guardar...) ...

def obtener_directorio_completo():
    """
    Descarga una lista ligera de TODOS los alumnos para el buscador.
    """
    try:
        # Traemos solo los campos necesarios para buscar (ahorra datos)
        docs = db.collection("participantes").stream()
        lista = []
        for doc in docs:
            d = doc.to_dict().get("alumno", {})
            lista.append({
                "DNI": d.get("dni"),
                "Nombre Completo": d.get("nombres"), # Apellidos, Nombres
                "Colegio": d.get("colegio"),
                "Grado": d.get("grado"),
                "Categoría": d.get("categoria")
            })
        return pd.DataFrame(lista)
    except Exception as e:
        return pd.DataFrame()