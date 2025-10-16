import streamlit as st
from typing import Optional
import datetime
import json
import os
import pandas as pd
from pathlib import Path

# --- Carpeta base per guardar els arxius ---
BASE_DIR = Path("dades_facturacio")

# --- Funcions auxiliars -------------------------------------------------------
def get_mes_name(mes_num):
    mesos = [
        "gener", "febrer", "març", "abril", "maig", "juny",
        "juliol", "agost", "setembre", "octubre", "novembre", "desembre"
    ]
    return mesos[mes_num - 1]

def get_json_path(any, mes):
    carpeta_any = BASE_DIR / str(any)
    carpeta_any.mkdir(parents=True, exist_ok=True)
    return carpeta_any / f"{mes:02d}-{get_mes_name(mes)}.json"

def carregar_dades(any, mes):
    path = get_json_path(any, mes)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    return []

def guardar_dades(any, mes, dades):
    path = get_json_path(any, mes)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dades, f, indent=4, ensure_ascii=False)

# --- Inicialització -----------------------------------------------------------
today = datetime.date.today()
any_actual = today.year
mes_actual = today.month

if "any_seleccionat" not in st.session_state:
    st.session_state["any_seleccionat"] = any_actual
    st.session_state["mes_seleccionat"] = mes_actual
    st.session_state["dades"] = carregar_dades(any_actual, mes_actual)
    st.session_state["edit_index"] = None  # índex del registre a editar

# --- Constants ---------------------------------------------------------------
CENTRES = {
    "Aspros": ["Centre Casa Nostra", "Centre Llars Urbanes", "Centre La Coma"],
    "Terraferma": [],
}

# --- UI Selecció d'any i mes --------------------------------------------------
st.title("📊 Gestió de facturació per mesos i anys")

col1, col2 = st.columns(2)
with col1:
    any_seleccionat = st.number_input("Any", min_value=2020, max_value=2100, value=st.session_state["any_seleccionat"], step=1)
with col2:
    mes_seleccionat = st.selectbox(
        "Mes",
        options=list(range(1, 13)),
        format_func=lambda x: get_mes_name(x).capitalize(),
        index=st.session_state["mes_seleccionat"] - 1,
    )

if st.button("📂 Carregar dades del període seleccionat"):
    st.session_state["any_seleccionat"] = any_seleccionat
    st.session_state["mes_seleccionat"] = mes_seleccionat
    st.session_state["dades"] = carregar_dades(any_seleccionat, mes_seleccionat)
    st.session_state["edit_index"] = None
    st.success(f"Dades carregades: {get_mes_name(mes_seleccionat)} {any_seleccionat}")

st.markdown("---")

# --- Mostrar dades guardades -------------------------------------------------
st.subheader(f"📋 Dades de {get_mes_name(st.session_state['mes_seleccionat'])} {st.session_state['any_seleccionat']}")

if st.session_state["dades"]:
    df = pd.DataFrame(st.session_state["dades"])
    df = df.fillna("").astype(str)
    for i, row in df.iterrows():
        with st.expander(f"🔹 {row['Data']} — {row['Centre gran']} ({row['Hores']}h, {row['Import (€)']}€)"):
            st.write(row)
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✏️ Editar #{i}", key=f"edit_{i}"):
                    st.session_state["edit_index"] = i
                    st.rerun()
            with col2:
                if st.button(f"🗑️ Eliminar #{i}", key=f"del_{i}"):
                    st.session_state["dades"].pop(i)
                    guardar_dades(st.session_state["any_seleccionat"], st.session_state["mes_seleccionat"], st.session_state["dades"])
                    st.success("Registre eliminat ✅")
                    st.rerun()
else:
    st.info("Encara no hi ha dades guardades per aquest període.")

# --- Form per afegir o editar -------------------------------------------------
st.markdown("---")
if st.session_state["edit_index"] is not None:
    st.subheader("✏️ Editar registre")
    edit_reg = st.session_state["dades"][st.session_state["edit_index"]]
else:
    st.subheader("🆕 Nova entrada de dades")
    edit_reg = {}

centre_options = list(CENTRES.keys())
centre_gran = st.radio("Centre gran", options=centre_options, index=centre_options.index(edit_reg.get("Centre gran", "Aspros")) if edit_reg else 0)
subcentres = CENTRES.get(centre_gran, [])
subcentre = st.selectbox("Subcentre", options=subcentres if subcentres else ["-"], index=0)

col1, col2 = st.columns([2, 1])
with col1:
    data_treball = st.date_input("Data de treball", value=today, format="DD/MM/YYYY")
with col2:
    hores_treballades = st.number_input("Hores", min_value=0.0, max_value=24.0, step=0.5, value=float(edit_reg.get("Hores", 0.0)) if edit_reg else 0.0)

preu_hora = 85.0 if "Aspros" in centre_gran else 110.0

if st.button("💾 Guardar dades", type="primary"):
    registre = {
        "Centre gran": centre_gran,
        "Subcentre": subcentre,
        "Data": data_treball.strftime("%d-%b."),
        "Hores": hores_treballades,
        "Preu hora (€)": preu_hora,
        "Import (€)": hores_treballades * preu_hora,
    }

    if st.session_state["edit_index"] is not None:
        st.session_state["dades"][st.session_state["edit_index"]] = registre
        st.session_state["edit_index"] = None
        st.success("✅ Registre actualitzat correctament.")
    else:
        st.session_state["dades"].append(registre)
        st.success("✅ Nou registre afegit.")

    guardar_dades(st.session_state["any_seleccionat"], st.session_state["mes_seleccionat"], st.session_state["dades"])
    st.rerun()

if st.button("🗑️ Esborrar totes les dades del mes"):
    st.session_state["dades"] = []
    guardar_dades(st.session_state["any_seleccionat"], st.session_state["mes_seleccionat"], [])
    st.warning("⚠️ Dades del mes esborrades.")
