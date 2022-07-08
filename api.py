import json
import logging
from datetime import timedelta, datetime
from asyncpg import UniqueViolationError
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette.background import BackgroundTasks
from starlette.middleware.cors import CORSMiddleware
import aioredis
import models
from auth import get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY, pwd_context
from blockchain import register_user_on_blockchain
from database import database, users
from jose import jwt

logging.getLogger().setLevel(logging.DEBUG)

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await database.connect()
    app.state.redis = aioredis.from_url("redis://redis", password="CB8wRre4kHotGBDvUsxlf")


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/get_current_user")
async def get_current_user(current_user=Depends(get_current_user)):
    return models.User(id=current_user.id, username=current_user.username, email=current_user.email)


@app.get("/get_user")
async def get_user():
    if cache := await app.state.redis.get('user_cache'):
        return {'data': json.loads(cache), 'cached': True}

    user_info = await database.fetch_all(users.select())

    await app.state.redis.set('user_cache', json.dumps([dict(x) for x in user_info]))

    return {'data': user_info, 'cached': False}


@app.post("/create_user")
async def create_user(user_info: models.UserCreationModel, background_tasks: BackgroundTasks):

    query = users.insert().values(username=user_info.username,
                                  email=user_info.email,
                                  password_hash=pwd_context.hash(user_info.password),
                                  is_banned=False)
    try:
        new_user_id = await database.execute(query)
    except UniqueViolationError:
        return HTTPException(status_code=409, detail="Username is taken")

    await app.state.redis.delete('user_cache')
    background_tasks.add_task(register_user_on_blockchain, new_user_id, user_info.username)

    return {"id": new_user_id}


@app.post("/token")
async def token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_info = await database.fetch_one(users.select().where(users.c.username == form_data.username))
    if not user_info:
        raise HTTPException(status_code=400, detail="User doesn't exists")

    if not pwd_context.verify(form_data.password, user_info.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode(
        {"sub": user_info.username, "exp": datetime.utcnow() + access_token_expires},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/update_user")
async def update_user(user_info: models.UserUpdateModel, current_user=Depends(get_current_user)):
    query = users.update().where(users.c.id == current_user.id).values(
        **(
            {'email': user_info.email} if user_info.email else {} |
            {'password_hash': pwd_context.hash(user_info.password)} if user_info.password else {}
        )
    )

    await database.execute(query)

    await app.state.redis.delete('user_cache')

    new_user = await database.fetch_one(users.select().where(users.c.id == current_user.id))
    return models.User(id=new_user.id, username=new_user.username, email=new_user.email)
