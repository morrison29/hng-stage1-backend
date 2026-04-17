## Overview
# Backend Wizards Stage 1 – API

This project is a RESTful API that:

Accepts a name as input
Fetches data from three external APIs:
Gender prediction
Age estimation
Nationality prediction
Applies classification logic
Stores the processed data in a database
Exposes endpoints to manage and retrieve stored profiles.



## Base URL

https://your-api-url.com

---

## Repository

https://github.com/your-username/your-repo-name

---

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- HTTPX

---

## Endpoints

### Create Profile  
POST /api/profiles  
Creates a new profile from a name. If the name already exists, the existing profile is returned.

---

### Get Single Profile  
GET /api/profiles/{id}  
Returns a profile by its ID.

---

### Get All Profiles  
GET /api/profiles  
Returns all profiles.

Optional filters:
- gender
- country_id
- age_group  

Example: /api/profiles?gender=male&country_id=NG

---

### Delete Profile  
DELETE /api/profiles/{id}  
Deletes a profile.

---

## Logic

- Age groups:
  - 0–12 → child  
  - 13–19 → teenager  
  - 20–59 → adult  
  - 60+ → senior  

- Nationality:
  - Highest probability country is selected  

---

## Error Handling

All errors follow this format:

status: error  
message: description  

Status codes:
- 400 → Missing or empty name  
- 422 → Invalid input  
- 404 → Profile not found  
- 502 → External API error  

---

## Notes

- Names are unique (no duplicates stored)  
- IDs are UUID v7  
- Timestamps are in UTC format  
- CORS is enabled (*)  

---

## Run Locally

1. Clone the repository  
2. Create a virtual environment  
3. Install dependencies  
4. Run the server with uvicorn  

---

## API Docs

http://127.0.0.1:8000/docs