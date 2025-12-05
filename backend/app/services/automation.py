"""Mobile automation service for interacting with Walmart app."""
import subprocess
import time
from typing import List, Optional
from app.config import settings

try:
    from appium import webdriver
    from appium.options.android import UiAutomator2Options
    APPIUM_AVAILABLE = True
except ImportError:
    APPIUM_AVAILABLE = False


class AutomationService:
    """Service for automating interactions with the Walmart mobile app."""
    
    def __init__(self):
        self.driver: Optional[webdriver.Remote] = None
        self.connected = False
    
    async def connect_device(self) -> dict:
        """
        Connect to Android device via ADB/Appium.
        
        Returns:
            Connection status dictionary
        """
        try:
            # Check if device is connected via ADB
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True
            )
            
            if "device" not in result.stdout:
                return {
                    "connected": False,
                    "message": "No Android device found. Please connect a device via USB and enable USB debugging."
                }
            
            # Try to initialize Appium driver
            if APPIUM_AVAILABLE:
                try:
                    options = UiAutomator2Options()
                    options.platform_name = "Android"
                    options.automation_name = "UiAutomator2"  # Required for Android
                    options.no_reset = True  # Don't reset app state
                    options.full_reset = False
                    options.adb_exec_timeout = 60000  # Increase timeout to 60 seconds
                    options.new_command_timeout = 300  # Keep session alive for 5 minutes
                    
                    if settings.android_device_id:
                        options.udid = settings.android_device_id
                    
                    self.driver = webdriver.Remote(
                        settings.appium_server_url,
                        options=options
                    )
                    self.connected = True
                    
                    return {
                        "connected": True,
                        "message": "Successfully connected via Appium"
                    }
                except Exception as appium_error:
                    # Fall back to ADB if Appium fails
                    self.connected = True
                    return {
                        "connected": True,
                        "message": f"Connected via ADB fallback (Appium failed: {str(appium_error)})"
                    }
            else:
                # Use ADB-only mode
                self.connected = True
                return {
                    "connected": True,
                    "message": "Connected via ADB (Appium not available)"
                }
        
        except Exception as e:
            return {
                "connected": False,
                "message": f"Connection failed: {str(e)}"
            }
    
    async def get_status(self) -> dict:
        """Get automation service status."""
        return {
            "connected": self.connected,
            "appium_available": APPIUM_AVAILABLE,
            "driver_active": self.driver is not None
        }
    
    async def open_walmart_app(self) -> dict:
        """
        Open Walmart app on connected device.
        
        Returns:
            Status dictionary
        """
        try:
            if not self.connected:
                await self.connect_device()
            
            if APPIUM_AVAILABLE and self.driver:
                # Use Appium to open app
                self.driver.activate_app(settings.walmart_app_package)
            else:
                # Use ADB to open app
                subprocess.run([
                    "adb", "shell", "am", "start",
                    "-n", f"{settings.walmart_app_package}/{settings.walmart_app_activity}"
                ])
            
            return {"success": True, "message": "Walmart app opened"}
        
        except Exception as e:
            return {"success": False, "message": f"Failed to open app: {str(e)}"}
    
    async def search_item(self, item_name: str) -> dict:
        """
        Search for an item in Walmart app.
        Simple step-by-step: tap search bar, type, press enter.
        
        Args:
            item_name: Name of item to search
        
        Returns:
            Search result dictionary
        """
        try:
            if not self.connected:
                await self.connect_device()
            
            # Make sure Walmart app is open
            await self.open_walmart_app()
            time.sleep(2)
            
            if not APPIUM_AVAILABLE or not self.driver:
                return {"success": False, "message": "Appium not available"}
            
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            wait = WebDriverWait(self.driver, 10)
            SEARCH_BAR_ID = "com.walmart.android:id/search_view"
            
            # Helper to find search bar (handles stale element)
            def get_search_bar():
                return wait.until(EC.element_to_be_clickable((By.ID, SEARCH_BAR_ID)))
            
            # Step 1: Tap on search bar
            search_bar = get_search_bar()
            search_bar.click()
            time.sleep(1.5)  # Wait for keyboard to fully appear
            
            # Step 2: Type the product name (re-find to handle stale element)
            search_bar = get_search_bar()
            search_bar.send_keys(item_name)
            time.sleep(1)  # Wait for text to be entered
            
            # Step 3: Press Enter key on keyboard (Android keycode 66 = ENTER)
            self.driver.press_keycode(66)
            time.sleep(4)  # Wait for results to load
            
            # Verify results loaded
            PRODUCT_LIST_ID = "com.walmart.android:id/recycler_view"
            wait.until(EC.presence_of_element_located((By.ID, PRODUCT_LIST_ID)))
            
            return {"success": True, "message": f"Searched for {item_name}"}
        
        except Exception as e:
            return {"success": False, "message": f"Search failed: {str(e)}"}
    
    async def add_items_to_cart(self, items: List[str]) -> dict:
        """
        Add multiple items to cart in Walmart app.
        
        Args:
            items: List of item names to add
        
        Returns:
            Result dictionary with success status for each item
        """
        results = []
        
        for item in items:
            try:
                # Search for item
                search_result = await self.search_item(item)
                
                if search_result.get("success"):
                    # Add first result to cart
                    add_result = await self._add_first_result_to_cart(search_term=item)
                    results.append({
                        "item": item,
                        "success": add_result.get("success", False),
                        "message": add_result.get("message", "")
                    })
                else:
                    results.append({
                        "item": item,
                        "success": False,
                        "message": f"Failed to search for {item}"
                    })
            
            except Exception as e:
                results.append({
                    "item": item,
                    "success": False,
                    "message": f"Error: {str(e)}"
                })
        
        return {
            "success": all(r["success"] for r in results),
            "results": results
        }
    
    async def _add_first_result_to_cart(self, search_term: str = None) -> dict:
        """
        Add the first search result to cart.
        Simple step-by-step: tap first product, tap add to cart button.
        
        Args:
            search_term: The search term used (optional, for logging)
        
        Returns:
            Result dictionary
        """
        try:
            if not APPIUM_AVAILABLE or not self.driver:
                return {"success": False, "message": "Appium not available"}
            
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            wait = WebDriverWait(self.driver, 10)
            
            # Wait for product list
            PRODUCT_LIST_ID = "com.walmart.android:id/recycler_view"
            wait.until(EC.presence_of_element_located((By.ID, PRODUCT_LIST_ID)))
            time.sleep(2)
            
            # Step 1: Tap on first product (ViewGroup[2], skip metadata ViewGroup[1])
            FIRST_PRODUCT_XPATH = "//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]"
            first_product = wait.until(EC.element_to_be_clickable((By.XPATH, FIRST_PRODUCT_XPATH)))
            first_product.click()
            time.sleep(2)  # Wait for product page
            
            # Step 2: Tap on add to cart button
            ADD_TO_CART_XPATH = "(//android.view.ViewGroup[@resource-id=\"com.walmart.android:id/quantitystepper_root\"])[1]"
            add_to_cart_button = wait.until(EC.element_to_be_clickable((By.XPATH, ADD_TO_CART_XPATH)))
            add_to_cart_button.click()
            time.sleep(1)
            
            # Go back for next item
            self.driver.back()
            time.sleep(1)
            
            return {"success": True, "message": "Item added to cart"}
        
        except Exception as e:
            return {"success": False, "message": f"Failed to add to cart: {str(e)}"}
    
    def disconnect(self):
        """Disconnect from device."""
        if self.driver:
            self.driver.quit()
            self.driver = None
        self.connected = False


