 ollama run deepseek-r1:1.5b
 ollama serve
https://ollama.com/library/deepseek-r1:1.5b
https://www.datacamp.com/tutorial/deepseek-r1-ollama

https://www.youtube.com/watch?v=i8HsZjfszE8
https://www.youtube.com/watch?v=7R8bk4pCThA


Whisper
https://www.youtube.com/watch?v=ABFqbY_rmEk



https://www.youtube.com/watch?v=qNUbPw62-rk&ab_channel=KrishNaik
https://github.com/krishnaik06/Gen-AI-With-Deep-Seek-R1
https://github.com/krishnaik06/Gen-AI-With-Deep-Seek-R1/blob/main/app.py



mcq and openended 
multimodal llm application in evalution 


conda activate Torch
pip install psycopg2
streamlit run .\QandA.py      


CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) CHECK (role IN ('admin', 'student')) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_updated BOOLEAN DEFAULT FALSE
);

INSERT INTO users (user_id, username, password, role, is_active)
VALUES ('u1', 'testuser', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'admin', TRUE);
-- password = 'password'

pip install evaluate bert-score
