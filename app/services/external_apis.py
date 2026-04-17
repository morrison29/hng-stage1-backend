import httpx
from fastapi import HTTPException

async def fetch_data_from_external_api(name: str):
    try:
        async with httpx.AsyncClient() as client:
            gender = await client.get(f"https://api.genderize.io?name={name}")
            age = await client.get(f"https://api.agify.io?name={name}")
            country = await client.get(f"https://api.nationalize.io?name={name}")

        responses = [
            (gender, "Genderize"),
            (age, "Agify"),
            (country, "Nationalize"),
        ]
        for response, label in responses:
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail=f"{label} returned an invalid response")

        return gender.json(), age.json(), country.json()
    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=str(exc))