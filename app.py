import streamlit as st
import pandas as pd
import json
import pyreadstat
import io
import os

# Configuration de la page
st.set_page_config(page_title="Convertisseur universel", layout="wide")

# Titre principal
st.title("🔄 MI File Converter  (Excel / CSV / SPSS ) → (JSON, CSV, Excel, Parquet)")

# Upload du fichier
uploaded_file = st.file_uploader("📁 Charger un fichier (.xlsx, .csv, .sav)", type=["xlsx", "xls", "csv", "sav"])

# Nom par défaut basé sur le fichier
default_name = os.path.splitext(uploaded_file.name)[0] if uploaded_file else "fichier_converti"
file_name_input = st.text_input("✏️ Nom de base des fichiers exportés", value=default_name)

# Traitement après upload
if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1].lower()
    try:
        if file_type in ["xlsx", "xls"]:
            df = pd.read_excel(uploaded_file)
        elif file_type == "csv":
            df = pd.read_csv(uploaded_file)
        elif file_type == "sav":
            # Enregistrer temporairement le fichier en local
            temp_path = "temp_uploaded_file.sav"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())
            df, meta = pyreadstat.read_sav(temp_path)
            os.remove(temp_path)
        else:
            st.error("❌ Format non pris en charge.")
            st.stop()
    except Exception as e:
        st.error("❌ Erreur à la lecture du fichier :")
        st.exception(e)
        st.stop()

    # Interface multi-onglets
    tab1, tab2 = st.tabs(["🧼 Aperçu & Nettoyage", "⬇️ Export fichiers"])

    with tab1:
        st.subheader("👁️ Aperçu du tableau original")
        st.dataframe(df.head(50), use_container_width=True)

        st.markdown("---")
        st.subheader("🧹 Nettoyage des données")

        # Nettoyage : suppression des NaN
        remove_nan = st.checkbox("❌ Supprimer les lignes contenant des valeurs manquantes", value=False)

        # Nouvelle fonctionnalité : colonnes à inclure
        cols_to_include = st.multiselect("✅ Colonnes à INCLURE dans le fichier final (facultatif)", options=df.columns)

        # Colonnes à exclure si rien n'est inclus
        cols_to_exclude = st.multiselect("🚫 Colonnes à EXCLURE du fichier final (optionnel)", options=df.columns)

        # Application des nettoyages
        cleaned_df = df.copy()
        if remove_nan:
            cleaned_df = cleaned_df.dropna()

        # Si colonnes à inclure sélectionnées → priorité
        if cols_to_include:
            cleaned_df = cleaned_df[cols_to_include]
        elif cols_to_exclude:
            cleaned_df = cleaned_df.drop(columns=cols_to_exclude)

        st.success(f"✅ Données nettoyées : {cleaned_df.shape[0]} lignes / {cleaned_df.shape[1]} colonnes")
        st.dataframe(cleaned_df.head(50), use_container_width=True)

    with tab2:
        st.subheader("⬇️ Générer les fichiers exportables")

        if st.button("🚀 Convertir et exporter"):
            try:
                # Conversion JSON
                df_str = cleaned_df.astype(str)
                json_data = df_str.to_dict(orient="records")
                json_str = json.dumps(json_data, indent=2, ensure_ascii=False)

                # Conversion CSV
                csv_str = cleaned_df.to_csv(index=False)

                # Conversion Excel
                excel_buffer = io.BytesIO()
                cleaned_df.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_buffer.seek(0)

                # Conversion Parquet
                parquet_buffer = io.BytesIO()
                cleaned_df.to_parquet(parquet_buffer, index=False)
                parquet_buffer.seek(0)

                # Aperçu JSON
                with st.expander("👁️ Aperçu JSON"):
                    st.code(json_str[:5000], language="json")

                # Téléchargement
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("⬇️ Télécharger JSON", data=json_str,
                        file_name=file_name_input + ".json", mime="application/json")
                    st.download_button("⬇️ Télécharger CSV", data=csv_str,
                        file_name=file_name_input + ".csv", mime="text/csv")
                with col2:
                    st.download_button("⬇️ Télécharger Excel", data=excel_buffer,
                        file_name=file_name_input + ".xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    st.download_button("⬇️ Télécharger Parquet", data=parquet_buffer,
                        file_name=file_name_input + ".parquet", mime="application/octet-stream")

                st.text_area("📋 Copier le JSON ici :", json_str, height=300)

            except Exception as e:
                st.error("❌ Erreur lors de l'export :")
                st.exception(e)
