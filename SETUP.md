# Setup Guide for Wally Voice AI Agent

## Prerequisites

### 1. Python Environment
- Python 3.11 or higher
- pip package manager

### 2. Android Development Tools
- **Android Debug Bridge (ADB)**: Required for device communication
  - Download from: https://developer.android.com/studio/releases/platform-tools
  - Add to system PATH
  - Verify installation: `adb version`

- **Appium** (Optional but recommended):
  - Install Node.js: https://nodejs.org/
  - Install Appium: `npm install -g appium`
  - Install Appium drivers: `appium driver install uiautomator2`
  - Start Appium server: `appium`

### 3. Android Device Setup
- Android phone or tablet (or emulator)
- Enable Developer Options:
  1. Go to Settings > About Phone
  2. Tap "Build Number" 7 times
- Enable USB Debugging:
  1. Settings > Developer Options > USB Debugging (ON)
- Connect device via USB
- Verify connection: `adb devices`

### 4. Walmart App
- Install Walmart app from Google Play Store
- Log in to your Walmart account
- Ensure app is up to date

### 5. API Keys
- **OpenAI API Key**: 
  - Sign up at https://platform.openai.com/
  - Get API key from https://platform.openai.com/api-keys
  - Add credits to your account

- **Anthropic API Key** (Optional):
  - Sign up at https://www.anthropic.com/
  - Get API key from console

## Installation Steps

### Step 1: Clone and Navigate
```bash
cd Wally
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 4: Configure Environment
```bash
# Copy example env file
copy env.example .env  # Windows
# or
cp env.example .env    # macOS/Linux

# Edit .env file with your API keys
# Use your preferred text editor
```

Edit `.env` file:
```env
OPENAI_API_KEY=sk-your-actual-key-here
DATABASE_URL=sqlite:///./wally.db
```

### Step 5: Start Appium Server (if using Appium)
```bash
# In a separate terminal
appium
```

### Step 6: Verify Device Connection
```bash
adb devices
# Should show your device listed
```

### Step 7: Run the Backend Server
```bash
cd backend
uvicorn app.main:app --reload
```

The API will be available at: http://localhost:8000

### Step 8: Test the API
Open browser to: http://localhost:8000/docs

You'll see the Swagger UI with all available endpoints.

## Testing Voice Commands

### Option 1: Using the API Directly
```bash
# Test text command
curl -X POST "http://localhost:8000/api/v1/voice/text-command" \
  -H "Content-Type: application/json" \
  -d '{"command": "Add milk, eggs, and bread"}'
```

### Option 2: Using Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/voice/text-command",
    json={"command": "Add my usual groceries"}
)
print(response.json())
```

### Option 3: Using Swagger UI
1. Go to http://localhost:8000/docs
2. Find `/api/v1/voice/text-command` endpoint
3. Click "Try it out"
4. Enter a command and execute

## Next Steps

1. **Map Walmart App UI Elements**: 
   - Use Appium Inspector or UI Automator Viewer
   - Update selectors in `automation.py` with actual element IDs/XPaths

2. **Test Order History**:
   - Manually save some test orders via API
   - Test reordering functionality

3. **Improve AI Agent**:
   - Fine-tune prompts in `ai_agent.py`
   - Add more intent types
   - Improve item extraction accuracy

4. **Add Voice Input**:
   - Create a simple web interface for voice recording
   - Or use a mobile app that sends audio to the API

## Troubleshooting

### Device Not Found
- Check USB connection
- Verify USB debugging is enabled
- Try `adb kill-server && adb start-server`
- Check if device appears in `adb devices`

### Appium Connection Failed
- Ensure Appium server is running: `appium`
- Check if port 4723 is available
- Verify Appium version: `appium --version`

### OpenAI API Errors
- Verify API key is correct
- Check account has credits
- Ensure internet connection is working

### Import Errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r backend/requirements.txt`

## Important Notes

⚠️ **Walmart App Automation**: 
- This project uses automation to interact with the Walmart app
- Walmart may update their app UI, breaking automation
- You'll need to update element selectors when UI changes
- Use responsibly and in compliance with Walmart's Terms of Service

🔒 **Security**:
- Never commit `.env` file with real API keys
- Use environment variables in production
- Consider using a secrets manager for production deployments

