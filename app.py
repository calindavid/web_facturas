import streamlit as st
from typing import Optional
import datetime
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Gestió de facturació – Centres", page_icon="📊", layout="centered")

# --- Constants ---------------------------------------------------------------
CENTRES = {
    "Aspros": [
        "Centre Casa Nostra",
        "Centre Llars Urbanes",
        "Centre La Coma",
    ],
    "Terraferma": [],
}

EXCEL_PATH = Path("dades_facturacio.xlsx")

# --- Helpers -----------------------------------------------------------------
def init_state_key(key: str, value):
    if key not in st.session_state:
        st.session_state[key] = value

init_state_key("centre_gran", None)
init_state_key("subcentre", None)
init_state_key("data_treball", datetime.date.today())
init_state_key("hores_treballades", 0.0)

# --- Mostrar dades guardades -------------------------------------------------
st.title("📑 Selecció de centre i hores")

if EXCEL_PATH.exists():
    df_exist = pd.read_excel(EXCEL_PATH)

    # Convertir columna 'Data' a datetime para ordenar correctamente
    try:
        df_exist["Data"] = pd.to_datetime(df_exist["Data"], format="%d/%m/%Y")
    except Exception:
        pass  # por si ya está en formato datetime

    df_exist = df_exist.sort_values(by="Data", ascending=False)

    st.subheader("📋 Dades guardades")
    st.dataframe(df_exist)

    st.markdown("---")

else:
    st.info("ℹ️ Encara no hi ha dades guardades.")
    df_exist = pd.DataFrame()

# --- UI ----------------------------------------------------------------------
st.subheader("Nova entrada de dades")
st.write("Selecciona el **centre gran**, el **subcentre** (si aplica), la **data** i les **hores treballades**.")

centre_options = list(CENTRES.keys())
centre_gran: Optional[str] = st.radio(
    "Centre gran",
    options=centre_options,
    index=centre_options.index(st.session_state.centre_gran)
    if st.session_state.centre_gran in centre_options
    else 0,
)
st.session_state.centre_gran = centre_gran

subcentres = CENTRES.get(centre_gran, [])
subcentre: Optional[str] = None
if subcentres:
    subcentre = st.selectbox(
        "Subcentre",
        options=subcentres,
        index=subcentres.index(st.session_state.subcentre)
        if st.session_state.subcentre in subcentres
        else 0,
    )
    st.session_state.subcentre = subcentre
else:
    st.session_state.subcentre = None

# --- Selecció de data i hores -------------------------------------------------
st.markdown("---")
st.subheader("📅 Data i hores treballades")
col1, col2 = st.columns([2, 1])
with col1:
    data_treball = st.date_input(
        "Data de treball",
        value=st.session_state.data_treball,
        format="DD/MM/YYYY",
    )
with col2:
    hores_treballades = st.number_input(
        "Hores",
        min_value=0.0,
        max_value=24.0,
        step=0.5,
        value=st.session_state.hores_treballades,
    )

st.session_state.data_treball = data_treball
st.session_state.hores_treballades = hores_treballades

# --- Resum visual -------------------------------------------------------------
with st.container(border=True):
    st.subheader("Resum de selecció")
    st.write(f"**Centre gran:** {st.session_state.centre_gran}")
    if st.session_state.subcentre:
        st.write(f"**Subcentre:** {st.session_state.subcentre}")
    else:
        st.caption("Aquest centre no té subcentres per seleccionar.")
    st.write(f"**Data:** {st.session_state.data_treball.strftime('%d/%m/%Y')}")
    st.write(f"**Hores treballades:** {st.session_state.hores_treballades} h")

# --- Guardar dades a Excel ----------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    guardar = st.button("💾 Guardar dades", type="primary")
with col2:
    st.button("🔄 Reiniciar selecció", on_click=lambda: (
        st.session_state.update({
            "centre_gran": centre_options[0],
            "subcentre": CENTRES[centre_options[0]][0],
            "data_treball": datetime.date.today(),
            "hores_treballades": 0.0,
        })
    ))

if guardar:
    # Determinar el preu hora segons el centre
    if "Aspros" in st.session_state.centre_gran:
        preu_hora = 85.0
    else:
        preu_hora = 110.0

    registre = {
        "Centre gran": st.session_state.centre_gran,
        "Subcentre": st.session_state.subcentre if st.session_state.subcentre else "-",
        "Data": st.session_state.data_treball.strftime("%d/%m/%Y"),
        "Hores": st.session_state.hores_treballades,
        "Preu hora (€)": preu_hora,
        "Import (€)": st.session_state.hores_treballades * preu_hora,
    }

    # Crear o afegir al fitxer Excel
    if EXCEL_PATH.exists():
        df = pd.read_excel(EXCEL_PATH)
        df = pd.concat([df, pd.DataFrame([registre])], ignore_index=True)
    else:
        df = pd.DataFrame([registre])

    df.to_excel(EXCEL_PATH, index=False)

    st.success(f"✅ Dades desades correctament a '{EXCEL_PATH.name}'.")
    st.dataframe(df.sort_values(by='Data', ascending=False))


