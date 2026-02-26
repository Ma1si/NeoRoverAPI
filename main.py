from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Form, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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
from fastapi.staticfiles import StaticFiles



app = FastAPI()
# ВАЖНО: замените обработчик ошибок
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Неверный формат файла",
            "details": [f"{err['loc']}: {err['msg']}" for err in exc.errors()]
        }
    )

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


class Message(BaseModel):
    id : int
    chat_id : int
    message: str



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
        insert_query = "INSERT INTO users (lname, fname, email, password_user) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_query, (new_users.lastName, new_users.firstName, new_users.email, hashed_password,))
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
        
        if isinstance(user_password[0], bytes):
            user_password_byte = user_password[0]
            print('1')
        elif isinstance(user_password[0], str) and user_password[0].startswith('\\x'):
            user_password_byte = bytes.fromhex(user_password[0][2:])

        else:
            user_password_byte = user_password[0].encode('utf-8')
        
        if bcrypt.checkpw(pass_byte, user_password_byte):
            print('пароль верный')

            pyload = {
                "sub" : user_password[1],
                "name" : user_password[2],
                "iat" : datetime.now(timezone.utc),
                "exp" : datetime.now(timezone.utc) + timedelta(hours=24)
            }
            
            token = jwt.encode(pyload, SECRET_KEY, algorithm=ALGORITM)

            return {"success": True, "token": token, "user_id": user_password[1]} 
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


#передача фотографии и данных пользвателя 

@app.get('/profile_inf')
def profile_inf(id: int = Query(..., ge=1)):
    try:
        connect = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)
        cursor = connect.cursor()

        cursor.execute("select lname, fname from users_information where id = %s", (id,))
        content = cursor.fetchone()

        print(content[1])

        connect.close()
        return {'lname' : content[0], 'fname' : content[1]}
    except:
        print('errorr')
        


@app.get("/profile_image_get")
def profimaget(id: int = Query(..., ge=1)):
    try:
        connect = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)
        cursor = connect.cursor()

        cursor.execute('select profile_image from users_information where id = %s', (id,))

        content = cursor.fetchone()[0]
        connect.close()

        image_dir = '/home/malsi/my_global/iosprojectapi/static/images'
        file_path = os.path.join(image_dir, content)

        return FileResponse(file_path, media_type='image/jpeg')

    except:
        print('')

@app.post("/profile_image")
async def profimage(id: str = Form(...), file: UploadFile = File(...)):
    try:
        user_id = int(id)
        # Проверка типа файла
        if not file.content_type.startswith('image/'):
            raise HTTPException(422, "Файл должен быть изображением")
        
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(422, "Пустой файл")

        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'jpg'
        filename = f'{uuid.uuid4()}.{file_extension}'

        upload_dir = 'static/images'
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(content)

        # Обновление БД
        connect = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)
        cursor = connect.cursor()
        cursor.execute('UPDATE users_information SET profile_image = %s WHERE user_id = %s', (filename, user_id))
        
        updated = cursor.rowcount
        connect.commit()
        connect.close()
        
        if updated == 0:
            raise HTTPException(404, "Пользователь не найден")
            
        return {"message": "Изображение загружено", "filename": filename}
        
    except ValueError:
        raise HTTPException(422, "Неверный ID пользователя")
    except Exception:
        raise HTTPException(500, "Ошибка сервера")

#добавление постов в приложение 



@app.post('/description')
async def description(request: Request):
    try:
        form = await request.form()
        
        id_str = form.get('id')
        text = form.get('text')
        file = form.get('file')  
        
        
        if not all([id_str, text, file]):
            return {"error": "нет полей", "поля": list(form.keys())}
        
        user_id = int(id_str)
        

        if hasattr(file, 'read'):  
            content = await file.read()
            filename = file.filename if hasattr(file, 'filename') and file.filename else 'image.jpg'
        else:  
            content = file.encode() if isinstance(file, str) else file
            filename = 'image.jpg'
        
        file_extension = filename.split('.')[-1].lower() if '.' in filename else 'jpg'
        safe_filename = f'{uuid.uuid4()}.{file_extension}'

        upload_dir = 'static/post_images'
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, safe_filename)

        with open(file_path, 'wb') as f:
            f.write(content)
        
        # БД
        connect = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)
        cursor = connect.cursor()
        cursor.execute('INSERT INTO description (user_id, post_file, post_text) VALUES (%s, %s, %s)', 
                      (user_id, safe_filename, text))
        connect.commit()
        cursor.close()
        connect.close()
        
       
        return {"status": "success", "filename": safe_filename}
        
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        return {"status": "error", "message": str(e)}
    

#показ постов 

