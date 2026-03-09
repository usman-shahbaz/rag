import streamlit as st
from openai import OpenAI
from mem0 import Memory
import os
import json
from datetime import datetime, timedelta

st.title("AI Customer Support Agent with Memory 🛒")
st.caption("Chat with a customer support assistant who remembers your past interactions.")

openai_api_key = st.text_input("Enter OpenAI API Key", type="password")

if openai_api_key:
    os.environ['OPENAI_API_KEY'] = openai_api_key

 class CustomerSupportAIAgent:
        def __init__(self):
            config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "model": "gpt-4o-mini",
                        "host": "localhost",
                        "port": 6333,
                    }
                },
            }
            self.memory = Memory.from_config(config)
            self.client = OpenAI()
            self.app_id = "customer-support"
