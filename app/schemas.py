from pydantic import BaseModel

class CreateProfile(BaseModel):
    name: str
   