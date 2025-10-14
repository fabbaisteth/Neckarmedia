# 🚀 Quick Start - Public Chatbot Deployment

Get your Neckarmedia chatbot running in 5 minutes!

## Prerequisites
- Docker installed
- Your OpenAI API key (or other LLM provider)

## Steps

### 1. Create Environment File

Create a `.env` file in the project root:

```bash
# Copy the example
cp .env.example .env

# Edit with your settings
nano .env
```

**Minimum required settings:**
```env
# Allow all origins (for testing) or specify your domain
ALLOWED_ORIGINS=*

# Your OpenAI API key
OPENAI_API_KEY=sk-your-key-here

# Public mode (no authentication needed)
PUBLIC_MODE=true

# Environment
ENVIRONMENT=development
```

### 2. Build and Run with Docker

```bash
# Build the image
docker build -t neckarmedia-chatbot .

# Run the container
docker run -d \
  --name neckarmedia-chatbot \
  -p 8000:8000 \
  --env-file .env \
  neckarmedia-chatbot
```

**OR use Docker Compose:**

```bash
docker-compose up -d
```

### 3. Test It

```bash
# Health check
curl http://localhost:8000/health

# Test chat
curl -X POST http://localhost:8000/chat_response \
  -H "Content-Type: application/json" \
  -d '{"user_prompt": "Was macht Neckarmedia?"}'
```

**Or run the test script:**
```bash
./test_public_api.sh
```

### 4. Integrate with Your Website

Add this to your HTML:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Chatbot</title>
</head>
<body>
    <div id="chat"></div>
    <input id="input" type="text" placeholder="Ask something...">
    <button onclick="sendMessage()">Send</button>

    <script>
        const API_URL = 'http://localhost:8000';  // Change to your domain

        async function sendMessage() {
            const input = document.getElementById('input');
            const message = input.value;
            
            const response = await fetch(`${API_URL}/chat_response`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_prompt: message })
            });
            
            const data = await response.json();
            document.getElementById('chat').innerHTML += 
                `<p><strong>You:</strong> ${message}</p>
                 <p><strong>Bot:</strong> ${data.response}</p>`;
            
            input.value = '';
        }
    </script>
</body>
</html>
```

## Next Steps

### For Production Deployment:

1. **Get a domain and SSL certificate**
   ```bash
   # Update .env
   ALLOWED_ORIGINS=https://yourdomain.com
   ENVIRONMENT=production
   ```

2. **Deploy to cloud** (choose one):
   - Railway: Connect GitHub repo, auto-deploy
   - DigitalOcean: App Platform or Droplet
   - Google Cloud Run: `gcloud run deploy`
   - Your own VPS: Same Docker commands

3. **Add reverse proxy** (optional but recommended):
   - Use Nginx or Caddy for SSL termination
   - Or use Cloudflare for free SSL + DDoS protection

4. **Monitor your API**:
   ```bash
   # View logs
   docker logs -f neckarmedia-chatbot
   
   # Check resource usage
   docker stats neckarmedia-chatbot
   ```

## Configuration Options

### Rate Limiting
```env
# Allow 20 requests per minute per IP
RATE_LIMIT_REQUESTS=20
RATE_LIMIT_PERIOD=60
```

### CORS (Cross-Origin Resource Sharing)
```env
# Development - allow all
ALLOWED_ORIGINS=*

# Production - specific domains
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Environment
```env
# Development - shows detailed errors, enables /docs
ENVIRONMENT=development

# Production - hides errors, disables /docs
ENVIRONMENT=production
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs neckarmedia-chatbot

# Check if port is already in use
lsof -i :8000
```

### CORS errors in browser
```bash
# Temporarily allow all origins for testing
ALLOWED_ORIGINS=*

# Or add your local development URL
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Rate limiting too strict
```bash
# Increase limits in .env
RATE_LIMIT_REQUESTS=50
RATE_LIMIT_PERIOD=60

# Restart container
docker restart neckarmedia-chatbot
```

## Security Notes

✅ **What's protected:**
- Rate limiting per IP (prevents spam)
- Input validation (rejects too long prompts)
- Security headers (XSS, clickjacking protection)
- CORS restrictions (only allowed domains)
- Non-root container user

⚠️ **What's NOT protected (by design):**
- No authentication (public chatbot)
- Anyone can access the API endpoint

💡 **For production:**
- Use HTTPS (SSL certificate)
- Set ALLOWED_ORIGINS to your domain only
- Monitor usage to detect abuse
- Consider adding CAPTCHA if needed
- Use Cloudflare or similar for DDoS protection

## Full Documentation

- **Detailed deployment guide:** See `PUBLIC_DEPLOYMENT.md`
- **API documentation:** Visit http://localhost:8000/docs (development mode)
- **General info:** See `README.md`

## Need Help?

1. Check logs: `docker logs neckarmedia-chatbot`
2. Test endpoints: `./test_public_api.sh`
3. Review configuration: `cat .env`

---

**Ready to deploy?** Follow the comprehensive guide in `PUBLIC_DEPLOYMENT.md`

