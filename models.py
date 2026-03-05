from pydantic import BaseModel

class NewUsers(BaseModel): 
    firstName: str
    lastName: str
    email: str
    password: str

class LogUsers(BaseModel):
    email: str
    password: str 

class Message(BaseModel):
    id: int
    chat_id: int
    message: str
