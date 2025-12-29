import streamlit as st

st.set_page_config(
    page_title="RightRent",
    page_icon="📄",
    layout="centered"
)

if "preferences" not in st.session_state:
    st.session_state.preferences = {}

st.title("RightRent")
st.write("AI-assisted contract understanding for renters")

