from fastapi import APIRouter, Query, BackgroundTasks
from models import Message
from fastapi import  HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from config import BD_HOST, BD_NAME, BD_PASSWORD, BD_USER
from pika import ConnectionParameters, BlockingConnection

router = APIRouter()

@router.post('/postchat')
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





@router.get('/messages/{chat_id}')
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
        raise HTTPException(status_code=500, detail=f"Ошибка  БД: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()





@router.post('/postmessage')
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



@router.get('/getchat/{id}')
def getchat(id: int):  # ← int!
    connect = None
    cursor = None
    try:
        connect = psycopg2.connect(
            host=BD_HOST, 
            database=BD_NAME, 
            user=BD_USER, 
            password=BD_PASSWORD
        )
        cursor = connect.cursor()

        # Добавили GROUP BY для уникальных собеседников
        cursor.execute('''
            SELECT cu2.user_id, ui2.fname, ui2.lname, ui2.profile_image
            FROM chat_users cu1
            JOIN chat_users cu2 ON cu1.chat_id = cu2.chat_id
            JOIN users_information ui2 ON cu2.user_id = ui2.id
            WHERE cu1.user_id = %s 
            AND cu2.user_id != %s;
        ''', (id, id))

        content = cursor.fetchall()  # → [(42,), (43,)]
        
        # Правильное преобразование в dict
        result = []

        for i in content:
            result.append({
                'id' : i[0],
                'lname' : i[1],
                'fname': i[2],
                'profile_image' :i[3]
            })
        
        print(f"Найдено собеседников для {id}: {result}")
        return {'message' : result}
        
    except Exception as e:
        print(f'Ошибка: {e}')
        return {'error': 'Не удалось получить чаты'}
    finally:
        if cursor:
            cursor.close()
        if connect:
            connect.close()

@router.get('/serch_users')
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
        

#делаем отправку сообщений консюмеру с помощью рабит



connection_params = ConnectionParameters(
    host='localhost',
    port=5672,
)

def main(message: str):
    with BlockingConnection(connection_params) as conn:
        with conn.channel() as ch:
            ch.queue_declare(queue='mess')

            ch.basic_publish(
                exchange='',
                routing_key='mess',
                body=message
            )
            print('message')


if __name__ == '__main__':
    main()
