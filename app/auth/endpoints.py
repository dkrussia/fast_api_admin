import uuid
from starlette import status
from datetime import timedelta, datetime

from sqlalchemy.orm.exc import NoResultFound
from fastapi_sqlalchemy import db

from fastapi import APIRouter, Request, HTTPException, Depends, Response

from app.auth.crud.user_token import create_access_token, authenticate_user, get_current_user, create_session
from app.auth.models import User, UserSession
from app.auth.schema import UserLogin, UserData, RefreshTokenData
from core.config import settings

auth_router = APIRouter()


@auth_router.post("/login")
def login(login_data: UserLogin, request: Request, response: Response):
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # TODO: Проверить сколько у пользователя активных сессий. Если больше 10 - удалять.

    refresh_token = create_session(user, request, request_data=login_data)
    # response.set_cookie("refreshToken", refresh_token, max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES, path='/auth',
    #                      httponly=True, samesite='None')

    access_token = create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}


@auth_router.post("/refresh_tokens")
def refresh_tokens(request: Request, refresh_data: RefreshTokenData, response: Response):
    # refresh_token = request.cookies.get('refreshToken')
    refresh_token = refresh_data.refresh_token

    if not refresh_token:
        print(1)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MISSED REFRESH TOKEN",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        session = db.session.query(UserSession).filter_by(refresh_token=refresh_token).one()
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MISSED SESSION",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = session.user
    db.session.delete(session)
    db.session.commit()

    if session.fingerprint != refresh_data.fingerprint:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_FINGER_PRINT",
            headers={"WWW-Authenticate": "Bearer"},

        )

    if session.expires_in < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TOKEN_EXPIRED",
            headers={"WWW-Authenticate": "Bearer"},
        )


    refresh_token = create_session(user, request, request_data=refresh_data)
    response.set_cookie("refreshToken", refresh_token, max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES, path='/auth',
                        httponly=True)
    
    access_token = create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}


@auth_router.post("/logout")
def logout(request: Request):
    refresh_token = request.cookies.get('refreshToken')
    try:
        session = db.session.query(UserSession).filter_by(refresh_token=refresh_token).one()
        db.session.delete(session)
        db.session.commit()
    except NoResultFound:
        pass
    return Response(status_code=204)


@auth_router.get("/user")
def user(current_user: User = Depends(get_current_user)):
    return UserData.from_orm(current_user)
