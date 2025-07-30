# CMT Poster Generator

A FastAPI-based service to automatically generate event posters for CMT Association meetings. It integrates with WordPress for media storage, Azure OpenAI for text processing, and Upstash Redis for rate limiting.

## Features
- Receives meeting/event details as JSON
- Uses OpenAI to format and summarize text, extract speaker info, and determine landmark images
- Fetches images (landmarks, overlays, speaker photos) from WordPress media
- Generates a dynamic, portrait poster using Pillow
- Uploads the generated poster to WordPress media
- Rate limiting via Upstash Redis

## Project Structure
```
cmt-poster-generator/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   └── poster.py
│   ├── core/
│   │   ├── config.py
│   │   ├── rate_limiter.py
│   │   └── utils.py
│   ├── services/
│   │   ├── openai_service.py
│   │   ├── wordpress_service.py
│   │   └── image_service.py
│   ├── poster/
│   │   ├── __init__.py
│   │   └── generator.py
│   └── fonts/
│       ├── GlacialIndifference-Regular.ttf
│       └── GlacialIndifference-Bold.ttf
│
├── requirements.txt
└── README.md
```

## Setup
1. Place the Glacial Indifference font files in `app/fonts/`.
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set environment variables as required (see Render setup).
4. Run the app locally:
   ```sh
   uvicorn app.main:app --reload
   ```

## API
- `POST /generate-posters/` — Accepts event JSON and returns poster URLs.
- `GET /health` — Health check endpoint.

## Extending
- Add new image/text providers by extending the `services/` modules.
- Add new poster templates in `poster/generator.py`.
