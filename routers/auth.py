from fastapi import APIRouter, HTTPException
from models import NewUsers, LogUsers
import bcrypt
import psycopg2
from config import BD_HOST, BD_NAME, BD_PASSWORD, BD_USER, SECRET_KEY, ALGORITM
from datetime import datetime, timedelta, timezone
import jwt


router = APIRouter()

@router.post('/users')
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
@router.post('/users_log')
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