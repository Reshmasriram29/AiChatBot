from pydantic import BaseModel, EmailStr, constr
from repository import check_user, generate_session_id, save_new_user, session_validation, vectorize_question, get_medicine_vector, compose_prompt, llm_generator

class LoginRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=15)

class SignupRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=15)
    full_name: str

class UserRequest(BaseModel):
    question: str
    session_id: str

def authenticate_user(email: EmailStr, password: str) -> str:
    try:
        if check_user(email, password):
            return generate_session_id(email, password)
        else:
            raise ValueError("Invalid login credentials")
    except Exception as e:
        raise ValueError(f"Error during authentication: {str(e)}")

def register_user(signup_request: SignupRequest):
    try:
        if check_user(signup_request.email, signup_request.password):
            raise ValueError("User already exists. Please log in.")

        save_new_user(signup_request.email, signup_request.password, signup_request.full_name)
        session_id = generate_session_id(signup_request.email, signup_request.password)
        return {"message": "Signup successful", "session_id": session_id}
    except Exception as e:
        raise ValueError(f"Error during registration: {str(e)}")

def process_rag_request(user_request: UserRequest):
    try:
        if not session_validation(user_request.session_id):
            raise ValueError("Unauthorized")

        question_vector = vectorize_question(user_request.question)
        records = get_medicine_vector(question_vector)

        if records:
            output = compose_prompt(user_request.question, records)
            return llm_generator(output)
        else:
            raise ValueError("No relevant data found")
    except Exception as e:
        raise ValueError(str(e))
