# Tech Stack & APIs Reference

## Core Technologies

### Backend Framework: FastAPI
- **Version**: 0.104.1
- **Why**: 
  - Modern, fast Python web framework
  - Built-in async support
  - Automatic OpenAPI/Swagger documentation
  - Type validation with Pydantic
- **Documentation**: https://fastapi.tiangolo.com/

### Python Version
- **Required**: Python 3.11+
- **Why**: Modern async/await support, better type hints

### Database: SQLAlchemy
- **Version**: 2.0.23
- **Why**: 
  - ORM for database operations
  - Supports SQLite (dev) and PostgreSQL (production)
  - Type-safe queries
- **Documentation**: https://docs.sqlalchemy.org/

## APIs & External Services

### 1. OpenAI API
**Purpose**: Voice transcription and AI agent

**Services Used**:
- **Whisper API** (`whisper-1` model)
  - Speech-to-text transcription
  - Supports multiple audio formats (mp3, wav, m4a, etc.)
  - High accuracy, handles accents and background noise
  - Cost: ~$0.006 per minute of audio

- **GPT-4 Turbo** (`gpt-4-turbo-preview`)
  - Natural language understanding
  - Intent recognition
  - Item extraction from commands
  - Cost: ~$0.01 per 1K input tokens, $0.03 per 1K output tokens

**Setup**:
1. Sign up at https://platform.openai.com/
2. Get API key from https://platform.openai.com/api-keys
3. Add credits to account
4. Set `OPENAI_API_KEY` in `.env`

**Alternative**: Anthropic Claude API
- Similar capabilities to GPT-4
- Set `ANTHROPIC_API_KEY` in `.env` to use instead

**Documentation**: https://platform.openai.com/docs

### 2. Appium
**Purpose**: Mobile app automation

**What it is**:
- Open-source framework for automating mobile apps
- Cross-platform (Android & iOS)
- Uses WebDriver protocol (same as Selenium)

**Setup**:
```bash
# Install Node.js first
npm install -g appium
appium driver install uiautomator2  # For Android
```

**How it works**:
- Appium server runs on port 4723
- Python client connects to server
- Server communicates with device via ADB (Android) or XCUITest (iOS)

**Documentation**: https://appium.io/docs/

**Alternative**: Direct ADB commands
- Simpler but less powerful
- Already implemented as fallback
- No Appium server needed

### 3. Android Debug Bridge (ADB)
**Purpose**: Direct Android device communication

**What it is**:
- Command-line tool for Android devices
- Part of Android SDK Platform Tools
- Allows device control, app installation, UI interaction

**Setup**:
1. Download from: https://developer.android.com/studio/releases/platform-tools
2. Add to system PATH
3. Enable USB debugging on device
4. Connect device via USB

**Common Commands**:
```bash
adb devices              # List connected devices
adb shell am start ...   # Launch app
adb shell input tap x y  # Tap screen
adb shell input text ... # Type text
```

**Documentation**: https://developer.android.com/studio/command-line/adb

## Mobile Automation Approach

### Why Mobile Automation?
Walmart doesn't provide a public API for ordering. Mobile automation allows us to:
- Interact with the Walmart app programmatically
- Search for products
- Add items to cart
- Navigate the app UI

### How It Works
1. **Connect to device** via ADB or Appium
2. **Launch Walmart app** using package name
3. **Find UI elements** using:
   - Element IDs (resource-id)
   - XPath selectors
   - Accessibility labels
   - Screen coordinates (fallback)
4. **Interact with elements**:
   - Tap buttons
   - Enter text in search fields
   - Scroll lists
   - Wait for elements to appear

### Challenges
- **UI Changes**: Walmart may update app UI, breaking selectors
- **Element Finding**: Requires inspecting app UI hierarchy
- **Timing**: Need to wait for elements to load
- **Error Handling**: Handle network errors, out of stock, etc.

### Tools for UI Inspection
- **Appium Inspector**: Visual tool for finding elements
- **UI Automator Viewer**: Android SDK tool
- **Accessibility Scanner**: For accessibility-based selection

## Database Options

### Development: SQLite
- **File-based**: `wally.db` in project directory
- **Zero configuration**: Works out of the box
- **Easy backup**: Just copy the file
- **Limitations**: Single writer, no network access

