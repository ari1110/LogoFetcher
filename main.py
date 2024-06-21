import streamlit as st
from components.ui import display_ui
import traceback

def main():
    display_ui()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_message = traceback.format_exc()
        st.error(f"An error occurred: {error_message}")
