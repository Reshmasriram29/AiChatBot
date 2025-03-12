import random
import psycopg2
from langchain_openai import AzureOpenAIEmbeddings
from openai import AzureOpenAI
import os
from database import get_db_connection
from dotenv import load_dotenv

load_dotenv()

def check_user(email: str, password: str) -> bool:
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT email, password FROM users WHERE email = %s", (email,))
        record = cursor.fetchone()
        return record and record[1] == password
    finally:
        cursor.close()
        connection.close()

def save_new_user(email: str, password: str, full_name: str):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO users (email, password, full_name) VALUES (%s, %s, %s)", 
                       (email, password, full_name))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def generate_session_id(email, password) -> str:
    session_id = str(random.random()).split('.')[1]
    with open('tokens.txt', 'a') as file:
        file.write(f"{email}:{session_id}\n")
    return session_id

def session_validation(session_id: str):
    try:
        with open('tokens.txt', 'r') as file:
            tokens = file.readlines()
            return any(session_id == line.strip().split(":")[1] for line in tokens)
    except Exception:
        return False
# Function to vectorize the question using OpenAI embeddings
def vectorize_question(question: str) -> list:
    try:
        embedding = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv('OPENAI_AZURE_EMD_ENDPOINT'),
            api_key=os.getenv('OPENAI_API_EMD_KEY'),
            api_version=os.getenv('OPENAI_EMD_VERSION'),
            azure_deployment=os.getenv('OPENAI_EMD_DEPLOYMENT')
        )
        response = embedding.embed_query(question) 
        return response
    except Exception as e:
        print(f"Error while creating embeddings: {e}")
        return []

# Database connection parameters
NAME = os.getenv("DB_NAME")
USER = os.getenv("DB_USER")
HOST = os.getenv("DB_HOST")
PASS = os.getenv("DB_PASS")

def get_medicine_vector(vector):
    try:
        connection = psycopg2.connect(f"postgresql://{USER}:{PASS}@{HOST}/{NAME}")
        cursor = connection.cursor()

        similarity_query = """
        SELECT description 
        FROM reshma.medicine
        ORDER BY descriptionvector <=> %s::vector
        LIMIT 3
        """
        cursor.execute(similarity_query, (vector,))
        result = cursor.fetchall()
        return result if result else []
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def generate_prompt(question_vector):
    medicine_data = get_medicine_vector(question_vector)
    return medicine_data if medicine_data else []

def compose_prompt(question, medicine_data):
    prompt = [
        {
            "role": "system",
            "content": 
            """
            hashtag#Role:
            You are a medical prescription guidance application.

            hashtag#Objective:
            You need to generate info about the medical prescription or general medicine queries.

            hashtag#Input Structure:
            user send the question as a string and medicine_data has list of string 

            hashtag#Rules:
            **User will be giving a medical prescription or asking questions about medicine.
            **If the user's question or prescription is not related to medical topics, return an invalid question.
            **You need to generate the content only from the user medicine_data; do not generate anything beyond that.
            **If it's a prescription, give detailed information about it one by one.
            **If the response is empty or not relevant to the context, use SerpAPI for more information.

            hashtag#Constraints:
            Strictly provide the response in JSON format. The response should be compatible with the json.loads() method.

            hashtag#Output Structure:
            Return a JSON object. One key should be "question" with the value being the user's question. 
            Another key should be "medicineData" with the value being the recommended medicine. 
            If none of the provided medicine match the user's question, set the value of the "medicineData" key to an empty string.
            """
        },
        {
            "role": "user",
            "content": f"{[question, medicine_data]}"
        }
    ]
    return prompt

def llm_generator(prompt):
    try:
        client = AzureOpenAI(
            azure_endpoint=os.getenv("OPENAI_AZURE_ENDPOINT"),
            api_key=os.getenv("OPENAI_API_KEY"),
            api_version=os.getenv("OPENAI_API_VERSION")  # Fixed incorrect env var
        )
        chat_completion = client.chat.completions.create(
            messages=prompt,
            model=os.getenv("OPENAI_MODEL"),
            response_format={"type": "json_object"}
        )
        response = chat_completion.choices[0].message.content
        dictResponse = json.loads(response)  # Ensure valid JSON response
        return dictResponse
    except Exception as e:
        return str(e)

async def SERAPI(question):
    try:
        os.environ['SERPER_API_KEY'] = os.getenv('SERPER_API_KEY')
        search = GoogleSerperAPIWrapper(type="search")
        response = search.run(question)
        return response
    except Exception as e:
        return f"Error while searching with SERPER API: {e}"
