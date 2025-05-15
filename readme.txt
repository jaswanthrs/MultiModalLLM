Project Title: Open-ended Question-Answer Evaluation System
===========================================================

Overview:
---------
This application is designed to evaluate open-ended questions using typed or voice responses. It uses document-based question generation, LLM-based answer evaluation, and NLP scoring techniques. The system is implemented in Python using Streamlit for the UI, PostgreSQL for data persistence, and Whisper for speech-to-text transcription.

Main Features:
--------------
1. Upload PDF documents to extract content.
2. Automatically generate question-answer pairs using LangChain + Ollama (DeepSeek).
3. Allow manual editing and validation of questions by administrators.
4. Students can answer questions via text or voice.
5. Automatic scoring using:
   - LLM-based correctness, completeness, relevance, depth
   - NLP metrics: BLEU, ROUGE-L, BERTScore
6. Results stored in PostgreSQL and visible to users/admins.
7. Session-based interaction and feedback.



Setup Instructions:
-------------------
1. Ensure Python 3.10 or higher is installed.
2. Install dependencies using:
   > pip install -r requirements.txt

3. Start PostgreSQL and ensure the following tables are created:
   - questions
   - user_answers
   - users

4. Run the application:
   > streamlit run Menu.py

Model Requirements:
-------------------
- Ollama must be installed locally and model `deepseek-r1:1.5b` available.
- Whisper (`small` model) will be used for voice transcription.

RefLink:
------------
https://ollama.com/library/deepseek-r1:1.5b

Ollama reflink 
https://www.youtube.com/watch?v=i8HsZjfszE8

Whisper refLink
https://www.youtube.com/watch?v=ABFqbY_rmEk

Directory Structure:
--------------------
- Menu.py                : Main application file
- db scripts             : SQL scripts for DB setup
- README.txt             : Project instructions
- requirements.txt       : Dependency list

Contributors:
-------------
- R.S.Jaswanth

Contact:
--------
For questions or support, email: Jaswanth@gmail.com

