import streamlit as st
import psycopg2
from datetime import datetime
import logging

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="llmqa",
        user="postgres",
        password="postgres"
    )

def app():  # 👈 Wrap everything in this function
    st.title("Question Entry Form")

    topic = st.text_input("Enter Topic Name")
    question = st.text_area("Enter Question")
    answer = st.text_area("Enter Answer")
    created_by = st.text_input("Enter Your UID")

    if st.button("Submit"):
        if not all([topic, question, answer, created_by]):
            st.warning("Please fill in all fields.")
        else:
            try:
                conn = get_connection()
                cur = conn.cursor()
                insert_query = """
                    INSERT INTO questions (topic_name, question, answer, created_by, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cur.execute(insert_query, (topic, question, answer, created_by, datetime.now()))
                conn.commit()
                cur.close()
                conn.close()
                st.success("✅ Question saved to database!")
            except Exception as e:
                st.error("❌ Failed to insert data.")
                st.exception(e)

    st.markdown("---")
    st.header("📋 View / Update / Delete Questions")

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, topic_name, question, answer, created_by, created_at FROM questions ORDER BY id DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            st.info("No questions found.")
        else:
            for row in rows:
                qid, topic, updatequestion, updateanswer, uid, created_at = row

                with st.expander(f"🔹 {topic} (by {uid} at {created_at.strftime('%Y-%m-%d %H:%M:%S')})"):
                    st.write("**Question:**", updatequestion)
                    st.write("**Answer:**", updateanswer)

                    col1, col2 = st.columns(2)
                    update_key = f"update_mode_{qid}"

                    with col1:
                        if st.button(f"✏️ Update", key=f"update_{qid}"):
                            st.session_state[update_key] = True

                    if st.session_state.get(update_key, False):
                        new_question = st.text_area("Edit Question", value=updatequestion, key=f"qedit_{qid}")
                        new_answer = st.text_area("Edit Answer", value=updateanswer, key=f"aedit_{qid}")

                        if st.button("💾 Save", key=f"save_{qid}"):
                            try:
                                conn = get_connection()
                                cur = conn.cursor()
                                cur.execute("""
                                    UPDATE questions
                                    SET question = %s, answer = %s
                                    WHERE id = %s
                                """, (new_question, new_answer, qid))
                                conn.commit()
                                cur.close()
                                conn.close()
                                st.success("✅ Updated successfully.")
                                st.rerun()
                            except Exception as e:
                                st.error("Update failed!")
                                st.exception(e)

                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_{qid}"):
                            try:
                                conn = get_connection()
                                cur = conn.cursor()
                                cur.execute("DELETE FROM questions WHERE id = %s", (qid,))
                                conn.commit()
                                cur.close()
                                conn.close()
                                st.warning("🗑️ Question deleted.")
                                st.rerun()
                            except Exception as e:
                                st.error("Delete failed!")
                                st.exception(e)

    except Exception as e:
        st.error("❌ Could not fetch data")
        st.exception(e)
