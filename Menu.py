# menu.py
import streamlit as st
import login  # Make sure login.py is in the same folder
import QandACreator
import QandA
import AnswerEvaluator
import UserAnswerFeedback
import UserAnswerEvaluator
import admin_user_manager

# Initialize login state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Show login if not logged in
if not st.session_state.logged_in:
    login.app()  # Load login screen
    st.stop()    # Stop here — don’t load menu

# 👇 If we reach here, user is logged in
st.markdown("<h1 style='text-align: center;'>LLM Q&A Assistant</h1>", unsafe_allow_html=True)

st.sidebar.title("📂 Navigation Menu")

menu_options = [
    "🔧 Admin: Q&A PDF Upload",
    "🔧 Admin: List QandA",
    "🔧 Admin: Answer Evaluator",
    "🔧 Admin: Admin User Manager",
    "🧑‍💻 User: Feedback Provider",
    "🧑‍💻 User: User Answer Evaluator"
]

choice = st.sidebar.radio("Select an Option", menu_options)

if choice == "🔧 Admin: Q&A PDF Upload":
    QandACreator.app()
elif choice == "🔧 Admin: List QandA":
    QandA.app()
elif choice == "🔧 Admin: Answer Evaluator":
    AnswerEvaluator.app()
elif choice == "🔧 Admin: Admin User Manager":
    admin_user_manager.app()    
elif choice == "🧑‍💻 User: Feedback Provider":
    UserAnswerFeedback.app()
elif choice == "🧑‍💻 User: User Answer Evaluator":
    UserAnswerEvaluator.app()

# Logout Button
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_id = None
    st.session_state.role = ""
    st.success("Logged out!")
    st.rerun()  # ✅ Correct replacement
