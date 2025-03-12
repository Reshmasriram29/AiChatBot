from fastapi import HTTPException
from service import authenticate_user, register_user, process_rag_request
from service import LoginRequest, SignupRequest, UserRequest

def login_user(login_request: LoginRequest):
    try:
        session_id = authenticate_user(login_request.email, login_request.password)
        return {"message": "Login successful", "session_id": session_id}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def signup_user(signup_request: SignupRequest):
    try:
        response = register_user(signup_request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def rag_request(user_request: UserRequest):
    try:
        response = process_rag_request(user_request)
        return response
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
