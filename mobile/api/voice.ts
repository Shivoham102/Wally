import { API_CONFIG, getApiUrl } from './config';

export interface TranscriptionResult {
  text: string;
  language: string;
}

export interface ProcessCommandResult {
  transcription: string;
  intent: {
    type: string;
    items?: string[];
  };
  status: string;
  message?: string;
}

/**
 * Transcribe audio file to text
 */
export async function transcribeAudio(audioUri: string): Promise<TranscriptionResult> {
  const url = getApiUrl(API_CONFIG.ENDPOINTS.VOICE_TRANSCRIBE);
  console.log('Transcribing audio:', audioUri);
  console.log('POST to:', url);
  
  const formData = new FormData();
  
  // Create file object from URI
  const filename = audioUri.split('/').pop() || 'recording.m4a';
  formData.append('audio_file', {
    uri: audioUri,
    name: filename,
    type: 'audio/m4a',
  } as any);

  // Don't set Content-Type header - fetch will set it automatically with boundary
  const response = await fetch(url, {
    method: 'POST',
    body: formData,
    headers: {
      'ngrok-skip-browser-warning': 'true', // Bypass ngrok warning page
    },
  });

  console.log('Response status:', response.status);

  if (!response.ok) {
    const error = await response.text();
    console.error('Transcription error:', error);
    throw new Error(`Transcription failed: ${error}`);
  }

  const result = await response.json();
  console.log('Transcription result:', result);
  return result;
}

/**
 * Process voice command - transcribe and execute
 */
export async function processVoiceCommand(audioUri: string): Promise<ProcessCommandResult> {
  const url = getApiUrl(API_CONFIG.ENDPOINTS.VOICE_PROCESS);
  console.log('Processing voice command:', audioUri);
  console.log('POST to:', url);
  
  const formData = new FormData();
  
  const filename = audioUri.split('/').pop() || 'recording.m4a';
  formData.append('audio_file', {
    uri: audioUri,
    name: filename,
    type: 'audio/m4a',
  } as any);

  const response = await fetch(url, {
    method: 'POST',
    body: formData,
    headers: {
      'ngrok-skip-browser-warning': 'true',
    },
  });

  console.log('Response status:', response.status);

  if (!response.ok) {
    const error = await response.text();
    console.error('Command processing error:', error);
    throw new Error(`Command processing failed: ${error}`);
  }

  return response.json();
}

/**
 * Process text command directly (for testing)
 */
export async function processTextCommand(command: string): Promise<ProcessCommandResult> {
  const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.VOICE_TEXT), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'ngrok-skip-browser-warning': 'true',
    },
    body: JSON.stringify({ command }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Command processing failed: ${error}`);
  }

  return response.json();
}

/**
 * Test backend connection
 */
export async function testConnection(): Promise<boolean> {
  try {
    const url = getApiUrl(API_CONFIG.ENDPOINTS.HEALTH);
    console.log('Testing connection to:', url);
    
    // Try XMLHttpRequest as fallback (sometimes works better in Expo Go)
    return new Promise((resolve) => {
      const xhr = new XMLHttpRequest();
      xhr.open('GET', url);
      xhr.setRequestHeader('ngrok-skip-browser-warning', 'true');
      xhr.timeout = 10000;
      
      xhr.onload = () => {
        console.log('XHR status:', xhr.status);
        resolve(xhr.status >= 200 && xhr.status < 300);
      };
      
      xhr.onerror = (e) => {
        console.error('XHR error:', e);
        resolve(false);
      };
      
      xhr.ontimeout = () => {
        console.error('XHR timeout');
        resolve(false);
      };
      
      xhr.send();
    });
  } catch (err) {
    console.error('Connection test failed:', err);
    return false;
  }
}
