import sqlite3
import json
from datetime import datetime


class SQLiteService:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def disconnect(self):
        if self.conn:
            self.conn.close()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                age INTEGER,
                difficulty TEXT,
                scenario TEXT,
                character TEXT,
                exercise TEXT,
                answer TEXT,
                created_at TIMESTAMP
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS llm_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input TEXT,
                output TEXT,
                model TEXT,
                created_at TIMESTAMP
            )
        ''')

        self.conn.commit()

    def insert_exercise(self, age, difficulty, scenario, character, exercise, answer):
        self.cursor.execute('''
            INSERT INTO exercises (age, difficulty, scenario, character, exercise, answer, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (age, difficulty, scenario, character, exercise, answer, datetime.now()))
        self.conn.commit()
        return self.cursor.lastrowid

    def insert_llm_interaction(self, input_data, output_data, model):
        self.cursor.execute('''
            INSERT INTO llm_interactions (input, output, model, created_at)
            VALUES (?, ?, ?, ?)
        ''', (json.dumps(input_data), json.dumps(output_data), model, datetime.now()))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_exercise(self, exercise_id):
        self.cursor.execute('SELECT * FROM exercises WHERE id = ?', (exercise_id,))
        return self.cursor.fetchone()

    def get_llm_interaction(self, interaction_id):
        self.cursor.execute('SELECT * FROM llm_interactions WHERE id = ?', (interaction_id,))
        return self.cursor.fetchone()


# Usage example
if __name__ == "__main__":
    db_service = SQLiteService('your_database.db')
    db_service.connect()
    db_service.create_tables()

    # Insert an exercise
    exercise_id = db_service.insert_exercise(
        age=8,
        difficulty="medium",
        scenario="space adventure",
        character="Astro the Space Dog",
        exercise="If Astro collects 5 moon rocks on Monday and 7 on Tuesday, how many rocks does he have in total?",
        answer="12"
    )
    print(f"Inserted exercise with ID: {exercise_id}")

    # Insert an LLM interaction
    interaction_id = db_service.insert_llm_interaction(
        input_data={"prompt": "Generate a space adventure for kids"},
        output_data={"story": "Astro the Space Dog embarked on an exciting journey..."},
        model="GPT-3.5-turbo"
    )
    print(f"Inserted LLM interaction with ID: {interaction_id}")

    db_service.disconnect()