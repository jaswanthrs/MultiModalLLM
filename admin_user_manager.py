import streamlit as st
import psycopg2
import hashlib

# ------------------ DB Connection ------------------
def get_connection():
    return psycopg2.connect(
        host="localhost",        # 🔁 Update as needed
        dbname="llmqa",
        user="postgres",
        password="postgres",
        port="5432"
    )

# ------------------ Password Hashing ------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------ Add User Function ------------------
def add_user(username, user_id, password, role, is_active=True, is_updated=False):
    conn = get_connection()
    cur = conn.cursor()
    hashed = hash_password(password)

    cur.execute("""
        INSERT INTO users (username, user_id, password, role, is_active, is_updated)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (username, user_id, hashed, role, is_active, is_updated))

    conn.commit()
    cur.close()
    conn.close()

# ------------------ Admin UI ------------------
def app():
    if st.session_state.get("role") != "admin":
        st.error("⛔ Access Denied. Admins only.")
        return

    st.title("👥 Add New User")

    username = st.text_input("Username")
    user_id = st.text_input("User ID")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["admin", "student"])
    is_active = st.checkbox("Is Active?", value=True)

    if st.button("Add User"):
        if username and user_id and password:
            add_user(username, user_id, password, role, is_active)
            st.success(f"✅ User **{username}** added successfully.")
        else:
            st.warning("⚠️ Please fill in all fields.")
