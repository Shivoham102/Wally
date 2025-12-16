export const API_CONFIG = {
  // Use ngrok URL for Expo Go testing (HTTPS works reliably)
  // Run: ngrok http 8000
  // Then paste the https URL here
  BASE_URL: 'https://stupid-clocks-occur.loca.lt', // <-- PASTE LOCALTUNNEL URL HERE
  
  ENDPOINTS: {
    HEALTH: '/health',
    VOICE_TRANSCRIBE: '/api/v1/voice/transcribe',
    VOICE_PROCESS: '/api/v1/voice/process-command',
    VOICE_TEXT: '/api/v1/voice/text-command',
    ORDERS_HISTORY: '/api/v1/orders/history',
    ORDERS_REORDER: '/api/v1/orders/reorder',
    AUTOMATION_STATUS: '/api/v1/automation/status',
    AUTOMATION_ADD_ITEMS: '/api/v1/automation/add-items-direct',
    AUTOMATION_CONNECT: '/api/v1/automation/connect',
    AUTOMATION_OPEN_WALMART: '/api/v1/automation/open-walmart',
  },
};

export function getApiUrl(endpoint: string): string {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
}
