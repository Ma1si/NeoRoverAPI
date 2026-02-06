from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import uvicorn
import psycopg2
import bcrypt
import uuid
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
from datetime import datetime, timedelta, timezone



app = FastAPI()

SECRET_KEY = "fuzkz-z-nt,z-lj-cbp-gjh-k.,k.-dthybcm-rjvyt"
ALGORITM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081",
                    "http://127.0.0.1:8081", 
                    "http://localhost:3000",
                    "*"],
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


#Добавление пользователя 
@app.post('/users')
def creat_users(new_users: NewUsers): 
    connect = None
    try:
        
        password_bytes = new_users.password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        connect = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)
        cursor = connect.cursor()

        # ✅ ПРАВИЛЬНАЯ проверка email
        cursor.execute("SELECT email FROM users WHERE email = %s", (new_users.email,))
        existing_user = cursor.fetchone()
        
        print(f"🔍 Пользователь существует: {bool(existing_user)}")  # Лог!
        
        if existing_user:  # ✅ Сохраняем результат сразу
            connect.close()
            raise HTTPException(status_code=409) 
        
        # Регистрация...
        insert_query = "INSERT INTO users (lname, fname, email, password_user, pass_byte) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (new_users.lastName, new_users.firstName, new_users.email, hashed_password, hashed_password))
        connect.commit()
        connect.close()
        
        return {"success": True, "message": "Пользователь добавлен"}, 201
    
    except HTTPException:
        raise

    except Exception as Error:
        print(f"Ошибка: {Error}")
        if connect:
            connect.close()
        return {"error": "Ошибка базы данных"}, 500


    
#Проверка логина
@app.post('/users_log')
def userlog(log_users: LogUsers):
    connect = None
    try:
        connect = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)
        cursor = connect.cursor()
        print('подключен')
        
        cursor.execute("SELECT password_user, user_id, email FROM users WHERE email = %s", (log_users.email,))
        user_password = cursor.fetchone()



        if not user_password[0]:
            raise HTTPException(status_code=401)


        pass_byte = log_users.password.encode('utf-8')
        user_password_byte = user_password[0][2:].encode('utf-8') 
        
        if isinstance(user_password[0], str) and user_password[0].startswith('\\x'):
            user_password_byte = bytes.fromhex(user_password[0][2:])  
        else:
            user_password_byte = user_password[0] 
        
        print(f"Пароль из БД: {user_password[0]}")
        print(f"Тип хеша: {type(user_password_byte)}")
        print(f"Введенный пароль: {pass_byte}")
        
        if bcrypt.checkpw(pass_byte, user_password_byte):
            print('пароль верный')

            pyload = {
                "sub" : user_password[1],
                "name" : user_password[2],
                "iat" : datetime.now(timezone.utc),
                "exp" : datetime.now(timezone.utc) + timedelta(hours=24)
            }
            
            token = jwt.encode(pyload, SECRET_KEY, algorithm=ALGORITM)

            return {"success": True, "token": token} 
        else:
            print('пароль не верный')
            raise HTTPException(status_code=401)
        
    except HTTPException:
        raise

    except Exception as e:
        print(f"ОШИБКА: {e}")  # ✅ Показываем реальную ошибку!
        raise HTTPException(status_code=401)
    
    finally:
        if connect:
            connect.close()  # ✅ Всегда закрываем соединение


#передача фотографии 

@app.post("/profile_image")
async def profimage(file: UploadFile = File(...)):
    try:
        content = await file.read()

        file_extension = file.filename.split('.')[-1]
        filename = f'{uuid.uuid4()}.{file_extension}'

        upload_dir = 'static/images'
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(content)

        connect = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)
        cursor = connect.cursor()
        cursor.execute('update users set profile_image = (%s) where user_id = 12', (filename,))

        connect.commit()
        connect.close()

    except:
        print('')

@app.get("/profile_image_get")
def profimaget():
    try:
        connect = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)
        cursor = connect.cursor()

        cursor.execute('select profile_image from users where user_id = 12')

        content = cursor.fetchone()[0]
        connect.close()

        image_dir = '/home/malsi/my_global/iosprojectapi/static/images'
        file_path = os.path.join(image_dir, content)

        return FileResponse(file_path, media_type='image/jpg')

    except:
        print('')


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)

