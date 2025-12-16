import { API_CONFIG, getApiUrl } from './config';

export interface AddItemRequest {
  item: string;
  quantity: number;
}

export interface AddItemsResult {
  intent: string;
  items: AddItemRequest[];
  result: any;
  note: string;
}

export interface AutomationStatus {
  device_connected: boolean;
  walmart_app_ready: boolean;
}

/**
 * Add items to cart via automation (string array version)
 */
export async function addItemsToCart(items: string[]): Promise<AddItemsResult> {
  // Convert string array to AddItemRequest format
  const itemsRequest = items.map(item => ({
    item: item,
    quantity: 1,
  }));
  
  return addItemsToCartStructured(itemsRequest);
}

/**
 * Add items to cart via automation (structured with quantities)
 */
export async function addItemsToCartStructured(items: AddItemRequest[]): Promise<AddItemsResult> {
  const url = getApiUrl(API_CONFIG.ENDPOINTS.AUTOMATION_ADD_ITEMS);
  console.log('Adding items to cart:', items);

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'ngrok-skip-browser-warning': 'true',
    },
    body: JSON.stringify({
      intent: 'add_items',
      items: items,
    }),
  });

  console.log('Add to cart response status:', response.status);

  if (!response.ok) {
    const error = await response.text();
    console.error('Add to cart error:', error);
    throw new Error(`Failed to add items: ${error}`);
  }

  return response.json();
}

/**
 * Get automation service status
 */
export async function getAutomationStatus(): Promise<AutomationStatus> {
  const url = getApiUrl(API_CONFIG.ENDPOINTS.AUTOMATION_STATUS);
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'ngrok-skip-browser-warning': 'true',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get automation status');
  }

  return response.json();
}

/**
 * Connect to Android device
 */
export async function connectDevice(): Promise<any> {
  const url = getApiUrl('/api/v1/automation/connect');
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'ngrok-skip-browser-warning': 'true',
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to connect device: ${error}`);
  }

  return response.json();
}

/**
 * Open Walmart app on device
 */
export async function openWalmartApp(): Promise<any> {
  const url = getApiUrl('/api/v1/automation/open-walmart');
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'ngrok-skip-browser-warning': 'true',
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to open Walmart app: ${error}`);
  }

  return response.json();
}

