# Mobile App Setup Guide

This guide explains how to set up and run the Wally React Native mobile app.

## Overview

The mobile app is a lightweight React Native client built with Expo that connects to your FastAPI backend. It provides:

- Voice command recording and processing
- Order history viewing
- Backend configuration and status monitoring
- Simple onboarding flow

## Prerequisites

- Node.js 18+ and npm
- Expo CLI (installed globally or via npx)
- Android device or emulator (for Android development)
- Backend server running (see main README for backend setup)

## Installation

1. Navigate to the mobile directory:
   ```bash
   cd mobile
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Running the App

### Development Mode

Start the Expo development server:
```bash
npm start
# or
npx expo start
```

This will:
- Start the Metro bundler
- Display a QR code for Expo Go app
- Show options to open on Android/iOS

### Running on Android

**Option 1: Using Expo Go (Easiest)**
1. Install [Expo Go](https://play.google.com/store/apps/details?id=host.exp.exponent) on your Android device
2. Scan the QR code from `npm start`
3. The app will load on your device

**Option 2: Using Android Emulator**
```bash
npm run android
```

**Option 3: Building APK**
```bash
npx expo build:android
```

## First-Time Setup

When you first launch the app:

1. **Onboarding Screen**: 
   - Explains what Wally does
   - Requests microphone permission
   - Guides you to enter backend URL

2. **Backend Configuration**:
   - Enter your backend URL (e.g., `http://192.168.1.100:8000` for local network, or cloud URL)
   - Tap "Test Connection" to verify connectivity
   - Backend must be running and accessible

3. **Wireless Debugging** (for automation):
   - Enable Developer Options on your Android device
   - Enable Wireless Debugging
   - Note the IP address and port
   - Your backend server will connect to the device using this information

## App Structure

```
mobile/
├── app/                    # Expo Router screens
│   ├── (tabs)/            # Tab navigation screens
│   │   ├── voice.tsx      # Main voice command screen
│   │   ├── history.tsx    # Order history screen
│   │   └── settings.tsx   # Settings and configuration
│   ├── onboarding.tsx     # First-time setup flow
│   └── _layout.tsx        # Root layout
├── api/                    # API client layer
│   ├── client.ts          # Base HTTP client
│   ├── voice.ts           # Voice endpoints
│   ├── orders.ts          # Order endpoints
│   └── automation.ts      # Automation endpoints
├── config/                 # Configuration
│   ├── env.ts             # Environment/config management
│   └── storage.ts         # AsyncStorage utilities
└── package.json
```

## Features

### Voice Screen
- Record voice commands using the microphone
- View transcription and AI intent recognition results
- See execution status (items added, reorder status, etc.)

### History Screen
- View past orders
- Reorder previous orders with one tap
- Pull to refresh order list

### Settings Screen
- Configure backend URL
- Test backend connection
- View automation status (device connection, Walmart app status)
- Instructions for wireless debugging setup

## Backend Connection

The mobile app communicates with the backend via HTTP REST API:

- **Voice Processing**: `POST /api/v1/voice/process-command`
- **Text Commands**: `POST /api/v1/voice/text-command`
- **Order History**: `GET /api/v1/orders/history`
- **Reorder**: `POST /api/v1/orders/reorder/{id}`
- **Automation Status**: `GET /api/v1/automation/status`
- **Health Check**: `GET /health`

### Backend URL Configuration

The backend URL can be:
- **Local Network**: `http://192.168.x.x:8000` (when backend runs on same network)
- **Cloud Server**: `https://your-backend.com` (when backend is deployed)

The URL is stored locally using AsyncStorage and can be changed in Settings.

## Wireless Debugging Setup

For Walmart app automation to work, wireless debugging must be enabled:

1. **Enable Developer Options**:
   - Go to Settings → About Phone
   - Tap "Build Number" 7 times
   - Go back → Developer Options

2. **Enable Wireless Debugging**:
   - In Developer Options, enable "Wireless Debugging"
   - Note the IP address and port displayed (e.g., `192.168.1.100:5555`)

3. **Backend Connection**:
   - Your backend server connects to the device using: `adb connect <ip>:<port>`
   - The mobile app shows automation status in Settings

**Note**: The mobile app itself doesn't handle ADB connections - that's done by the backend server. The app only displays status.

## Troubleshooting

### Backend Connection Issues
- Ensure backend is running: `cd backend && uvicorn app.main:app --reload`
- Check backend URL is correct (no trailing slash)
- Verify network connectivity (same WiFi for local network)
- Check CORS settings in backend (should allow all origins)

### Audio Recording Issues
- Grant microphone permission when prompted
- Check device microphone is working
- Ensure audio format is supported (M4A/AAC)

### Build Issues
- Clear cache: `npx expo start -c`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 18+)

## Development Tips

- Use Expo DevTools for debugging: `npx expo start --devtools`
- Hot reload is enabled by default - changes reflect immediately
- Check Metro bundler logs for errors
- Use React Native Debugger for advanced debugging

## Production Build

To create a production APK:

```bash
npx expo build:android
```

Or use EAS Build (recommended):

```bash
npm install -g eas-cli
eas build --platform android
```

## Next Steps

- Add authentication/API keys for multi-user support
- Implement push notifications for order status
- Add iOS support (Expo makes this straightforward)
- Optimize bundle size and performance

## Related Documentation

- [Main README](../README.md) - Backend setup and architecture
- [Backend API Documentation](../backend/README.md) - API endpoints reference
- [Expo Documentation](https://docs.expo.dev/) - Expo framework docs



