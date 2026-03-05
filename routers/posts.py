from fastapi.responses import FileResponse
from fastapi import APIRouter, Request
import psycopg2
import uuid
import os
import psycopg2
from config import *

router = APIRouter()

@router.post('/description')
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

@router.get('/get_description')
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
@router.get('/get_description{filename}')  
async def get_image(filename: str):
    try:
        image_dir = '/home/malsi/my_global/iosprojectapi/static/post_images'

        file_path = os.path.join(image_dir, filename)
        return FileResponse(file_path, media_type='image/jpeg')
    except:
        print('ошибка')



