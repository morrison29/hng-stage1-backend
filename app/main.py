from itertools import count

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from uuid6 import uuid7

from .utils import get_age_group
from .services.external_apis import fetch_data_from_external_api
from .schemas import CreateProfile
from .models import Profile
from .database import Base, engine, get_db

app = FastAPI()
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}

@app.post("/api/profiles/", status_code=201)
async def create_profile(payload: CreateProfile, db: Session = Depends(get_db)):
    name = payload.name.strip().lower()
    if name.isdigit():
        raise HTTPException(status_code=422, detail="Name cannot be a number")

    if not name:
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    
    existing_name = db.query(Profile).filter(Profile.name == name).first()
    if existing_name:
        return {
            "status": "success",
            "message": "Profile already exists",
            "data": {
                "id": existing_name.id,
                "name": existing_name.name,
                "gender": existing_name.gender,
                "gender_probability": existing_name.gender_probability,
                "sample_size": existing_name.sample_size,
                "age": existing_name.age,
                "age_group": existing_name.age_group,
                "country_id": existing_name.country_id,
                "country_probability": existing_name.country_probability,
                "created_at": existing_name.created_at.isoformat() + "Z"
            }
        }
    
    gender_data, age_data, nation_data = await fetch_data_from_external_api(name)

    if gender_data['gender'] is None or gender_data['count'] == 0:
        return JSONResponse(
            status_code=502,
            content={
                "status": "error",
                "message": "Genderize returned an invalid response"
            }
        )
    
    if age_data['age'] is None or age_data['count'] == 0:
        return JSONResponse(
            status_code=502,
            content={
                "status": "error",
                "message": "Agify returned an invalid response"
            }
        )

    if not nation_data['country']:
        return JSONResponse(
            status_code=502,
            content={
                "status": "error",
                "message": "Nationalize returned an invalid response"
            }
        )

    top_country = max(nation_data['country'], key=lambda x: x['probability'])

    profile = Profile(
        id = str(uuid7()),
        name = name,
        gender = gender_data['gender'],
        gender_probability = gender_data['probability'],
        sample_size = gender_data['count'],
        age = age_data['age'],  
        age_group = get_age_group(age_data['age']),
        country_id = top_country['country_id'],
        country_probability = top_country['probability'],
        created_at = datetime.utcnow()
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return JSONResponse(
        status_code=201,
        content={
            "status": "success",
            "data": {
                "id": profile.id,
                "name": profile.name,
                "gender": profile.gender,
                "gender_probability": profile.gender_probability,
                "sample_size": profile.sample_size,
                "age": profile.age,
                "age_group": profile.age_group,
                "country_id": profile.country_id,
                "country_probability": profile.country_probability,
                "created_at": profile.created_at.isoformat() + "Z"
            }
        }
    )

@app.get("/api/profiles/{id}", status_code=200)
def get_profile(id: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == id).first()
    if not profile:
        raise HTTPException(status_code=404, detail={"status": "error", "message": "Profile not found"})

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "data": {
                "id": profile.id,
                "name": profile.name,
                "gender": profile.gender,
                "gender_probability": profile.gender_probability,
                "sample_size": profile.sample_size,
                "age": profile.age,
                "age_group": profile.age_group,
                "country_id": profile.country_id,
                "country_probability": profile.country_probability,
                "created_at": profile.created_at.isoformat() + "Z"
            }
        }
    )




@app.get("/api/profiles/")
def get_profiles(
    gender: str = Query(None),
    age_group: str = Query(None),
    country_id: str = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Profile)
    if gender:
        query = query.filter(func.lower(Profile.gender) == gender.lower())
    if age_group:
        query = query.filter(func.lower(Profile.age_group) == age_group.lower())    
    if country_id:
        query = query.filter(func.lower(Profile.country_id) == country_id.lower())

    profiles = query.all()
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "count": len(profiles),
            "data": [
                {
                    "id": profile.id,
                    "name": profile.name,
                    "gender": profile.gender,
                    "age": profile.age,
                    "age_group": profile.age_group,
                    "country_id": profile.country_id,
                }
                for profile in profiles
            ]
        }
    )

@app.delete("/api/profiles/{id}", status_code=204)
def delete_profile(id: str, db: Session = Depends(get_db)):

    if not id:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "ID parameter is required"
            }
        )
    
    if not isinstance(id, str):
        raise HTTPException(
            status_code=422,
            detail={
                "status": "error",
                "message": "ID must be a string"
            }
        )
    profile = db.query(Profile).filter(Profile.id == id).first()

    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "message": "Profile not found"
            }
        )
    
    #server error handling for database issues
    try:
        db.delete(profile)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "An error occurred while deleting the profile"
            }
        ) from e
    return Response(status_code=204)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    for error in errors:
        if error['loc'][-1] == 'name':
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Name field is required and must be a string"
                }
            )
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Invalid input"
        }
    )

from fastapi import HTTPException

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):

    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail
        }
    )