import streamlit as st
import pandas as pd
import joblib
import io

# === SAYFA AYARLARI === #
st.set_page_config(
    page_title="Kolon Kanseri Tahmin Aracı",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="auto"
)

# === DİL SEÇİMİ === #
language = st.selectbox("Dil Seçin", ["Türkçe", "English"])

# === DİL BAZLI METİNLER === #
texts = {
    "Türkçe": {
        "title": "🧬 Kolon Kanseri Tahmin Aracı",
        "description": "Erken teşhis hayat kurtarır! Bu araç, belirli gen ifadelerine göre kolon kanseri riski tahmini yapar.",
        "privacy_warning": "**Uyarı:** Girdiğiniz veriler kaydedilmez ve tamamen gizlidir.",
        "tab_single": "👤 Tekli Tahmin",
        "tab_bulk": "📁 Toplu Tahmin",
        "gen_expression": "Gen İfadelerini Giriniz",
        "predict": "🔎 Tahmin Et",
        "low_risk": "✅ Düşük risk: Model kanser riski tespit etmedi.",
        "high_risk": "⚠️ Yüksek risk: Model kolon kanseri riski tespit etti. Lütfen bir uzmana danışın.",
        "model_input": "🧠 Model Girişi",
        "bulk_upload": "Excel Dosyası ile Toplu Tahmin",
        "csv_example": "📄 Örnek Excel İndir",
        "download_excel": "📥 Excel Olarak İndir",
        "note": "📌 **Not:** Bu araç yalnızca eğitim amaçlıdır ve tıbbi tanı yerine geçmez.",
    },
    "English": {
        "title": "🧬 Colon Cancer Prediction Tool",
        "description": "Early diagnosis saves lives! This tool predicts colon cancer risk based on specific gene expressions.",
        "privacy_warning": "**Warning:** The data you enter is not saved and is completely private.",
        "tab_single": "👤 Single Prediction",
        "tab_bulk": "📁 Bulk Prediction",
        "gen_expression": "Enter Gene Expressions",
        "predict": "🔎 Predict",
        "low_risk": "✅ Low risk: The model did not detect cancer risk.",
        "high_risk": "⚠️ High risk: The model detected colon cancer risk. Please consult a specialist.",
        "model_input": "🧠 Model Input",
        "bulk_upload": "Bulk Prediction via Excel",
        "csv_example": "📄 Download Example Excel",
        "download_excel": "📥 Download as Excel",
        "note": "📌 **Note:** This tool is for educational purposes only and does not replace medical diagnosis.",
    }
}

# Seçilen dilin metinlerini al
selected_texts = texts[language]

# === STİL === #
st.markdown("""
    <style>
        body {
            background-color: #f8f9fa;
        }
        h1, h2, h3 {
            color: #800080;
        }
        .stButton>button {
            background-color: #6f42c1;
            color: white;
            font-weight: bold;
        }
        .stDownloadButton>button {
            background-color: #198754;
            color: white;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# === BAŞLIK === #
st.title(selected_texts["title"])
st.markdown(selected_texts["description"])
st.info(selected_texts["privacy_warning"])

# === GEN HARİTASI === #
expression_map = {
    "Neg": 0,
    "Zayıf Pos": 1,
    "Pos": 2,
    "Pos +": 3,
    "Pos 2+": 4,
    "Pos 3+": 5,
    "Pos 4+": 6,
    "Pos 5+": 7,
    "Pos 6+": 8,
    "Pos 7+": 9
}
inverse_expression_map = {v: k for k, v in expression_map.items()}

options = list(expression_map.keys())
columns = ['TFPI2 SET-1', 'SEPTIN9 SET-1 R1', 'SDC2 SET-3', 'SFRP2 SET1 (40)', 'HOXA2 SET1']

# === MODEL YÜKLEME === #
@st.cache_resource
def load_model():
    return joblib.load("final.pkl")

model = load_model()

# === SEKME YAPISI === #
tab1, tab2 = st.tabs([selected_texts["tab_single"], selected_texts["tab_bulk"]])

# === TEKLİ TAHMİN === #
with tab1:
    st.header(selected_texts["gen_expression"])

    user_input = {}
    for col in columns:
        user_input[col] = st.selectbox(f"{col} ifadesi", options)

    if st.button(selected_texts["predict"]):
        input_encoded = [expression_map[user_input[col]] for col in columns]
        input_df = pd.DataFrame([input_encoded], columns=columns)
        prediction = model.predict(input_df)[0]

        # Tahmin sonucu
        if prediction == 0:
            st.success(selected_texts["low_risk"])
        else:
            st.error(selected_texts["high_risk"])

        st.markdown("---")
        st.subheader(selected_texts["model_input"])

        # Numeric değerleri metinlere çevirerek göster
        input_text_df = pd.DataFrame([user_input])
        st.write(input_text_df)

# === TOPLU TAHMİN === #
with tab2:
    st.header(selected_texts["bulk_upload"])

    st.markdown("**📌 Excel dosyanız şu kolonları içermelidir:**")
    st.code(", ".join(columns), language="markdown")

    uploaded_file = st.file_uploader("Excel dosyası yükleyin", type="xlsx")

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)

            # Kontrol ve dönüştürme
            for col in columns:
                if col in df.columns:
                    df[col] = df[col].map(expression_map)
                else:
                    st.error(f"❌ Hata: '{col}' kolonu eksik.")
                    st.stop()

            predictions = model.predict(df[columns])
            df["Tahmin"] = predictions
            df["Tahmin"] = df["Tahmin"].map(lambda x: "Düşük risk" if x == 0 else "Yüksek risk")

            # Sayısal değerleri metne çevir
            for col in columns:
                df[col] = df[col].map(inverse_expression_map)

            st.success("✅ Tahminler başarıyla oluşturuldu.")
            st.dataframe(df)

            # Excel olarak indirme
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Sonuclar")
            buffer.seek(0)

            st.download_button(selected_texts["download_excel"], data=buffer, file_name="tahmin_sonuclari.xlsx")

        except Exception as e:
            st.error(f"❌ Dosya işlenirken hata oluştu: {str(e)}")

    # Örnek dosya indir
    sample_df = pd.DataFrame([[opt for opt in options[:5]]], columns=columns)
    with io.BytesIO() as buffer:
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            sample_df.to_excel(writer, index=False, sheet_name="Örnek Veriler")
        buffer.seek(0)
        st.download_button(selected_texts["csv_example"], data=buffer, file_name="ornek.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# === ALT BİLGİ === #
st.markdown(f"""
---
{selected_texts["note"]}
""")
