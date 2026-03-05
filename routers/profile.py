from fastapi.responses import FileResponse
from fastapi import APIRouter,  Query, HTTPException, Form, UploadFile, File
import psycopg2
import uuid
import os
import psycopg2
from config import *

router = APIRouter()

#передача фотографии и данных пользвателя 

@router.get('/profile_inf')
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
        


@router.get("/profile_image_get")
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

@router.post("/profile_image")
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