### Production: PostgreSQL
- **Change**: `DATABASE_URL=postgresql://user:pass@host/dbname`
- **Benefits**: 
  - Concurrent connections
  - Better performance
  - Network accessible
  - Advanced features

## Task Queue (Optional)

### Celery + Redis
**Purpose**: Background job processing

**Use Cases**:
- Process long-running automation tasks
- Queue multiple orders
- Retry failed operations
- Scheduled tasks (e.g., weekly reorders)

**Setup** (if needed):
```bash
# Install Redis
# Then in Python:
pip install celery redis
```

## Audio Processing

### pydub
- **Purpose**: Audio file manipulation
- **Use**: Convert between formats, trim audio
- **Documentation**: https://github.com/jiaaro/pydub

### speechrecognition
- **Purpose**: Alternative speech recognition (not used currently)
- **Note**: Using OpenAI Whisper instead (better accuracy)

## HTTP Client

### httpx / aiohttp
- **Purpose**: Async HTTP requests
- **Use**: Future API integrations, webhooks
- **Why async**: Non-blocking I/O operations

## Testing

### pytest
- **Purpose**: Unit and integration tests
- **Setup**: `pip install pytest pytest-asyncio`
- **Run**: `pytest backend/tests/`

## Development Tools

### uvicorn
- **Purpose**: ASGI server for FastAPI
- **Run**: `uvicorn app.main:app --reload`
- **Features**: Hot reload, production-ready

### alembic
- **Purpose**: Database migrations
- **Use**: Track schema changes, version control
- **Setup**: `alembic init alembic` (if needed)

## Cost Estimates

### OpenAI API (Monthly)
- **Whisper**: ~$0.006/minute
  - 100 commands/day × 30 days = 3,000 minutes = $18/month
- **GPT-4**: ~$0.01/1K tokens
  - 100 commands/day × 500 tokens = 1.5M tokens = $15/month
- **Total**: ~$33/month for moderate usage

### Infrastructure
- **Development**: Free (local)
- **Production**: 
  - Server: $5-20/month (VPS)
  - Database: $0-10/month (managed PostgreSQL)
  - Total: ~$5-30/month

## Alternative APIs & Services

### Voice Recognition Alternatives
1. **Google Speech-to-Text**
   - Similar accuracy to Whisper
   - Free tier: 60 minutes/month
   - Paid: $0.006/15 seconds

2. **Azure Speech Services**
   - Good accuracy
   - Free tier: 5 hours/month
   - Paid: $1/hour

3. **Local Whisper**
   - Run Whisper model locally
   - No API costs
   - Requires GPU for good performance

### AI Agent Alternatives
1. **Anthropic Claude**
   - Similar to GPT-4
   - Good for long contexts
   - Set `ANTHROPIC_API_KEY` to use

2. **Local LLM** (Ollama, Llama.cpp)
   - Run model locally
   - No API costs
   - Lower accuracy, requires GPU

3. **OpenAI GPT-3.5**
   - Cheaper than GPT-4
   - Good enough for simple intents
   - Change `AI_MODEL=gpt-3.5-turbo`

## Future Integrations

### Potential APIs to Add
1. **Walmart API** (if available)
   - Direct product search
   - Cart management
   - Order placement
   - Would eliminate need for automation

2. **Instacart API**
   - Similar grocery ordering
   - May have public API

3. **Google Shopping API**
   - Product search across stores
   - Price comparison

4. **Twilio API**
   - Voice calls for ordering
   - SMS notifications

5. **Stripe API**
   - Payment processing
   - Subscription management

## Security Considerations

### API Keys
- **Storage**: Environment variables (`.env` file)
- **Never commit**: `.env` in `.gitignore`
- **Production**: Use secrets manager (AWS Secrets Manager, etc.)

### Device Access
- **ADB**: Requires physical USB connection (secure)
- **Network ADB**: Can be enabled but less secure
- **Appium**: Runs locally, not exposed to internet

### Rate Limiting
- **Add**: For production API endpoints
- **Use**: `slowapi` or `fastapi-limiter`
- **Protect**: Against abuse and API cost overruns

## Performance Optimization

### Current Setup
- **Async**: All I/O operations are async
- **Connection Pooling**: Database connections reused
- **No Caching**: Could add Redis for orders

### Future Optimizations
1. **Redis Caching**: Cache frequent queries
2. **CDN**: For static assets (if web UI added)
3. **Database Indexing**: On order date, user ID
4. **Batch Processing**: Group multiple operations



