# Quick Start Guide

Get Wally up and running in 5 minutes!

## Prerequisites Check

1. **Python 3.11+**: `python --version`
2. **ADB installed**: `adb version` 
   - ⚠️ **Don't have ADB?** See [INSTALL_ADB.md](INSTALL_ADB.md) for Windows installation guide
3. **Android device connected**: `adb devices`

## Setup Steps

### 0. Install ADB (If Not Already Installed)

**Windows Quick Install**:
1. Download: https://developer.android.com/studio/releases/platform-tools
2. Extract `platform-tools` folder (e.g., to `C:\platform-tools`)
3. Add to PATH: 
   - Win+X → System → Advanced system settings → Environment Variables
   - Edit "Path" → Add `C:\platform-tools`
   - **Restart your terminal/IDE**
4. Verify: `adb version`

📖 **Detailed instructions**: See [INSTALL_ADB.md](INSTALL_ADB.md)

### 1. Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r backend/requirements.txt
```

### 2. Configure API Keys
```bash
# Copy the example env file
copy env.example .env  # Windows
# or
cp env.example .env    # macOS/Linux

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### 3. Start the Server
```bash
cd backend
uvicorn app.main:app --reload
```

### 4. Test It Out

Open your browser to: **http://localhost:8000/docs**

Try the `/api/v1/voice/text-command` endpoint:
```json
{
  "command": "Add milk, eggs, and bread"
}
```

## Next: Connect Your Device

**Option 1: USB Connection**
1. Enable USB debugging on your Android device
2. Connect via USB
3. Verify: `adb devices`

**Option 2: Wireless Connection (Recommended)**
1. See [WIRELESS_ADB.md](WIRELESS_ADB.md) for QR code pairing method
2. Connect wirelessly: `adb connect <IP>:<PORT>`
3. Verify: `adb devices`

**Then:**
4. Call `/api/v1/automation/connect` endpoint

## Example API Calls

### Test Text Command
```bash
curl -X POST "http://localhost:8000/api/v1/voice/text-command" ^
  -H "Content-Type: application/json" ^
  -d "{\"command\": \"Add my usual groceries\"}"
```

### Connect Device
```bash
curl -X POST "http://localhost:8000/api/v1/automation/connect"
```

### Get Order History
```bash
curl "http://localhost:8000/api/v1/orders/history"
```

### Hardcoded query (bypass LLM usage)
```bash
curl -X POST http://localhost:8000/api/v1/automation/add-items-direct -H "Content-Type: application/json" -d "{\"intent\": \"add_items\", \"items\": [{\"item\": \"greek yogurt\", \"quantity\": 2}, {\"item\": \"coffee\", \"quantity\": 1}]}"

curl -X POST http://localhost:8000/api/v1/automation/add-items-direct -H "Content-Type: application/json" -d "{\"intent\": \"add_items\", \"items\": [{\"item\": \"whole milk\", \"quantity\": 2}, {\"item\": \"non-fat Greek yogurt\", \"quantity\": 1}, {\"item\": \"tomatoes\", \"quantity\": 10}, {\"item\": \"Nestle Toll House 100% pure cocoa powder\", \"quantity\": 1}, {\"item\": \"Azumaya Tofu, extra firm\", \"quantity\": 4}, {\"item\": \"fresh cantaloupe\", \"quantity\": 1}, {\"item\": \"fresh mangoes\", \"quantity\": 3}, {\"item\": \"fresh grapefruits\", \"quantity\": 2}, {\"item\": \"fresh cucumber\", \"quantity\": 1}, {\"item\": \"Great Value Old Fashioned Oats\", \"quantity\": 1}]}"
```

## Troubleshooting

**"No module named 'app'"**
- Make sure you're in the `backend` directory when running uvicorn
- Or use: `uvicorn backend.app.main:app --reload` from project root

**"OpenAI API key not found"**
- Check your `.env` file exists and has `OPENAI_API_KEY=sk-...`
- Make sure `.env` is in the project root

**Device not found**
- Run `adb devices` to verify connection
- Check USB debugging is enabled
- Try `adb kill-server && adb start-server`


