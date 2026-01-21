from fastapi import FastAPI
import uvicorn
import psycopg2
import bcrypt
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt

app = FastAPI()

SECRET_KEY = "fuzkz-z-nt,z-lj-cbp-gjh-k.,k.-dthybcm-rjvyt"
ALGORITM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

origins = [
    'http://localhost:8081/'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081",
                    "http://127.0.0.1:8081", 
                    "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BD_HOST = 'localhost'
BD_NAME = 'postgres'
BD_USER = 'postgres'
BD_PASSWORD = 'fubkz13love'

record = []



class NewUsers(BaseModel): 
    firstName: str
    lastName : str
    email : str
    password : str

class LogUsers(BaseModel):
    email : str
    password : str 

@app.get('/')
def root():
    return "hello world"

@app.get('/showusers')
def show_users():


    try: 
        connect = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)
        print('соединение установлено')

        cursor = connect.cursor()

        select_qyery = "SELECT user_id, lname, fname, email, password_user FROM users"
        cursor.execute(select_qyery)

        rows = cursor.fetchall()
        connect.close()
        return rows

    except:
        print("Ошибка")

#Добавление пользователя 
@app.post('/users')
def creat_users(new_users: NewUsers): 

    #подключение postgresql
    try:
        password_bytes = new_users.password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        user = (new_users.lastName, new_users.firstName, new_users.email, hashed_password)

        connection = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)
        print('соединение установлено')

        cursor = connection.cursor()

        cursor.execute("SELECT email FROM users WHERE email = %s", (new_users.email,))
        

        if cursor.fetchone():
            connection.close()
            return {
                "error" : "Эта почта уже зарегестрирована"
            }, 409
        

        insert_qyery = "INSERT INTO users (lname, fname, email, password_user) VALUES (%s, %s, %s, %s)"
    
        cursor.execute(insert_qyery, user)
        connection.commit()
        
        connection.close()
        
        return {"success" : True, "message" : "Пользователь добавлен"}, 201


    except (Exception, psycopg2.Error) as Error:
        print("ошибка", Error)
        if 'connection' in locals():
            connection.close() 
        return {"error": "Ошибка базы данных"}, 500
    
#Проверка логина
@app.post("/users_log")
def users_login(log_user : LogUsers):
    try: 
        connect = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)  
        cursor = connect.cursor()

        cursor.execute("SELECT user_id password_user from users WHERE email = %s", (log_user.email))

        data_user = cursor.fetchone()

        if data_user:
            user_id, stored_hash = data_user
            input_pass_bytes = log_user.password.encode('utf-8')

            if bcrypt.checkpw(input_pass_bytes, stored_hash):
                playload = {
                    "user_id": user_id,
                    "email": log_user.email,
                    "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                }
                token = jwt.encode(playload, SECRET_KEY, algorithm=ALGORITM)
                cursor.close()
                connect.close()
                return {
                    "message":"успешный вход",
                    "token": token,
                    "user_id": user_id,
                    "email": log_user
                }, 200
            else:
                cursor.close()
                connect.close()
                return {"message" : "Неверный пароль"}, 401
            
        connect.close()
        cursor.close()
        return {"message": "Пользователь не найден"}, 404

    except (Exception, psycopg2.Error) as Error:
        print(Error)
        if 'connect' in locals():
            connect.close()
        return {"error": "Ошибка базы данных"}, 500
if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
