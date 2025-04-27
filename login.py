# login.py
import streamlit as st
import psycopg2
import hashlib

def get_connection():
    return psycopg2.connect(
        host="localhost", dbname="llmqa",
        user="postgres", password="postgres", port="5432"
    )

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    hashed = hash_password(password)

    cur.execute("""
        SELECT user_id, role FROM users
        WHERE username = %s AND password = %s AND is_active = TRUE
    """, (username, hashed))

    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

def app():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.user_id = user[0]
            st.session_state.role = user[1]
            st.success("Login successful!")
        else:
            st.error("Invalid credentials or inactive user.")
