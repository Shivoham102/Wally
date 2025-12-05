# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
│  (Web UI, Mobile App, Voice Input Device)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP/REST API
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              API Routes Layer                           │ │
│  │  • /api/v1/voice/*    - Voice processing               │ │
│  │  • /api/v1/orders/*   - Order management               │ │
│  │  • /api/v1/automation/* - Device automation            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │            Service Layer                                │ │
│  │  ┌──────────────────┐  ┌──────────────────┐          │ │
│  │  │ VoiceService     │  │ AIAgent          │          │ │
│  │  │ • Transcribe     │  │ • Intent parsing │          │ │
│  │  │ • Process cmd    │  │ • Item extraction│          │ │
│  │  └────────┬─────────┘  └────────┬─────────┘          │ │
│  │           │                      │                     │ │
│  │  ┌────────▼──────────────────────▼─────────┐          │ │
│  │  │ AutomationService                       │          │ │
│  │  │ • Device connection                     │          │ │
│  │  │ • App interaction                       │          │ │
│  │  │ • Add to cart                           │          │ │
│  │  └─────────────────────────────────────────┘          │ │
│  │                                                       │ │
│  │  ┌─────────────────────────────────────────┐          │ │
│  │  │ OrderHistoryService                      │          │ │
│  │  │ • Save orders                            │          │ │
│  │  │ • Retrieve history                      │          │ │
│  │  │ • Reorder functionality                  │          │ │
│  │  └─────────────────────────────────────────┘          │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌─────▼──────┐ ┌────▼──────────┐
│   Database   │ │   OpenAI   │ │  Android      │
│  (SQLite/    │ │    API     │ │  Device       │
│   Postgres)  │ │            │ │  (ADB/Appium) │
└──────────────┘ └────────────┘ └───────────────┘
```

## Data Flow

### Voice Command Processing

```
1. User speaks command
   ↓
2. Audio file uploaded to /api/v1/voice/process-command
   ↓
3. VoiceService.transcribe_audio()
   → OpenAI Whisper API
   → Returns: "Add milk, eggs, and bread"
   ↓
4. VoiceService.process_text_command()
   ↓
5. AIAgent.understand_intent()
   → OpenAI GPT-4 API
   → Returns: {
       "type": "add_items",
       "items": ["milk", "eggs", "bread"]
     }
   ↓
6. AutomationService.add_items_to_cart()
   → Appium/ADB commands
   → Walmart app interaction
   ↓
7. Response returned to client
```

### Reorder Flow

```
1. User: "Add my usual groceries"
   ↓
2. AIAgent detects "reorder" intent
   ↓
3. OrderHistoryService.get_order_history(limit=1)
   → Database query
   → Returns most recent order
   ↓
4. Extract items from order
   ↓
5. AutomationService.add_items_to_cart(items)
   → Add each item to Walmart cart
   ↓
6. Return success status
```

## Key Components

### 1. Voice Service (`voice_service.py`)
- **Responsibility**: Handle audio transcription and command orchestration
- **Dependencies**: OpenAI API, AIAgent, AutomationService
- **Key Methods**:
  - `transcribe_audio()`: Convert speech to text
  - `process_command()`: Full command processing pipeline
  - `process_text_command()`: Process text commands

### 2. AI Agent (`ai_agent.py`)
- **Responsibility**: Natural language understanding and intent recognition
- **Dependencies**: OpenAI API
- **Key Methods**:
  - `understand_intent()`: Parse user command and extract intent
  - `extract_items()`: Extract item names from commands
  - `_fallback_intent_parsing()`: Simple keyword-based fallback

### 3. Automation Service (`automation.py`)
- **Responsibility**: Interact with Android device and Walmart app
- **Dependencies**: Appium, ADB
- **Key Methods**:
  - `connect_device()`: Establish connection to Android device
  - `open_walmart_app()`: Launch Walmart app
  - `search_item()`: Search for product in app
  - `add_items_to_cart()`: Add multiple items to cart

### 4. Order History Service (`order_history.py`)
- **Responsibility**: Manage order data persistence
- **Dependencies**: SQLAlchemy, Database
- **Key Methods**:
  - `get_order_history()`: Retrieve past orders
  - `save_order()`: Store new order
  - `reorder()`: Reorder from previous order

## Technology Choices

### Why FastAPI?
- Async support for I/O-bound operations (API calls, database)
- Automatic OpenAPI documentation
- Type hints and validation with Pydantic
- High performance

### Why OpenAI Whisper?
- High accuracy speech-to-text
- Supports multiple languages
- Handles various audio formats
- Cloud-based (no local ML model needed)

### Why Appium?
- Cross-platform mobile automation
- Supports both Android and iOS
- Standard WebDriver protocol
- Large community and documentation

### Why SQLite for Development?
- Zero configuration
- File-based (easy to backup/reset)
- Sufficient for development/testing
- Easy migration to PostgreSQL for production

## Extension Points

### Adding Support for Other Apps

1. **Create new automation service**:
   ```python
   class TargetAppAutomationService:
       def add_items_to_cart(self, items):
           # App-specific implementation
   ```

2. **Update AI agent** to detect target app:
   ```python
   intent = {
       "type": "add_items",
       "app": "target_app",
       "items": [...]
   }
   ```

3. **Add app selector in voice service**:
   ```python
   if intent.get("app") == "target_app":
       service = TargetAppAutomationService()
   ```

### Adding More Intent Types

1. Update `AIAgent.SYSTEM_PROMPT` with new intent type
2. Add handler in `VoiceService._execute_intent()`
3. Implement corresponding automation logic

### Adding Voice Input UI

Create a simple web interface:
- HTML5 audio recording
- Send audio to `/api/v1/voice/process-command`
- Display results in real-time

## Security Considerations

1. **API Keys**: Stored in `.env`, never committed
2. **Device Access**: ADB requires physical access (secure)
3. **Rate Limiting**: Should be added for production
4. **Authentication**: Add API keys/auth tokens for production
5. **Input Validation**: Pydantic models validate all inputs

## Performance Optimizations

1. **Async Operations**: All I/O operations are async
2. **Connection Pooling**: Database connections reused
3. **Caching**: Could add Redis for frequently accessed orders
4. **Batch Operations**: Multiple items added in single automation session

## Future Enhancements

- [ ] WebSocket support for real-time updates
- [ ] Mobile app companion (React Native)
- [ ] Voice feedback (text-to-speech)
- [ ] Order prediction based on patterns
- [ ] Multi-user support
- [ ] Order scheduling
- [ ] Price comparison across stores



