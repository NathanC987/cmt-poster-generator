# CMT Poster Generator

An automated FastAPI service that generates professional event posters for CMT Association meetings using Azure OpenAI for text processing, WordPress for media management, and intelligent layout algorithms.

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Configuration](#configuration)
4. [Deployment](#deployment)
5. [API Reference](#api-reference)
6. [Troubleshooting](#troubleshooting)

## Project Overview

### What It Does
Transforms structured event data (JSON) into professional, branded posters automatically:
- Processes event details through Azure OpenAI for intelligent text formatting
- Retrieves relevant images from WordPress media library
- Generates dynamic layouts based on speaker count (1-4 speakers)
- Uploads completed posters to WordPress and returns URLs

### Key Features
- **Automation**: Eliminates manual poster design work
- **Consistency**: Maintains CMT branding across all events
- **Integration**: Works with Power Automate workflows
- **Scalability**: Handles events with varying speaker counts
- **Intelligence**: AI-powered text summarization and formatting

## System Architecture

### High-Level Architecture

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   Power Automate    │────│   FastAPI Service    │────│     WordPress       │
│   (Event Trigger)   │    │  (Poster Generator)  │    │   (Media Storage)   │
│                     │    │                      │    │                     │
│ • Meeting Creation  │    │ • Content Processing │    │ • Image Library     │
│ • Data Collection   │    │ • Layout Generation  │    │ • Poster Upload     │
│ • API Calls         │    │ • Error Handling     │    │ • Media Search      │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
                                      │                           
                                      │                           
                           ┌──────────────────────┐               
                           │    Azure OpenAI      │               
                           │  (Text Processing)   │               
                           │                      │               
                           │ • Content Summary    │               
                           │ • Speaker Extraction │               
                           │ • Venue Processing   │               
                           │ • Text Formatting    │               
                           └──────────────────────┘               
                                      │                           
                                      │                           
                           ┌──────────────────────┐               
                           │   Upstash Redis      │               
                           │  (Rate Limiting)     │               
                           │                      │               
                           │ • IP-based Limits    │               
                           │ • Request Throttling │               
                           │ • DDoS Protection    │               
                           └──────────────────────┘               
```

### Technology Stack
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI | REST API server with async support |
| **AI Processing** | Azure OpenAI | Text formatting and summarization |
| **Image Processing** | Python Pillow | Poster composition and layout |
| **Media Storage** | WordPress REST API | Image library and poster uploads |
| **Rate Limiting** | Upstash Redis | Request throttling protection |
| **Deployment** | Render.com | Cloud hosting with auto-scaling |

### Data Flow Process

1. **Input Stage**: Power Automate sends event JSON to `/generate-posters` endpoint
2. **Processing Stage**: 
   - Rate limiter validates request frequency
   - OpenAI processes text content for formatting and summarization
   - WordPress media search retrieves relevant images
3. **Generation Stage**: 
   - Pillow library composes poster with dynamic layout
   - Text wrapping and image positioning algorithms apply
4. **Output Stage**: 
   - Generated poster uploads to WordPress
   - API returns poster URL to Power Automate

### Project Structure
```
app/
├── main.py                    # FastAPI application entry
├── api/poster.py             # POST /generate-posters endpoint
├── core/
│   ├── config.py            # Environment variables
│   └── rate_limiter.py      # Upstash Redis rate limiting
├── services/
│   ├── openai_service.py    # Azure OpenAI integration
│   ├── wordpress_service.py # WordPress media operations
│   └── image_service.py     # Image processing utilities
├── poster/generator.py       # Core poster generation logic
└── fonts/                    # CMT brand typography
```

## Configuration

### Required Environment Variables
| Variable | Purpose | Example |
|----------|---------|---------|
| `AZURE_OPENAI_ENDPOINT` | AI service URL | `https://resource.openai.azure.com/...` |
| `AZURE_OPENAI_API_KEY` | AI authentication | `your_api_key` |
| `WORDPRESS_URL` | Media storage | `https://cmtpl.org` |
| `WORDPRESS_USERNAME` | WP login email | `admin@cmtpl.org` |
| `WORDPRESS_PASSWORD` | WP app password | `abcd efgh ijkl mnop` |
| `UPSTASH_REDIS_URL` | Rate limiting | `https://db.upstash.io` |
| `UPSTASH_REDIS_TOKEN` | Redis auth | `your_token` |

### WordPress Media Requirements
- **Landmark Images**: Named as "city-country" (e.g., "singapore-singapore")
- **Overlay Image**: Named "overlay" for branding
- **Speaker Photos**: Named exactly as speaker names
- **Icons**: "date", "time", "venue", "register" icons

### Local Development Setup
```bash
# Clone repository
git clone https://github.com/cmt-poster-generator/cmt-poster-generator.git
cd cmt-poster-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (create .env file)
# Run server
uvicorn app.main:app --reload
```

## Deployment

### Render.com (Production)
1. **Setup**: Connect GitHub repository to Render.com
2. **Configuration**:
   - Environment: Python 3
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. **Environment Variables**: Set all variables from Configuration section
4. **Deploy**: Auto-deploys on push to main branch

## API Reference

### POST /generate-posters
**Purpose**: Generate poster from event data  
**Rate Limit**: 1 request/minute per IP

**Request Body**:
```json
{
  "title": "Event Title (required)",
  "date": "Event date (required)", 
  "time": "Event time (required)",
  "venue": "Event location (required)",
  "description": "Event description (required)",
  "speakers": ["Speaker 1", "Speaker 2"] // optional
}
```

**Response**:
```json
{
  "poster_urls": ["https://cmtpl.org/wp-content/uploads/.../poster.png"]
}
```

### GET /health
**Purpose**: Service health check  
**Response**: `{"status": "ok"}`

### Testing
```bash
# Production testing
curl -X POST "https://cmt-poster-generator.onrender.com/generate-posters" \
  -H "Content-Type: application/json" \
  --data-binary "@test_payload.json"
```

## Troubleshooting

### Common Issues
1. **Poster Generation Fails**: Check environment variables and service connectivity
2. **Rate Limiting**: Requests limited to 1/minute per IP
3. **Missing Images**: Verify WordPress media library has required assets
4. **Deployment Issues**: Check Render logs for build/startup errors

### Debug Steps
```bash
# Check environment
echo $AZURE_OPENAI_ENDPOINT
echo $WORDPRESS_URL

# Test services
curl "$WORDPRESS_URL/wp-json/wp/v2/"
curl https://your-service.onrender.com/health
```

### Performance
- Typical generation time: 15-30 seconds
- Memory requirement: 512MB minimum
- Rate limiting: 1 request/minute per IP

---

**CMT Poster Generator** - Automated poster generation for CMT Association events  
*Built with FastAPI, Azure OpenAI, and WordPress REST API*  
*Deployed on Render.com with auto-scaling*
