import streamlit as st
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load .env variables
load_dotenv()

client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

# --- Streamlit UI ---
st.set_page_config(page_title="Azure OpenAI POC", page_icon="🤖", layout="centered")
st.title("🤖 Azure OpenAI POC with Streamlit")

st.write("Enter a prompt below and let Azure OpenAI respond.")

user_prompt = st.text_area("Your prompt", placeholder="e.g., Suggest 3 marketing ideas for a coffee shop.")

temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.7)
max_tokens = st.slider("Max tokens", 100, 1000, 300)

if st.button("Generate Response"):
    if not user_prompt.strip():
        st.warning("Please enter a prompt before generating a response.")
    else:
        try:
            with st.spinner("Thinking..."):
                response = client.chat.completions.create(
                    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),  # Deployment name from .env
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature
                )
                output = response.choices[0].message.content
                st.success("Response generated!")
                st.write(output)

        except Exception as e:
            st.error(f"Error: {e}")

