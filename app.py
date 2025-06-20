import streamlit as st
import pandas as pd
import datetime
from io import BytesIO
import plotly.express as px
from utils.helpers import load_data, filter_data, save_data

# Ruta a tu CSV
DATA_PATH = "data/registro2.csv"

# Mapeo interno → encabezado original
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

# Configuración de la página
st.set_page_config(
    page_title="📋 Comercio Ambulatorio",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS para ocultar la flechita de la sidebar en móvil
st.markdown("""
    <style>
      .css-1lcbmhc.e1fqkh3o1, .css-1d391kg {
        visibility: hidden;
        width: 0;
        padding: 0;
      }
    </style>
""", unsafe_allow_html=True)

# 1. Carga de datos
df = load_data(DATA_PATH)

# 2. Controles dentro de un expander (más accesible en móvil)
with st.expander("🔎 Controles de Búsqueda y Exportación", expanded=True):
    # Búsqueda
    search_input = st.text_input("Buscar", placeholder="Nombre, DNI, Estado…")
    if st.button("🔍 Buscar", key="btn_search"):
        filtered = filter_data(df, search_input)
    else:
        filtered = df.copy()

    st.markdown("---")
    # Exportar CSV (;)
    csv_data = filtered.to_csv(index=False, sep=";", encoding="utf-8").encode()
    st.download_button(
        "📥 Descargar CSV (;)", csv_data,
        file_name="registros_filtrados.csv",
        mime="text/csv",
        key="dl_csv"
    )

    # Exportar Excel (.xlsx)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter",
                        datetime_format="yyyy-mm-dd", date_format="yyyy-mm-dd") as writer:
        filtered.rename(columns=DISPLAY_MAP).to_excel(
            writer, index=False, sheet_name="Registros"
        )
    st.download_button(
        "📥 Descargar Excel (.xlsx)",
        output.getvalue(),
        file_name="registros_filtrados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_xlsx"
    )

# 3. Métricas principales
st.title("📋 Registro de Comercio Ambulatorio")
col1, col2, col3 = st.columns(3)
col1.metric("Total registros", len(filtered))
if "estado" in filtered.columns:
    col2.metric("Autorizados", int((filtered.estado == "AUTORIZADO").sum()))
    col3.metric("En espera", int((filtered.estado == "ESPERA").sum()))

# 4. Tendencia mensual de registros
st.divider()
st.subheader("📈 Tendencia Mensual de Registros")
df_time = filtered.copy()
df_time["fecha_de_ingreso"] = pd.to_datetime(
    df_time["fecha_de_ingreso"], dayfirst=True, errors="coerce"
)
monthly = (
    df_time
      .groupby(df_time["fecha_de_ingreso"].dt.to_period("M"))
      .size()
      .reset_index(name="conteo")
)
monthly["mes"] = monthly["fecha_de_ingreso"].dt.strftime("%b %Y")

fig = px.bar(
    monthly,
    x="mes",
    y="conteo",
    color="mes",
    title="Registros por Mes de Ingreso",
    labels={"mes": "Mes", "conteo": "Cantidad de registros"}
)
st.plotly_chart(fig, use_container_width=True, height=400)

# 5. Pestañas: Ver ▸ Agregar ▸ Editar/Eliminar
tab1, tab2, tab3 = st.tabs([
    "📖 Ver Registros",
    "➕ Agregar Registro",
    "✏️ Editar / 🗑️ Eliminar"
])

# Tab 1: Ver registros
with tab1:
    st.subheader("📋 Resultados de la búsqueda")
    st.dataframe(
        filtered.rename(columns=DISPLAY_MAP),
        use_container_width=True,
        height=600
    )

# Tab 2: Agregar registro
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
            try:
                st.experimental_rerun()
            except AttributeError:
                pass

# Tab 3: Editar / Eliminar registros
with tab3:
    st.subheader("✏️ Editar / 🗑️ Eliminar registros")
    if filtered.empty:
        st.info("No hay registros para modificar.")
    else:
        idx = st.number_input(
            "Índice a modificar/eliminar",
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
                    label = DISPLAY_MAP.get(col, col.replace("_", " ").title())
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
                        df.at[idx, k] = (
                            v.strftime("%Y-%m-%d") if hasattr(v, "strftime") else v
                        )
                    save_data(df, DATA_PATH)
                    st.success("✅ Registro actualizado")
                    try:
                        st.experimental_rerun()
                    except AttributeError:
                        pass
        else:
            if st.button("Eliminar registro"):
                df2 = df.drop(idx).reset_index(drop=True)
                save_data(df2, DATA_PATH)
                st.success("🗑️ Registro eliminado")
                try:
                    st.experimental_rerun()
                except AttributeError:
                    pass
