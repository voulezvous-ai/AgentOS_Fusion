
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.core.security import authenticate_user, create_access_token, CurrentUser
from app.main import limiter

router = APIRouter()

@router.post("/login", dependencies=[Depends(limiter.limit("10/minute"))])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais incorretas")
    access_token = create_access_token(data={"sub": user["username"]}, expires_delta=timedelta(minutes=60))
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
async def read_me(current_user: dict = Depends(CurrentUser())):
    return current_user
