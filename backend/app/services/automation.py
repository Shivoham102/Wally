"""Mobile automation service for interacting with Walmart app."""
import subprocess
import time
from typing import List, Optional
from app.config import settings
from app.utils.selectors import selectors

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
            
            # Helper to find element using UiSelector first, then fallback to XPath/resource_id
            def find_element_by_selector(uiselector: str, xpath: str = "", resource_id: str = "", by_type: str = "clickable"):
                """Find element using UiSelector first, then fallback to XPath or resource_id."""
                try:
                    # Try UiSelector first (most reliable for Android)
                    if uiselector:
                        if by_type == "clickable":
                            return wait.until(EC.element_to_be_clickable((By.ANDROID_UIAUTOMATOR, uiselector)))
                        else:
                            return wait.until(EC.presence_of_element_located((By.ANDROID_UIAUTOMATOR, uiselector)))
                except:
                    pass
                
                # Fallback to XPath
                if xpath:
                    try:
                        if by_type == "clickable":
                            return wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                        else:
                            return wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    except:
                        pass
                
                # Fallback to resource_id
                if resource_id:
                    try:
                        if by_type == "clickable":
                            return wait.until(EC.element_to_be_clickable((By.ID, resource_id)))
                        else:
                            return wait.until(EC.presence_of_element_located((By.ID, resource_id)))
                    except:
                        pass
                
                raise Exception(f"Element not found with UiSelector, XPath, or resource_id")
            
            # Helper to find search bar (handles stale element, uses UiSelector by default)
            def get_search_bar():
                return find_element_by_selector(
                    uiselector=selectors.search_bar_uiselector,
                    xpath=selectors.get("search_bar", {}).get("xpath", ""),
                    resource_id=selectors.search_bar_id
                )
            
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
            
            # Verify results loaded (use products RecyclerView from selectors)
            product_list = find_element_by_selector(
                uiselector=selectors.products_recycler_uiselector,
                xpath=selectors.get("product_list", {}).get("xpath", ""),
                resource_id=selectors.products_recycler_id,
                by_type="presence"
            )
            
            return {"success": True, "message": f"Searched for {item_name}"}
        
        except Exception as e:
            return {"success": False, "message": f"Search failed: {str(e)}"}
    
    async def add_items_to_cart(self, items: List[str]) -> dict:
        """
        Add multiple items to cart in Walmart app.
        
        Args:
            items: List of item names to add (can include "3x milk" format for quantity)
        
        Returns:
            Result dictionary with success status for each item
        """
        results = []
        
        for item in items:
            try:
                # Parse quantity from item
                # Format can be:
                # - "3 milk" (from LLM, preferred)
                # - "3x milk" (from user input/fallback)
                # - "milk x3" (from user input/fallback)
                # - "milk" (default quantity 1)
                quantity = 1
                search_term = item
                
                import re
                
                # Strategy 1: "3 milk" format (from LLM)
                match = re.match(r'^(\d+)\s+(.+)$', item.strip())
                if match:
                    quantity = int(match.group(1))
                    search_term = match.group(2).strip()
                else:
                    # Strategy 2: "3x milk" format (fallback)
                    match = re.match(r'(\d+)x\s*(.+)', item, re.IGNORECASE)
                    if match:
                        quantity = int(match.group(1))
                        search_term = match.group(2).strip()
                    else:
                        # Strategy 3: "milk x3" format (fallback)
                        match = re.match(r'(.+?)\s*x\s*(\d+)', item, re.IGNORECASE)
                        if match:
                            search_term = match.group(1).strip()
                            quantity = int(match.group(2))
                
                # Search for item
                search_result = await self.search_item(search_term)
                
                if search_result.get("success"):
                    # Add first result to cart with specified quantity
                    add_result = await self._add_first_result_to_cart(search_term=search_term, quantity=quantity)
                    results.append({
                        "item": item,
                        "search_term": search_term,
                        "quantity": quantity,
                        "success": add_result.get("success", False),
                        "message": add_result.get("message", "")
                    })
                else:
                    results.append({
                        "item": item,
                        "search_term": search_term,
                        "quantity": quantity,
                        "success": False,
                        "message": f"Failed to search for {search_term}"
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
    
    async def _add_first_result_to_cart(self, search_term: str = None, quantity: int = 1) -> dict:
        """
        Add the first search result to cart directly from search results page.
        Finds the add to cart button within the first product item (no navigation to detail page).
        
        Args:
            search_term: The search term used (optional, for logging)
            quantity: Number of items to add (default: 1)
        
        Returns:
            Result dictionary
        """
        try:
            if not APPIUM_AVAILABLE or not self.driver:
                return {"success": False, "message": "Appium not available"}
            
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Use shorter wait times for better performance (5 seconds is usually enough)
            wait = WebDriverWait(self.driver, 5)
            wait_short = WebDriverWait(self.driver, 3)  # For quick checks
            
            # Wait for product list to load (quick check)
            try:
                product_list = wait_short.until(
                    EC.presence_of_element_located((By.XPATH, selectors.get("product_list", {}).get("xpath", "")))
                )
            except:
                # Fallback to resource ID
                try:
                    product_list = wait_short.until(
                        EC.presence_of_element_located((By.ID, selectors.products_recycler_id))
                    )
                except Exception as e:
                    return {"success": False, "message": f"❌ STEP 1 FAILED - Products RecyclerView not found: {str(e)}"}
            
            # Step 2: Find add to cart button directly (XPath is working based on logs, so try it first)
            try:
                # Since XPath is working (from logs), try it first for speed
                add_to_cart_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, selectors.add_to_cart_xpath))
                )
                add_to_cart_button.click()
                # No sleep needed - click is immediate
                    
            except Exception as e1:
                # Fallback 1: Try UiSelector
                try:
                    add_to_cart_uiselector = selectors.add_to_cart_uiselector
                    if add_to_cart_uiselector:
                        add_to_cart_button = wait.until(
                            EC.element_to_be_clickable((By.ANDROID_UIAUTOMATOR, add_to_cart_uiselector))
                        )
                        add_to_cart_button.click()
                    else:
                        raise Exception("UiSelector not configured")
                except Exception as e2:
                    # Fallback 2: Try resource ID
                    try:
                        resource_id = selectors.get("add_to_cart_button", {}).get("resource_id", "")
                        if resource_id:
                            add_to_cart_button = wait.until(
                                EC.element_to_be_clickable((By.ID, resource_id))
                            )
                            add_to_cart_button.click()
                        else:
                            raise Exception("Resource ID not configured")
                    except Exception as e3:
                        return {"success": False, "message": f"❌ STEP 2 FAILED - Add to Cart button not found. XPath: {str(e1)[:80]}... UiSelector: {str(e2)[:80]}... ResourceID: {str(e3)[:80]}..."}
            
            # Step 3: If quantity > 1, click the plus button (quantity - 1) times
            if quantity > 1:
                try:
                    # Wait for plus button to appear (appears after first add to cart click)
                    time.sleep(0.5)  # Small delay for button to appear
                    
                    # Find plus button using resource_id (stable, not content-desc which is dynamic)
                    plus_button_uiselector = selectors.cart_plus_button_uiselector
                    plus_button_id = selectors.cart_plus_button_id
                    
                    # Try UiSelector first (most reliable)
                    plus_button = None
                    if plus_button_uiselector:
                        try:
                            plus_button = wait.until(
                                EC.element_to_be_clickable((By.ANDROID_UIAUTOMATOR, plus_button_uiselector))
                            )
                        except:
                            pass
                    
                    # Fallback to resource_id
                    if not plus_button and plus_button_id:
                        try:
                            plus_button = wait.until(
                                EC.element_to_be_clickable((By.ID, plus_button_id))
                            )
                        except:
                            pass
                    
                    if not plus_button:
                        return {"success": False, "message": f"❌ STEP 3 FAILED - Plus button not found for increasing quantity to {quantity}"}
                    
                    # Click plus button (quantity - 1) times
                    for i in range(quantity - 1):
                        plus_button.click()
                        time.sleep(0.3)  # Small delay between clicks
                        
                except Exception as e:
                    return {"success": False, "message": f"❌ STEP 3 FAILED - Could not increase quantity to {quantity}. Error: {str(e)}"}
            
            # No need to go back - we're still on search results page
            return {"success": True, "message": f"Added {quantity}x {search_term} to cart from list view"}
        
        except Exception as e:
            return {"success": False, "message": f"Failed to add to cart: {str(e)}"}
    
    def disconnect(self):
        """Disconnect from device."""
        if self.driver:
            self.driver.quit()
            self.driver = None
        self.connected = False


