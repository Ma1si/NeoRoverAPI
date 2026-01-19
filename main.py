from fastapi import FastAPI
import uvicorn
import psycopg2
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

origins = [
    'http://localhost:8081/'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


record = []



class NewUsers(BaseModel): 
    lastName: str
    firstName : str
    email : str
    password : str

@app.get('/')
def root():
    return "hello world"

@app.get('/showusers')
def show_users():
    BD_HOST = 'localhost'
    BD_NAME = 'postgres'
    BD_USER = 'postgres'
    BD_PASSWORD = 'fubkz13love'

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


@app.post('/users')
def creat_users(new_users: NewUsers):

    global record
    record.clear()

 

    user = (new_users.lastName, new_users.firstName, new_users.email, new_users.password)

    #подключение postgresql
    BD_HOST = 'localhost'
    BD_NAME = 'postgres'
    BD_USER = 'postgres'
    BD_PASSWORD = 'fubkz13love'



    try:
        connection = psycopg2.connect(host=BD_HOST, database=BD_NAME, user=BD_USER, password=BD_PASSWORD)
        print('соединение установлено')

        cursor = connection.cursor()

        cursor.execute("SELECT email FROM users WHERE email = %s", (new_users.email,))
        sqlemail = cursor.fetchone()

        if sqlemail:
            connection.close()
            cursor.close()
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
        if 'connection' in locals():  # проверяем, что connection существует
            connection.close()       # ✅ СКОБКИ!
        return {"error": "Ошибка базы данных"}, 500

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)