import streamlit as st

st.set_page_config(page_title="Azure Test App", page_icon="✅", layout="centered")
st.title("✅ Azure Streamlit Deployment Test")

name = st.text_input("Enter your name:")

if st.button("Say Hello"):
    if name.strip():
        st.success(f"Hello, {name}! Your Streamlit app is running on Azure 🎉")
    else:
        st.warning("Please enter a name first.")
