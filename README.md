# CMT Poster Generator API

AI-powered poster generation API for CMT Association events. This service automatically generates professional meeting posters with landmark backgrounds, speaker information, and event details.

## 🚀 Live API

**Production URL:** https://cmt-poster-generator.onrender.com

- **API Documentation:** https://cmt-poster-generator.onrender.com/docs
- **Health Check:** https://cmt-poster-generator.onrender.com/health

## 📋 Features

- **Multiple Poster Types:**
  - General overview posters (all speakers, event details)
  - Individual speaker-focused posters
  - Theme-focused promotional posters

- **AI-Powered Generation:**
  - Landmark image generation using Replicate Flux-Schnell
  - Text summarization with Azure OpenAI
  - Dynamic layout optimization

- **Production-Ready:**
  - Rate limiting with Upstash Redis
  - Cloud storage with Cloudflare R2
  - Comprehensive error handling
  - Service health monitoring

## 🏗️ Architecture

```
├── config/              # Configuration and settings
├── app/
│   ├── models/          # Pydantic request/response models
│   ├── services/        # Core business logic
│   │   ├── base_service.py
│   │   ├── replicate_service.py      # AI image generation
│   │   ├── azure_openai_service.py   # Text processing
│   │   ├── upstash_service.py        # Rate limiting
│   │   ├── cloudflare_r2_service.py  # Storage
│   │   ├── poster_composer.py        # Main composition engine
│   │   └── service_factory.py        # Service management
│   └── main.py          # FastAPI application
├── requirements.txt
└── README.md
```

## 🔧 Setup

### 1. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Required Services:**
- **Replicate API** (for landmark generation)
- **Azure OpenAI** (for text processing)
- **Upstash Redis** (for rate limiting)
- **Cloudflare R2** (for storage)

### 2. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload --port 8000
```

### 3. Production Deployment

**Render Deployment:**
1. Push code to GitHub
2. Connect repository to Render
3. Configure environment variables
4. Deploy automatically

## 📡 API Endpoints

### Main Endpoints

#### `POST /generate-posters`
Generate all poster types for an event.

**Request:**
```json
{
  "event_details": {
    "title": "CMT Mumbai Chapter Meeting",
    "description": "Technical analysis workshop with industry experts",
    "date": "2024-08-15T18:00:00",
    "venue": "Hotel Taj Mumbai",
    "city": "Mumbai",
    "country": "India",
    "theme": "Technical Analysis in Modern Markets"
  },
  "speakers": [
    {
      "name": "John Doe",
      "bio": "Senior Technical Analyst with 15 years experience",
      "title": "Senior Analyst",
      "organization": "Financial Corp",
      "photo_url": "https://example.com/photo.jpg"
    }
  ],
  "poster_types": ["general", "speaker", "theme"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully generated 3 posters",
  "event_id": "abc123def456",
  "posters": [
    {
      "poster_type": "general",
      "url": "https://storage-url/poster.png",
      "dimensions": {"width": 1200, "height": 1600},
      "file_size": 2048000,
      "format": "PNG"
    }
  ],
  "generation_time": 45.2,
  "cached_landmark": true
}
```

#### `POST /landmarks`
Generate landmark images for specific cities.

#### `POST /process-text`
Summarize and process text content.

#### `GET /health`
Service health check with dependency status.

## 🔄 Power Automate Integration

This API integrates with Microsoft Power Automate for the CMT meeting workflow:

### Integration Flow:
1. **Microsoft Form** submitted → **SharePoint List** created
2. **Power Automate** triggers when `EventStatus = "Draft Created"`
3. **HTTP POST** to `/generate-posters` endpoint
4. **Response parsed** and poster URLs stored in SharePoint
5. **WordPress integration** for final publication

### Power Automate Configuration:
```json
{
  "method": "POST",
  "uri": "https://cmt-poster-generator.onrender.com/generate-posters",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "event_details": "@{SharePointEventDetails}",
    "speakers": "@{SharePointSpeakers}",
    "poster_types": ["general", "speaker", "theme"]
  }
}
```

## 🎨 Poster Design Features

### Dynamic Layouts
- **1-2 speakers:** Single row layout
- **3-4 speakers:** 2x2 grid
- **5-6 speakers:** 2x3 grid
- **7+ speakers:** 3x3+ adaptive grid

### Smart Content Processing
- **Text summarization** to fit poster dimensions
- **Automatic font sizing** based on content length
- **Responsive speaker grids** based on count
- **Optimized image placement** and cropping

### Branding Elements
- **Landmark backgrounds** for event location
- **CMT Association overlay** (customizable)
- **Professional color scheme**
- **Clear call-to-action sections**

## 🚦 Rate Limiting

- **100 requests per hour** per IP address
- **Fail-open policy** if rate limiter is unavailable
- **Sliding window algorithm** for accurate tracking

## 📦 Caching Strategy

### Landmark Images
- **30-day cache** for landmark images
- **MD5 hash keys** for consistent caching
- **Automatic cache warming** for popular cities

### Generated Posters
- **Event-specific storage** with unique IDs
- **Permanent storage** for audit trail
- **CDN distribution** via Cloudflare R2

## 🔧 Service Architecture

### Modular Design
- **Abstract base classes** for easy provider switching
- **Service factory pattern** for dependency injection
- **Graceful fallbacks** for service failures

### Provider Flexibility
- **Image Generation:** Replicate (Flux-Schnell) → easily switchable
- **Text Processing:** Azure OpenAI → OpenAI, Anthropic, etc.
- **Rate Limiting:** Upstash Redis → Redis, Memory, etc.
- **Storage:** Cloudflare R2 → AWS S3, Google Cloud, etc.

## 🏥 Monitoring & Health

### Health Checks
- **Individual service status** monitoring
- **Dependency health** tracking
- **Uptime and performance** metrics

### Error Handling
- **Comprehensive exception handling**
- **Structured error responses**
- **Service degradation** notifications

## 🚀 Development

### Adding New Providers

1. **Implement base class:**
```python
class NewImageProvider(BaseImageGenerator):
    async def generate_landmark_image(self, city, country, style):
        # Implementation
        pass
```

2. **Update service factory:**
```python
if provider == "new_provider":
    return NewImageProvider(config)
```

3. **Update configuration:**
```python
IMAGE_PROVIDER="new_provider"
```

### Testing

```bash
# Test health endpoint
curl https://cmt-poster-generator.onrender.com/health

# Test poster generation
curl -X POST https://cmt-poster-generator.onrender.com/generate-posters \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues or questions:
- **GitHub Issues:** Create an issue in the repository
- **API Documentation:** Visit `/docs` endpoint for interactive documentation
- **Health Monitoring:** Check `/health` for service status

---

**Built for CMT Association** | **Powered by AI** | **Production Ready**
