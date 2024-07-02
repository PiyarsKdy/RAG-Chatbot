import streamlit as st
from streamlit_float import *

# Float feature initialization
float_init()

# Initialize session variable that will open/close dialog
if "show" not in st.session_state:
    st.session_state.show = False

# Button that opens the dialog
if st.button("Contact us"):
        st.session_state.show = True
        st.experimental_rerun()

# Create Float Dialog container
dialog_container = float_dialog(st.session_state.show)

# Add contents of Dialog including button to close it
with dialog_container:
    st.header("Contact us")
    name_input = st.text_input("Enter your name", key="name")
    email_input = st.text_input("Enter your email", key="email")
    message = st.text_area("Enter your message", key="message")
    if st.button("Send", key="send"):
        # ...Handle input data here...
        st.session_state.show = False
        st.experimental_rerun()