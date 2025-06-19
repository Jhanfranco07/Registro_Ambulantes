import streamlit as st
import pandas as pd
import datetime
from io import BytesIO
from helpers import load_data, filter_data, save_data

DATA_PATH = "registro2.csv"

DISPLAY_MAP = {
    "estado":                            "ESTADO",
    "n°":                                "N°",
    "fecha_de_ingreso":                  "FECHA DE INGRESO",
    "n°_de_documento_simple":            "N° DE DOCUMENTO SIMPLE",
    "asunto":                            "ASUNTO",
    "nombre_y_apellido":                 "NOMBRE Y APELLIDO",
    "dni":                               "DNI",
    "domicilio_fiscal":                  "DOMICILIO FISCAL",
    "giro_o_motivo_de_la_solicitud":     "GIRO O MOTIVO DE LA SOLICITUD",
    "ubicacion":                         "UBICACIÓN A SOLICITAR",
    "n°_de_celular":                     "N° DE CELULAR",
    "procedente_/_improcedente":         "PROCEDENTE / IMPROCEDENTE",
    "n°_de_carta":                       "N° DE CARTA",
    "fecha_de_la_carta":                 "FECHA DE LA CARTA",
    "fecha_de_notificacion":             "FECHA DE NOTIFICACIÓN",
    "anexo":                             "ANEXO",
    "fecha_extra":                       "FECHA",
    "asunto_extra":                      "ASUNTO",
    "folios":                            "FOLIOS",
    "archivo":                           "ARCHIVO"
}

st.set_page_config(page_title="Comercio Ambulatorio", layout="wide")

# Sidebar: búsqueda y exportación
st.sidebar.header("🔎 Controles")
df = load_data(DATA_PATH)
query = st.sidebar.text_input("Buscar", placeholder="Nombre, DNI, Estado…")
filtered = filter_data(df, query)

st.sidebar.markdown("---")
st.sidebar.write("📥 **Exportar datos**")
csv_data = filtered.to_csv(index=False, sep=";", encoding="utf-8").encode()
st.sidebar.download_button("CSV (;)", csv_data, "registros.csv", "text/csv")
output = BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter",
                    datetime_format="yyyy-mm-dd", date_format="yyyy-mm-dd") as writer:
    filtered.rename(columns=DISPLAY_MAP).to_excel(writer, index=False, sheet_name="Registros")
st.sidebar.download_button("Excel (.xlsx)", output.getvalue(),
                            "registros.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Métricas
st.title("📋 Registro de Comercio Ambulatorio")
c1, c2, c3 = st.columns(3)
c1.metric("Total registros", len(filtered))
if "estado" in df.columns:
    c2.metric("Autorizados", int((df.estado == "AUTORIZADO").sum()))
    c3.metric("En espera", int((df.estado == "ESPERA").sum()))

# Gráfico
if "estado" in df.columns:
    st.divider()
    st.subheader("📊 Distribución por Estado")
    st.bar_chart(df.estado.value_counts(), height=300)

# Pestañas
tab1, tab2, tab3 = st.tabs(["📖 Ver Registros", "➕ Agregar Registro", "✏️ Editar / 🗑️ Eliminar"])

# --- Tab 1: Ver registros ---
with tab1:
    st.subheader("📋 Resultados de la búsqueda")
    st.dataframe(filtered.rename(columns=DISPLAY_MAP),
                use_container_width=True,
                height=600)

# --- Tab 2: Agregar registro ---
with tab2:
    st.subheader("➕ Agregar nuevo registro")
    with st.form("add_form", clear_on_submit=True):
        left, right = st.columns(2)
        new = {}
        for i, col in enumerate(df.columns):
            label = DISPLAY_MAP.get(col, col.replace("_", " ").title())
            widget = left if i % 2 == 0 else right
            if "fecha" in col:
                new[col] = widget.date_input(label)
            else:
                new[col] = widget.text_input(label)
        if st.form_submit_button("Registrar"):
            row = {
                k: (v.strftime("%Y-%m-%d") if hasattr(v, "strftime") else v)
                for k, v in new.items()
            }
            df2 = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            save_data(df2, DATA_PATH)
            st.success("✅ Registro guardado")
            try: st.experimental_rerun()
            except: pass

# --- Tab 3: Editar / Eliminar ---
with tab3:
    st.subheader("✏️ Editar / 🗑️ Eliminar registros")
    if filtered.empty:
        st.info("No hay registros para modificar.")
    else:
        # Número de índice
        idx = st.number_input(
            "Índice a editar/eliminar",
            min_value=int(filtered.index.min()),
            max_value=int(filtered.index.max()),
            value=int(filtered.index.min()),
            step=1
        )
        row = filtered.loc[idx]
        action = st.radio("Acción", ["Editar", "Eliminar"], horizontal=True)

        if action == "Editar":
            with st.form("edit_form", clear_on_submit=False):
                edits = {}
                for col in df.columns:
                    label = DISPLAY_MAP.get(col, col.replace("_"," ").title())
                    cell = row.get(col, "")
                    if "fecha" in col:
                        if pd.isna(cell) or cell == "":
                            edits[col] = st.date_input(label, key=f"e_{col}")
                        else:
                            parsed = pd.to_datetime(cell, dayfirst=True, errors="coerce")
                            default = parsed.date() if not pd.isna(parsed) else datetime.date.today()
                            edits[col] = st.date_input(label, value=default, key=f"e_{col}")
                    else:
                        edits[col] = st.text_input(label, value=cell or "", key=f"e_{col}")
                if st.form_submit_button("Guardar cambios"):
                    for k, v in edits.items():
                        df.at[idx, k] = v.strftime("%Y-%m-%d") if hasattr(v, "strftime") else v
                    save_data(df, DATA_PATH)
                    st.success("✅ Registro actualizado")
                    try: st.experimental_rerun()
                    except: pass

        else:  # Eliminar
            if st.button("Eliminar registro"):
                df2 = df.drop(idx).reset_index(drop=True)
                save_data(df2, DATA_PATH)
                st.success("🗑️ Registro eliminado")
                try: st.experimental_rerun()
                except: pass
