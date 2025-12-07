import streamlit as st
import requests

# Use secrets in production, fallback to localhost for local dev
BACKEND_URL = st.secrets.get("BACKEND_URL", "http://localhost:1234")