@app.get('/get_description')
def get_description():
    try:
        connect = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)
        cursor = connect.cursor()

        cursor.execute('select a.post_file, a.post_text, b.lname, b.fname ' \
                       'from description as a ' \
                       'inner join  users_information as b on a.user_id = b.id')
        conntent = cursor.fetchall()

        res = []

        

        for row in conntent:         
            res.append({
                'post_file' : row[0],
                'post_text' : row[1],
                'lname' : row[2],
                'fname': row[3]
            })

        connect.close()
        return {'data' : res}
    except:
        print('ошибка')
@app.get('/get_description{filename}')  
async def get_image(filename: str):
    try:
        image_dir = '/home/malsi/my_global/iosprojectapi/static/post_images'

        file_path = os.path.join(image_dir, filename)
        return FileResponse(file_path, media_type='image/jpeg')
    except:
        print('ошибка')
app.mount("/static", StaticFiles(directory="/home/malsi/my_global/iosprojectapi/static"), name="static")

#поиск пользователя по имени 

@app.get('/serch_users')
async def serch_users(query: str = Query(..., min_length=1, description='Имя или фамилия для поиска')):
    try:
        connect = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)
        cursor = connect.cursor()
        search_param = f"%{query}%"

        cursor.execute('select id, fname, lname, profile_image from users_information where lname ILIKE %s or fname ILIKE %s', (search_param, search_param))

        content = cursor.fetchall()

        users = [
            {
                'id' : row[0],
                'fname' : row[1],
                'lname' : row[2],
                'profile_image': row[3]

            }
            for row in content
        ]

        connect.close()
        cursor.close()
        return {'content': users}

    except:
        print('err')

#СОЗДАНИЕ ЧАТА

@app.post('/postchat')
def postchat(request: dict):
    id = int(request['id'])
    select_user_id = int(request['select_user_id'])
    try:
        connect = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)
        cursor = connect.cursor()
        print(0)

        cursor.execute('''
            SELECT c.id 
            FROM chats c
            JOIN chat_users cu1 ON c.id = cu1.chat_id
            JOIN chat_users cu2 ON c.id = cu2.chat_id 
            WHERE (cu1.user_id = %s AND cu2.user_id = %s)
            OR (cu1.user_id = %s AND cu2.user_id = %s)
            LIMIT 1
        ''', (id, select_user_id, select_user_id, id))
        
        result = cursor.fetchone()
        
        if result:  # ✅ Проверяем результат запроса
            chat_id = result[0]
            print(f"✅ Найден чат: {chat_id}")
            connect.commit()
            return {"status": "success", "chat_id": chat_id, "existing": True}

        
        cursor.execute('INSERT INTO chats DEFAULT VALUES RETURNING id')
        new_chat_id = cursor.fetchone()[0]

        cursor.execute('INSERT INTO chat_users (chat_id, user_id) VALUES (%s, %s)', (new_chat_id, id))
        cursor.execute('INSERT INTO chat_users (chat_id, user_id) VALUES (%s, %s)', (new_chat_id, select_user_id))

        connect.commit()
        print(1)
        return {"status": "success", "chat_id": new_chat_id, "existing": False}
    
    except:
        print('err')
    finally:
        if cursor:
            cursor.close()
        if connect:
            connect.close()



from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor

@app.get('/messages/{chat_id}')
async def get_messages(chat_id: int, limit: int = 50, user_id: int = 1):  # ✅ user_id из query
    conn = None
    cursor = None
    
    try:
        print(f"🔍 Запрос сообщений: chat_id={chat_id}, user_id={user_id}, limit={limit}")
        
        conn = psycopg2.connect(
            host=BD_HOST,
            database=BD_NAME,
            user=BD_USER,
            password=BD_PASSWORD,
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, content, user_id, sent_at,
                   CASE WHEN user_id = %s THEN true ELSE false END as is_me
            FROM messages 
            WHERE chat_id = %s
            ORDER BY sent_at DESC
            LIMIT %s
        """, (user_id, chat_id, limit))
        
        messages = cursor.fetchall()
        print(f"✅ Найдено сообщений: {len(messages)}")
        
        return {"messages": [dict(msg) for msg in messages]}  # ✅ Явное преобразование
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()





@app.post('/postmessage')
def postmessage(messagedata : Message):


    try:
        connect = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)
        cursor = connect.cursor()

        cursor.execute('INSERT INTO messages (user_id, chat_id, content) values (%s, %s, %s)', (messagedata.id, messagedata.chat_id, messagedata.message))
        connect.commit()
        return{"message": "success"}

    except:
        print('err')

    finally:
        if cursor:
            cursor.close()
        if connect:
            connect.close()

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)

