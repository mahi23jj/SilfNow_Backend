# Talk Gym Backend

Professional FastAPI project scaffold with clear layering for scaling features.

## Project Structure

```
Talk_Gym_Backend/
├── app/
│   ├── api/
│   │   ├── router.py
│   │   └── v1/
│   │       └── endpoints/
│   │           └── health.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── tests/
│   └── test_health.py
└── README.md
```

## Run Locally

1. Install dependencies:

	```bash
	pip install -r requirements.txt
	```

2. Start the API:

	```bash
	uvicorn main:app --reload
	```

3. Open docs:

	- Swagger UI: `http://127.0.0.1:8000/docs`
	- ReDoc: `http://127.0.0.1:8000/redoc`

## Environment Variables

Optional `.env` keys:

- `APP_NAME`
- `APP_VERSION`
- `API_V1_PREFIX`
- `POSTGRES_URL` (or legacy `postgres_url`)

## Next Development Pattern

- Add request/response schemas in `app/schemas/`
- Add domain models in `app/models/`
- Keep business logic in `app/services/`
- Keep route handlers thin in `app/api/v1/endpoints/`
