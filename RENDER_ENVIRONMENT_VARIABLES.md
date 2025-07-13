# Environment Variables for Render Deployment

## Required Environment Variables for CMT Poster Generator

### **Core Application Settings**
```
# API Configuration
API_TITLE=CMT Poster Generator
API_VERSION=1.0.0
DEBUG=false

# Performance Settings
REQUEST_TIMEOUT=25
IMAGE_DOWNLOAD_TIMEOUT=10
```

### **Text Processing (Required for AI Summarization)**
```
# Azure OpenAI Configuration
TEXT_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_TEMPERATURE=0.7
AZURE_OPENAI_MAX_TOKENS=150
```

### **Rate Limiting (Optional - Falls back to memory-based)**
```
# Upstash Redis (Optional - for production rate limiting)
RATE_LIMITER=upstash
UPSTASH_REDIS_URL=https://your-redis-instance.upstash.io
UPSTASH_REDIS_TOKEN=your-upstash-token

# Rate Limiting Settings
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

### **WordPress Integration (Required for Media Management)**
```
# WordPress Media Library Access
STORAGE_PROVIDER=wordpress
WORDPRESS_URL=https://cmtpl.org
WORDPRESS_USERNAME=your-wp-username
WORDPRESS_PASSWORD=your-wp-app-password
WORDPRESS_MEDIA_TIMEOUT=60
WORDPRESS_SEARCH_LIMIT=50
```

### **Image Generation (Optional - Not required for current workflow)**
```
# Replicate (Optional - for AI landmark generation)
IMAGE_PROVIDER=replicate
REPLICATE_API_TOKEN=your-replicate-token
```

### **Poster Configuration**
```
# Poster Settings
POSTER_WIDTH=1200
POSTER_HEIGHT=1600
POSTER_FORMAT=PNG
POSTER_QUALITY=95
POSTER_FONT_FAMILY=Glacial Indifference

# Image Processing
SPEAKER_PHOTO_CACHE_DURATION=86400
LANDMARK_SEARCH_TIMEOUT=30
```

---

## **Minimal Required Setup (Core Functionality)**

For basic poster generation without AI text processing:

```
API_TITLE=CMT Poster Generator
API_VERSION=1.0.0
DEBUG=false
STORAGE_PROVIDER=wordpress
WORDPRESS_URL=https://cmtpl.org
WORDPRESS_USERNAME=your-wp-username
WORDPRESS_PASSWORD=your-wp-app-password
```

---

## **Full Production Setup**

For complete functionality with AI text processing and rate limiting:

```
# Core
API_TITLE=CMT Poster Generator
API_VERSION=1.0.0
DEBUG=false

# WordPress
STORAGE_PROVIDER=wordpress
WORDPRESS_URL=https://cmtpl.org
WORDPRESS_USERNAME=your-wp-username
WORDPRESS_PASSWORD=your-wp-app-password

# Azure OpenAI
TEXT_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Rate Limiting (Optional)
RATE_LIMITER=upstash
UPSTASH_REDIS_URL=https://your-redis.upstash.io
UPSTASH_REDIS_TOKEN=your-upstash-token
```

---

## **How to Set Environment Variables in Render**

1. **Go to your Render Dashboard**
2. **Select your Web Service**
3. **Go to "Environment" tab**
4. **Add each variable as Key-Value pairs**

### **Priority Order:**
1. **WordPress credentials** (Required for media access)
2. **Azure OpenAI credentials** (Required for text summarization)
3. **Upstash Redis credentials** (Optional for rate limiting)
4. **Replicate token** (Optional for AI landmark generation)

---

## **Security Notes**

- **Never commit these values to Git**
- **Use Render's encrypted environment variables**
- **WordPress Password should be an Application Password, not your main login**
- **Azure OpenAI API keys should have minimal required permissions**
- **Upstash Redis should be configured for your expected traffic**

---

## **Testing Your Setup**

After setting environment variables:

1. **Deploy to Render**
2. **Visit**: `https://your-app.onrender.com/health`
3. **Check service status**: `https://your-app.onrender.com/services/status`
4. **Test with your payload**: `https://your-app.onrender.com/generate-posters`

The health endpoint will show which services are properly configured.
