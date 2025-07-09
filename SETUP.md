# CMT Poster Generator - Complete Setup Guide

## 🚀 **Production Setup Instructions**

### **Prerequisites**
- Render account for hosting
- Upstash account for Redis rate limiting
- WordPress site with 53GB storage for media
- Replicate account for AI image generation
- Azure OpenAI account for text processing

---

## 📋 **Step 1: Service Account Setup**

### **1.1 Replicate API Token**
1. Go to [replicate.com](https://replicate.com)
2. Sign up/Login to your account
3. Navigate to Account → API Tokens
4. Create new token → Copy the token (starts with `r8_...`)

### **1.2 Azure OpenAI Credentials**
1. Go to [Azure Portal](https://portal.azure.com)
2. Create "Azure OpenAI" resource
3. Once deployed, go to resource → Keys and Endpoint
4. Copy **Endpoint URL** and **API Key**
5. Go to Azure OpenAI Studio → Deploy **GPT-4** model
6. Note the **deployment name** (usually "gpt-4")

### **1.3 Upstash Redis Database**
1. Go to [upstash.com](https://upstash.com)
2. Create account → Create Database
3. **Configuration:**
   - **Name**: `cmt-poster-generator`
   - **Region**: `us-east-1` (best for global performance)
   - **Eviction**: `Enabled`
   - **Eviction Policy**: `allkeys-lru`
4. Copy **UPSTASH_REDIS_REST_URL** and **UPSTASH_REDIS_REST_TOKEN**

### **1.4 WordPress Media Storage**
1. Ensure WordPress site has media upload permissions
2. Verify WordPress REST API is enabled (usually default)
3. Have WordPress admin username and password ready

---

## 🌐 **Step 2: Render Deployment**

### **2.1 Render Service Configuration**
```yaml
Name: cmt-poster-generator
Language: Python 3
Branch: main
Region: Oregon (US West)
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
Auto-Deploy: On commit
```

### **2.2 Environment Variables**
Add these to Render Dashboard → Environment Variables:

```env
# API Configuration
API_TITLE=CMT Poster Generator
API_VERSION=1.0.0
DEBUG=false

# Service Providers
IMAGE_PROVIDER=replicate
TEXT_PROVIDER=azure_openai
RATE_LIMITER=upstash
STORAGE_PROVIDER=wordpress

# Replicate (AI Image Generation)
REPLICATE_API_TOKEN=r8_your_token_here

# Azure OpenAI (Text Processing)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Upstash Redis (Rate Limiting)
UPSTASH_REDIS_URL=https://your-db.upstash.io
UPSTASH_REDIS_TOKEN=your_token_here

# WordPress (Storage & Speaker Photos)
WORDPRESS_URL=https://your-wordpress-site.com
WORDPRESS_USERNAME=your_wp_username
WORDPRESS_PASSWORD=your_wp_password

# Poster Configuration
POSTER_WIDTH=1200
POSTER_HEIGHT=1600
POSTER_FORMAT=PNG
POSTER_QUALITY=95
POSTER_FONT_FAMILY=Glacial Indifference

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

---

## 🔧 **Step 3: WordPress Media Setup**

### **3.1 Media Library Structure**
The system will automatically create this structure in your WordPress media library:

```
WordPress Media Library:
├── cmt-landmarks/          # AI-generated landmark images
│   ├── new-york-usa.png
│   ├── london-uk.png
│   └── tokyo-japan.png
├── cmt-posters/           # Generated event posters
│   ├── event-abc123/
│   │   ├── general.png
│   │   ├── speaker-john-doe.png
│   │   └── theme.png
│   └── event-def456/
│       └── general.png
```

### **3.2 Media Upload Permissions**
Ensure your WordPress user has:
- ✅ **Upload files** permission
- ✅ **Edit media** permission
- ✅ **Delete media** permission (optional)

---

## 🧪 **Step 4: Testing Your Setup**

### **4.1 Health Check**
Visit: `https://your-app.onrender.com/health`

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "image_generator": {"status": "healthy"},
    "text_processor": {"status": "healthy"},
    "rate_limiter": {"status": "healthy"},
    "storage": {"status": "healthy"}
  }
}
```

### **4.2 API Documentation**
Visit: `https://your-app.onrender.com/docs`

### **4.3 Test Poster Generation**
Use the `/generate-posters` endpoint with sample data.

---

## 🎯 **Step 5: Power Automate Integration**

### **5.1 HTTP Request Configuration**
```json
{
  "method": "POST",
  "uri": "https://your-app.onrender.com/generate-posters",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "event_details": {
      "title": "CMT Event Title",
      "date": "2024-03-15T10:00:00Z",
      "venue": "Conference Center",
      "city": "New York",
      "country": "USA",
      "description": "Event description..."
    },
    "speakers": [
      {
        "name": "John Doe",
        "title": "CEO",
        "organization": "Tech Corp",
        "bio": "Speaker bio...",
        "linkedin_url": "https://linkedin.com/in/johndoe"
      }
    ],
    "poster_types": ["general", "speaker", "theme"]
  }
}
```

### **5.2 Response Handling**
```json
{
  "success": true,
  "posters": [
    {
      "poster_type": "general",
      "url": "https://your-wordpress.com/wp-content/uploads/...",
      "dimensions": {"width": 1200, "height": 1600},
      "format": "PNG"
    }
  ]
}
```

---

## 📊 **Storage Usage & Costs**

### **WordPress Storage (53GB)**
- ✅ **Landmark images**: ~5MB each, ~100 cities = 500MB
- ✅ **Event posters**: ~2MB each, ~1000 events = 2GB
- ✅ **Total estimated usage**: <5GB of 53GB available

### **Upstash Redis (Free Tier)**
- ✅ **10,000 commands/day** - sufficient for rate limiting
- ✅ **Rate limit data**: Auto-expires after 1 hour

### **Azure OpenAI**
- 💰 **Pay per token** - minimal usage for text summarization
- 💰 **Estimated**: <$10/month for typical usage

### **Replicate**
- 💰 **Pay per prediction** - ~$0.01 per landmark image
- 💰 **Estimated**: <$5/month for typical usage

---

## 🔍 **Troubleshooting**

### **Common Issues**

**1. WordPress Authentication Failed**
- Check WordPress URL, username, and password
- Verify user has media upload permissions
- Ensure WordPress site is accessible

**2. Rate Limiting Not Working**
- Verify Upstash Redis URL and token
- Check Redis database is active
- Ensure eviction policy is set to `allkeys-lru`

**3. Image Generation Failing**
- Check Replicate API token
- Verify account has sufficient credits
- Check model availability

**4. Text Processing Issues**
- Verify Azure OpenAI endpoint and API key
- Check GPT-4 model deployment
- Ensure API quotas are available

### **Debug Endpoints**
- **Health Check**: `/health`
- **Last Request**: `/last-payload` (debug endpoint)
- **API Docs**: `/docs`

---

## 🎉 **You're Ready!**

Your CMT Poster Generator is now configured for:
- ✅ **Automated poster generation** with AI
- ✅ **WordPress media storage** (53GB capacity)
- ✅ **Rate limiting** with Upstash Redis
- ✅ **Power Automate integration** 
- ✅ **Glacial Indifference font** for all text
- ✅ **Global scalability** with Render hosting

The system will automatically:
1. Generate landmark backgrounds for event cities
2. Create professional posters with event details
3. Fetch speaker photos from WordPress
4. Store all assets in WordPress media library
5. Return public URLs for Power Automate integration
