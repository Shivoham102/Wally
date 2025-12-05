# Wally - Voice AI Agent for Walmart Orders

A voice-powered AI agent that helps you order from the Walmart mobile app using natural language commands.

## Features

- 🎤 **Voice Commands**: Speak naturally to add items to your cart
- 📦 **Order History**: Automatically add items from previous orders
- 🤖 **AI-Powered**: Understands natural language and context
- 🔄 **Extensible**: Designed to support other shopping apps in the future

## Tech Stack

### Core Technologies
- **Backend**: Python 3.11+
- **API Framework**: FastAPI
- **Voice Recognition**: OpenAI Whisper API (or Google Speech-to-Text)
- **AI Agent**: OpenAI GPT-4 / GPT-4 Turbo (or Anthropic Claude)
- **Mobile Automation**: Appium (cross-platform) or Android ADB
- **Database**: SQLite (development) / PostgreSQL (production)
- **Task Queue**: Celery with Redis (for async operations)

### APIs & Services
- **OpenAI API**: For voice transcription and AI agent
- **Walmart API**: (Note: Walmart doesn't have a public API, so we'll use mobile automation)
- **Android Debug Bridge (ADB)**: For Android device automation

## Architecture

```
┌─────────────────┐
│  Mobile Device  │
│  (Walmart App)  │
└────────┬────────┘
         │
         │ ADB/Appium
         │
┌────────▼─────────────────────────┐
│      Automation Layer            │
│  (Appium/ADB Controller)        │
└────────┬─────────────────────────┘
         │
         │
┌────────▼─────────────────────────┐
│      Backend API (FastAPI)       │
│  ┌─────────────────────────────┐ │
│  │  Voice Processing Module    │ │
│  │  (Speech-to-Text)           │ │
│  └─────────────────────────────┘ │
│  ┌─────────────────────────────┐ │
│  │  AI Agent Module            │ │
│  │  (Intent Recognition)       │ │
│  └─────────────────────────────┘ │
│  ┌─────────────────────────────┐ │
│  │  Order History Manager      │ │
│  └─────────────────────────────┘ │
└────────┬─────────────────────────┘
         │
         │
┌────────▼────────┐
│   Database      │
│  (SQLite/Postgres)│
└─────────────────┘
```

## Project Structure

```
Wally/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration management
│   │   ├── models/              # Database models
│   │   ├── api/                 # API routes
│   │   ├── services/            # Business logic
│   │   │   ├── voice_service.py
│   │   │   ├── ai_agent.py
│   │   │   ├── order_history.py
│   │   │   └── automation.py
│   │   └── utils/               # Utilities
│   ├── tests/
│   └── requirements.txt
├── automation/
│   ├── android/                 # Android automation scripts
│   └── ios/                     # iOS automation scripts (future)
├── config/
│   └── config.yaml              # Configuration file
├── env.example                  # Environment variables template
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- **Rust** (for building Pydantic) - [Installation Guide](INSTALL_RUST.md)
- **Android Debug Bridge (ADB)** - [Installation Guide](INSTALL_ADB.md)
- Android device with USB debugging enabled (or Android emulator)
- OpenAI API key

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. Copy `env.example` to `.env` and fill in your API keys:
   ```bash
   copy env.example .env  # Windows
   # or
   cp env.example .env    # macOS/Linux
   ```

5. Run the backend server:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

## Usage

### Starting the Voice Agent

1. Connect your Android device via USB
2. Enable USB debugging
3. Start the backend server
4. Send voice commands via the API or web interface

### Example Commands

- "Add milk, eggs, and bread"
- "Add my usual groceries"
- "Show me my previous orders"
- "Add everything from my last order"

## Development Roadmap

- [x] Project structure and setup
- [ ] Voice recognition integration
- [ ] AI agent for intent recognition
- [ ] Android automation for Walmart app
- [ ] Order history tracking
- [ ] Web interface for testing
- [ ] iOS support
- [ ] Support for other shopping apps

## Important Notes

⚠️ **Walmart API Limitation**: Walmart doesn't provide a public API for ordering. This project uses mobile automation (Appium/ADB) to interact with the Walmart mobile app. This approach:
- Requires the Walmart app to be installed
- May break if Walmart updates their app UI
- Should be used responsibly and in compliance with Walmart's Terms of Service

## License

MIT License

