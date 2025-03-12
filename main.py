from fastapi import FastAPI
from controller import login_user, signup_user, rag_request
from service import LoginRequest, SignupRequest, UserRequest

app = FastAPI()

@app.post("/login")
def login(login_request: LoginRequest):
    return login_user(login_request)

@app.post("/signup")
def signup(signup_request: SignupRequest):
    return signup_user(signup_request)

@app.post("/rag")
def rag(user_request: UserRequest):
    return rag_request(user_request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
