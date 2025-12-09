"""Mobile automation service for interacting with Walmart app."""
import re
import subprocess
import time
from typing import List, Optional

from app.config import settings
from app.utils.selectors import selectors

# Conditional imports for Selenium and Appium
try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    # Create dummy classes to avoid NameError
    class By:
        ID = "id"
        XPATH = "xpath"
        ANDROID_UIAUTOMATOR = "android_uiautomator"
    class Keys:
        pass
    class EC:
        pass
    class WebDriverWait:
        pass

try:
    from appium import webdriver
    from appium.options.android import UiAutomator2Options
    APPIUM_AVAILABLE = True
except ImportError:
    APPIUM_AVAILABLE = False
    webdriver = None
    UiAutomator2Options = None


class AutomationService:
    """Service for automating interactions with the Walmart mobile app."""
    
    def __init__(self):
        self.driver = None  # Will be webdriver.Remote when connected
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
            
            time.sleep(2)  # Wait for app to load
            
            # Set address and delivery option early (product listings change based on address)
            address_result = await self.set_address_and_delivery()
            if not address_result.get("success"):
                # Log warning but don't fail - app is still open
                return {
                    "success": True,
                    "message": "Walmart app opened",
                    "address_set": False,
                    "address_warning": address_result.get("message", "Could not set address")
                }
            
            return {
                "success": True,
                "message": "Walmart app opened",
                "address_set": True
            }
        
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
            
            if not SELENIUM_AVAILABLE:
                return {"success": False, "message": "Selenium not installed. Please install: pip install selenium"}
            
            if not APPIUM_AVAILABLE or not self.driver:
                if not APPIUM_AVAILABLE:
                    return {"success": False, "message": "Appium not installed. Please install: pip install Appium-Python-Client"}
                if not self.driver:
                    return {"success": False, "message": "Device not connected. Please connect device first via /api/v1/automation/connect"}
            
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
    
    async def add_items_to_cart_structured(self, items: List[dict]) -> dict:
        """
        Add multiple items to cart using structured format (no regex parsing).
        
        Args:
            items: List of dicts with "item" and "quantity" keys
                  Format: [{"item": "milk", "quantity": 2}, {"item": "eggs", "quantity": 1}]
        
        Returns:
            Result dictionary with success status for each item
        """
        results = []
        
        for item_data in items:
            try:
                # Extract item name and quantity directly (no parsing needed)
                item_name = item_data.get("item", "")
                quantity = item_data.get("quantity", 1)
                
                if not item_name:
                    results.append({
                        "item": item_data,
                        "success": False,
                        "message": "Item name is required"
                    })
                    continue
                
                # Search for item
                search_result = await self.search_item(item_name)
                
                if search_result.get("success"):
                    # Add first result to cart with specified quantity
                    add_result = await self._add_first_result_to_cart(search_term=item_name, quantity=quantity)
                    results.append({
                        "item": item_name,
                        "quantity": quantity,
                        "success": add_result.get("success", False),
                        "message": add_result.get("message", "")
                    })
                else:
                    results.append({
                        "item": item_name,
                        "quantity": quantity,
                        "success": False,
                        "message": f"Failed to search for {item_name}"
                    })
            
            except Exception as e:
                results.append({
                    "item": item_data,
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
            if not SELENIUM_AVAILABLE:
                return {"success": False, "message": "Selenium not installed. Please install: pip install selenium"}
            
            if not APPIUM_AVAILABLE or not self.driver:
                if not APPIUM_AVAILABLE:
                    return {"success": False, "message": "Appium not installed. Please install: pip install Appium-Python-Client"}
                if not self.driver:
                    return {"success": False, "message": "Device not connected. Please connect device first via /api/v1/automation/connect"}
            
            # Use shorter wait times for better performance (5 seconds is usually enough)
            wait = WebDriverWait(self.driver, 5)
            wait_short = WebDriverWait(self.driver, 3)  # For quick checks
            
            # Wait for product list to load (quick check) - this is the main container
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
            
            # Get the products RecyclerView (recycler_view) that contains only actual products (no ads)
            # This is different from product_list which is the main container
            products_recycler = None
            try:
                products_recycler = wait_short.until(
                    EC.presence_of_element_located((By.XPATH, selectors.get("products_recycler_view", {}).get("xpath", "")))
                )
            except:
                # Fallback to resource ID
                try:
                    products_recycler = wait_short.until(
                        EC.presence_of_element_located((By.ID, selectors.get("products_recycler_view", {}).get("resource_id", "")))
                    )
                except:
                    pass  # If we can't find it, continue without scrolling
            
            # Scroll the page to position the RecyclerView's top edge at the top of the screen
            # This brings the RecyclerView container itself to the top, not scrolling its content
            if products_recycler:
                try:
                    recycler_location = products_recycler.location
                    recycler_top_y = recycler_location['y']
                    
                    # Get screen dimensions
                    screen_size = self.driver.get_window_size()
                    # Account for status bar/action bar - we want RecyclerView just below it
                    # Typically around 100-150px from top for action bar
                    target_top_y = 150  # Target position accounting for app bar
                    screen_center_x = int(screen_size['width'] / 2)
                    
                    # Calculate exact scroll needed: difference between RecyclerView's current top and target
                    scroll_needed = recycler_top_y - target_top_y
                    
                    # Only scroll if RecyclerView is significantly below target (with larger threshold)
                    if scroll_needed > 30:  # Only scroll if more than 30px off
                        # Scroll the page by the calculated amount
                        # Use a smaller scroll distance to avoid over-scrolling
                        # Start from middle of screen (safe from gesture zones)
                        start_y = int(screen_size['height'] * 0.5)
                        # Scroll by the exact amount needed, but cap it to avoid over-scrolling
                        max_scroll = int(screen_size['height'] * 0.3)  # Max 30% of screen height
                        scroll_amount = min(scroll_needed, max_scroll)
                        end_y = int(start_y - scroll_amount)
                        
                        # Ensure we don't scroll outside screen bounds
                        min_y = 100  # Minimum Y (with margin to avoid gesture zones)
                        if end_y < min_y:
                            end_y = min_y
                        
                        self.driver.swipe(
                            screen_center_x,
                            start_y,
                            screen_center_x,
                            end_y,
                            250  # Slower, more controlled scroll
                        )
                        
                except Exception as e:
                    # If scroll fails, continue anyway - RecyclerView might already be at top
                    pass
            
            # Helper function to find and scroll element into view, then click
            def find_and_click_element(xpath=None, uiselector=None, resource_id=None, scroll_into_view=True):
                """Find element, scroll into view if needed, then click."""
                element = None
                
                # Try to find element (presence check, not clickable - element might be off-screen)
                if xpath:
                    try:
                        element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    except:
                        pass
                
                if not element and uiselector:
                    try:
                        element = wait.until(EC.presence_of_element_located((By.ANDROID_UIAUTOMATOR, uiselector)))
                    except:
                        pass
                
                if not element and resource_id:
                    try:
                        element = wait.until(EC.presence_of_element_located((By.ID, resource_id)))
                    except:
                        pass
                
                if not element:
                    return False, "Element not found"
                
                # VALIDATION: Ensure element is NOT in an ad container
                # Ads don't have product_tile_list_view or quantitystepper_root, but let's double-check
                try:
                    # Check if element is inside ad_container
                    parent_xpath = "./ancestor::android.widget.FrameLayout[@resource-id='com.walmart.android:id/ad_container']"
                    ad_parents = element.find_elements(By.XPATH, parent_xpath)
                    if ad_parents:
                        return False, "Element is inside ad_container - this should not happen! Ads don't have product_tile_list_view or quantitystepper_root."
                    
                    # Also verify element is inside a product_tile_list_view (for quantitystepper_root)
                    if resource_id and "quantitystepper" in resource_id:
                        product_parent_xpath = "./ancestor::android.view.ViewGroup[@resource-id='com.walmart.android:id/product_tile_list_view']"
                        product_parents = element.find_elements(By.XPATH, product_parent_xpath)
                        if not product_parents:
                            return False, "quantitystepper_root not inside product_tile_list_view - might be wrong element"
                except:
                    pass  # If validation fails, continue anyway (better to try than fail)
                
                # Always scroll element into view to ensure button is fully visible
                if scroll_into_view:
                    max_scroll_attempts = 5  # Prevent infinite scrolling
                    scroll_attempt = 0
                    
                    while scroll_attempt < max_scroll_attempts:
                        try:
                            # Get element location and size
                            location = element.location
                            size = element.size
                            screen_size = self.driver.get_window_size()
                            
                            # Calculate button's bottom Y coordinate (we want this visible)
                            button_bottom_y = location['y'] + size['height']
                            button_top_y = location['y']
                            
                            # Check if button is fully visible (top and bottom within screen bounds)
                            # Add some margin (50px) to ensure it's comfortably visible
                            margin = 50
                            screen_bottom = screen_size['height'] - margin
                            screen_top = margin
                            
                            # If button is fully visible, break
                            if button_top_y >= screen_top and button_bottom_y <= screen_bottom:
                                break
                            
                            # Determine scroll direction and amount
                            if button_bottom_y > screen_bottom:
                                # Button is below screen, scroll down (swipe up)
                                scroll_amount = min(button_bottom_y - screen_bottom + margin, screen_size['height'] * 0.5)
                                self.driver.swipe(
                                    int(screen_size['width'] / 2),
                                    int(screen_size['height'] * 0.7),  # Start from 70% down
                                    int(screen_size['width'] / 2),
                                    int(screen_size['height'] * 0.7 - scroll_amount),  # Move up
                                    600  # duration in ms
                                )
                            elif button_top_y < screen_top:
                                # Button is above screen, scroll up (swipe down)
                                scroll_amount = min(screen_top - button_top_y + margin, screen_size['height'] * 0.5)
                                self.driver.swipe(
                                    int(screen_size['width'] / 2),
                                    int(screen_size['height'] * 0.3),  # Start from 30% down
                                    int(screen_size['width'] / 2),
                                    int(screen_size['height'] * 0.3 + scroll_amount),  # Move down
                                    600  # duration in ms
                                )
                            else:
                                # Button is partially visible, fine-tune scroll
                                if button_bottom_y > screen_bottom:
                                    # Need to scroll down a bit more
                                    self.driver.swipe(
                                        int(screen_size['width'] / 2),
                                        int(screen_size['height'] * 0.8),
                                        int(screen_size['width'] / 2),
                                        int(screen_size['height'] * 0.5),
                                        500
                                    )
                            
                            time.sleep(0.4)  # Wait for scroll to complete
                            scroll_attempt += 1
                            
                            # Re-find element after scroll (location may have changed)
                            try:
                                if xpath:
                                    element = self.driver.find_element(By.XPATH, xpath)
                                elif uiselector:
                                    element = self.driver.find_element(By.ANDROID_UIAUTOMATOR, uiselector)
                                elif resource_id:
                                    element = self.driver.find_element(By.ID, resource_id)
                            except:
                                break  # Element lost, break and try to click anyway
                                
                        except Exception as e:
                            # If scrolling fails, break and try clicking
                            break
                
                # Now try to click (element should be visible)
                try:
                    # Wait for element to be clickable (now that it's scrolled into view)
                    clickable_element = wait.until(EC.element_to_be_clickable(element))
                    clickable_element.click()
                    return True, "Success"
                except Exception as e:
                    return False, f"Element found but not clickable: {str(e)}"
            
            # Step 2: Find add to cart button directly (use scoped XPath first to avoid ads)
            try:
                # Try scoped XPath first - ensures we're in products RecyclerView, not ads
                scoped_xpath = selectors.add_to_cart_xpath_scoped
                if scoped_xpath:
                    success, msg = find_and_click_element(xpath=scoped_xpath)
                    if success:
                        pass  # Success, continue
                    else:
                        raise Exception(msg)
                else:
                    raise Exception("Scoped XPath not available")
                # No sleep needed - click is immediate
                    
            except Exception as e1:
                # Fallback to regular XPath
                try:
                    success, msg = find_and_click_element(xpath=selectors.add_to_cart_xpath)
                    if not success:
                        raise Exception(msg)
                except Exception as e1_alt:
                    # Fallback 1: Try UiSelector
                    try:
                        add_to_cart_uiselector = selectors.add_to_cart_uiselector
                        if add_to_cart_uiselector:
                            success, msg = find_and_click_element(uiselector=add_to_cart_uiselector)
                            if not success:
                                raise Exception(msg)
                        else:
                            raise Exception("UiSelector not configured")
                    except Exception as e2:
                        # Fallback 2: Try resource ID
                        try:
                            resource_id = selectors.get("add_to_cart_button", {}).get("resource_id", "")
                            if resource_id:
                                success, msg = find_and_click_element(resource_id=resource_id)
                                if not success:
                                    raise Exception(msg)
                            else:
                                raise Exception("Resource ID not configured")
                        except Exception as e3:
                            return {"success": False, "message": f"❌ STEP 2 FAILED - Add to Cart button not found. ScopedXPath: {str(e1)[:80]}... XPath: {str(e1_alt)[:80]}... UiSelector: {str(e2)[:80]}... ResourceID: {str(e3)[:80]}..."}
            
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
    
    async def reorder_last_order(self) -> dict:
        """
        Reorder items from the last order in Walmart app for a specific customer.
        Uses "View all" button to access purchase history, then loops through orders
        skipping invalid ones (still arriving or missing customer name).
        
        Returns:
            Result dictionary
        """
        try:
            if not SELENIUM_AVAILABLE:
                return {"success": False, "message": "Selenium not installed. Please install: pip install selenium"}
            
            if not APPIUM_AVAILABLE:
                return {"success": False, "message": "Appium not installed. Please install: pip install Appium-Python-Client"}
            
            # Auto-connect if not connected
            if not self.connected:
                await self.connect_device()
            
            if not self.driver:
                return {"success": False, "message": "Device not connected. Please connect device first via /api/v1/automation/connect"}
            
            # Check if customer name is configured
            if not settings.customer_name:
                return {"success": False, "message": "Customer name not configured. Please set CUSTOMER_NAME in environment variables."}
            
            # Make sure Walmart app is open
            await self.open_walmart_app()
            time.sleep(2)
            
            wait = WebDriverWait(self.driver, 10)
            
            # Step 1: Navigate to Account tab (bottom navigation)
            try:
                account_button_id = selectors.get("account_button", {}).get("resource_id", "")
                if account_button_id:
                    account_tab = wait.until(
                        EC.element_to_be_clickable((By.ID, account_button_id))
                    )
                    account_tab.click()
                    time.sleep(2)  # Wait for account page to load
                else:
                    return {"success": False, "message": "Account button selector not configured"}
            except Exception as e:
                return {"success": False, "message": f"Failed to navigate to Account: {str(e)}"}
            
            # Step 2: Click "View all" button to open purchase history
            try:
                view_all_button_id = selectors.get("view_all_orders_button", {}).get("resource_id", "")
                view_all_button_xpath = selectors.get("view_all_orders_button", {}).get("xpath", "")
                
                view_all_button = None
                if view_all_button_id:
                    try:
                        view_all_button = wait.until(
                            EC.element_to_be_clickable((By.ID, view_all_button_id))
                        )
                    except:
                        pass
                
                if not view_all_button and view_all_button_xpath:
                    try:
                        view_all_button = wait.until(
                            EC.element_to_be_clickable((By.XPATH, view_all_button_xpath))
                        )
                    except:
                        pass
                
                if not view_all_button:
                    return {"success": False, "message": "Could not find 'View all' button"}
                
                view_all_button.click()
                time.sleep(2)  # Wait for purchase history page to load
            except Exception as e:
                return {"success": False, "message": f"Failed to click 'View all' button: {str(e)}"}
            
            # Step 3: Loop through order cards until we find a valid match
            max_attempts = 20  # Maximum number of orders to check
            attempt = 0
            checked_card_positions = set()  # Track which card positions we've already checked
            
            while attempt < max_attempts:
                try:
                    # Step 3a: Find all order cards in the RecyclerView (refetch each time)
                    order_card_id = selectors.get("purchase_history_order_card", {}).get("resource_id", "")
                    order_card_xpath = selectors.get("purchase_history_order_card", {}).get("xpath", "")
                    
                    # Get all order cards (fresh fetch)
                    order_cards = []
                    if order_card_id:
                        try:
                            order_cards = self.driver.find_elements(By.ID, order_card_id)
                        except:
                            pass
                    
                    if not order_cards and order_card_xpath:
                        try:
                            order_cards = self.driver.find_elements(By.XPATH, order_card_xpath)
                        except:
                            pass
                    
                    if not order_cards:
                        return {"success": False, "message": "Could not find any order cards in purchase history"}
                    
                    # Step 3b: Find the first visible card we haven't checked yet
                    card_found = False
                    
                    for card_index, card in enumerate(order_cards):
                        try:
                            # Check if card is displayed
                            if not card.is_displayed():
                                continue
                            
                            # Get card position to track if we've checked it
                            try:
                                card_location = card.location
                                card_position = (card_location['x'], card_location['y'])
                                
                                # Skip if we've already checked this position
                                if card_position in checked_card_positions:
                                    continue
                            except:
                                # If we can't get location, use index as fallback
                                if card_index in checked_card_positions:
                                    continue
                            
                            # Check parentContainer to see if order is still arriving (BEFORE tapping)
                            # The content-desc with order status is on parentContainer, not the first ViewGroup
                            should_skip = False
                            try:
                                # Check parentContainer first (this is where the content-desc actually is)
                                parent_container = card.find_element(
                                    By.XPATH,
                                    ".//android.view.ViewGroup[@resource-id='com.walmart.android:id/parentContainer']"
                                )
                                content_desc = parent_container.get_attribute("content-desc") or ""
                                
                                # Skip if order is still arriving (content-desc contains "Arrives")
                                if "arrives" in content_desc.lower():
                                    should_skip = True
                            except:
                                # Fallback: try checking the first ViewGroup child if parentContainer not found
                                try:
                                    first_viewgroup = card.find_element(
                                        By.XPATH,
                                        ".//android.view.ViewGroup[1]"
                                    )
                                    content_desc = first_viewgroup.get_attribute("content-desc") or ""
                                    if "arrives" in content_desc.lower():
                                        should_skip = True
                                except:
                                    pass  # If we can't check, proceed (might be a valid card)
                            
                            # If card should be skipped, scroll past it without tapping
                            if should_skip:
                                # Mark this card as checked
                                try:
                                    checked_card_positions.add(card_position)
                                except:
                                    checked_card_positions.add(card_index)
                                
                                # Scroll up based on the order card itself (purchasehistory_orderStatus_tracker)
                                card_location = card.location
                                card_size = card.size
                                card_top_y = card_location['y']
                                
                                screen_size = self.driver.get_window_size()
                                # Scroll up to move past this card (swipe down: from 70% to 30%)
                                self.driver.swipe(
                                    int(screen_size['width'] / 2),
                                    int(screen_size['height'] * 0.7),
                                    int(screen_size['width'] / 2),
                                    int(screen_size['height'] * 0.3),
                                    500
                                )
                                time.sleep(0.5)
                                
                                attempt += 1
                                card_found = True
                                continue  # Skip to next card without tapping
                            
                            # Mark this card as checked before opening it (only if not skipping)
                            try:
                                checked_card_positions.add(card_position)
                            except:
                                checked_card_positions.add(card_index)
                            
                            # Card is not "arriving", click on image_carousel to open details
                            try:
                                image_carousel = card.find_element(
                                    By.XPATH,
                                    ".//android.widget.LinearLayout[@resource-id='com.walmart.android:id/image_carousel']"
                                )
                                image_carousel.click()
                                time.sleep(2)  # Wait for order details page to load
                            except:
                                # If image_carousel not found, skip this card
                                attempt += 1
                                continue
                            
                            # Step 3c: Scroll payment method card to bottom of screen so customer name and reorder button are visible
                            payment_card_xpath = selectors.get("payment_method_card", {}).get("xpath", "")
                            
                            payment_card = None
                            # First, try to find the card - if not visible, scroll down to bring it into view
                            max_scroll_attempts = 5
                            scroll_attempt = 0
                            while scroll_attempt < max_scroll_attempts:
                                try:
                                    payment_card = self.driver.find_element(By.XPATH, payment_card_xpath)
                                    # Check if card is visible on screen
                                    if payment_card.is_displayed():
                                        card_location = payment_card.location
                                        screen_size = self.driver.get_window_size()
                                        # If card is visible (even partially), break
                                        if card_location['y'] < screen_size['height']:
                                            break
                                except:
                                    pass
                                
                                # Card not visible, scroll down to bring it into view
                                screen_size = self.driver.get_window_size()
                                self.driver.swipe(
                                    int(screen_size['width'] / 2),
                                    int(screen_size['height'] * 0.7),
                                    int(screen_size['width'] / 2),
                                    int(screen_size['height'] * 0.3),
                                    500
                                )
                                time.sleep(0.5)
                                scroll_attempt += 1
                            
                            if payment_card:
                                try:
                                    # Now position payment card bottom at the bottom of the screen
                                    card_location = payment_card.location
                                    card_size = payment_card.size
                                    card_bottom_y = card_location['y'] + card_size['height']
                                    
                                    screen_size = self.driver.get_window_size()
                                    target_y = screen_size['height']  # Bottom of screen
                                    scroll_needed = card_bottom_y - target_y
                                    
                                    if abs(scroll_needed) > 10:
                                        if scroll_needed > 0:
                                            # Card bottom is below screen bottom, scroll content up (swipe down)
                                            self.driver.swipe(
                                                int(screen_size['width'] / 2),
                                                int(screen_size['height'] * 0.7),
                                                int(screen_size['width'] / 2),
                                                int(screen_size['height'] * 0.7 - scroll_needed),
                                                500
                                            )
                                        else:
                                            # Card bottom is above screen bottom, scroll content down (swipe up)
                                            self.driver.swipe(
                                                int(screen_size['width'] / 2),
                                                int(screen_size['height'] * 0.3),
                                                int(screen_size['width'] / 2),
                                                int(screen_size['height'] * 0.3 - scroll_needed),
                                                500
                                            )
                                        time.sleep(0.5)
                                except:
                                    pass  # If we can't position it, continue anyway
                            
                            # Step 3d: Check if customer name exists and matches
                            customer_name_id = selectors.get("order_details_customer_name", {}).get("resource_id", "")
                            customer_name_xpath = selectors.get("order_details_customer_name", {}).get("xpath", "")
                            
                            customer_name_element = None
                            if customer_name_id:
                                try:
                                    customer_name_element = wait.until(
                                        EC.presence_of_element_located((By.ID, customer_name_id))
                                    )
                                except:
                                    pass
                            
                            if not customer_name_element and customer_name_xpath:
                                try:
                                    customer_name_element = wait.until(
                                        EC.presence_of_element_located((By.XPATH, customer_name_xpath))
                                    )
                                except:
                                    pass
                            
                            # If customer name element doesn't exist, go back, scroll card to top, and try next
                            if not customer_name_element:
                                self.driver.back()
                                time.sleep(1.5)
                                
                                # Scroll current card close to top of screen
                                try:
                                    # Refetch card after going back to get current position
                                    order_cards_after_back = self.driver.find_elements(By.ID, order_card_id) if order_card_id else []
                                    if not order_cards_after_back:
                                        order_cards_after_back = self.driver.find_elements(By.XPATH, order_card_xpath) if order_card_xpath else []
                                    
                                    if order_cards_after_back and card_index < len(order_cards_after_back):
                                        current_card = order_cards_after_back[card_index]
                                        card_location = current_card.location
                                        card_top_y = card_location['y']
                                        screen_size = self.driver.get_window_size()
                                        target_top_y = int(screen_size['height'] * 0.1)  # 10% from top
                                        scroll_needed = card_top_y - target_top_y
                                        
                                        if abs(scroll_needed) > 10:
                                            if scroll_needed > 0:
                                                # Card is below target, scroll content up (swipe down: from 70% to 30%)
                                                self.driver.swipe(
                                                    int(screen_size['width'] / 2),
                                                    int(screen_size['height'] * 0.7),
                                                    int(screen_size['width'] / 2),
                                                    int(screen_size['height'] * 0.3),
                                                    500
                                                )
                                            else:
                                                # Card is above target, scroll content down (swipe up: from 30% to 70%)
                                                self.driver.swipe(
                                                    int(screen_size['width'] / 2),
                                                    int(screen_size['height'] * 0.3),
                                                    int(screen_size['width'] / 2),
                                                    int(screen_size['height'] * 0.7),
                                                    500
                                                )
                                            time.sleep(0.5)
                                except:
                                    pass
                                
                                attempt += 1
                                card_found = True
                                break  # Break to refetch cards and click next card's image_carousel
                            
                            # Get customer name text
                            order_customer_name = customer_name_element.text.strip()
                            
                            # Step 3e: Compare with configured customer name (case-insensitive)
                            if order_customer_name.lower() == settings.customer_name.lower():
                                # Name matches! order_details_card is already scrolled to 50% (done above)
                                # Find and click reorder button
                                reorder_button_id = selectors.get("reorder_all_items_button", {}).get("resource_id", "")
                                reorder_button_xpath = selectors.get("reorder_all_items_button", {}).get("xpath", "")
                                
                                reorder_button = None
                                if reorder_button_id:
                                    try:
                                        reorder_button = wait.until(
                                            EC.element_to_be_clickable((By.ID, reorder_button_id))
                                        )
                                    except:
                                        pass
                                
                                if not reorder_button and reorder_button_xpath:
                                    try:
                                        reorder_button = wait.until(
                                            EC.element_to_be_clickable((By.XPATH, reorder_button_xpath))
                                        )
                                    except:
                                        pass
                                
                                if not reorder_button:
                                    return {"success": False, "message": "Could not find reorder button"}
                                
                                # Click the button
                                reorder_button.click()
                                time.sleep(2)  # Wait for items to be added to cart
                                return {
                                    "success": True,
                                    "message": f"Successfully reordered order for {order_customer_name}",
                                    "customer_name": order_customer_name
                                }
                            else:
                                # Name doesn't match, go back, scroll card to top, and try next
                                self.driver.back()
                                time.sleep(1.5)
                                
                                # Scroll current card close to top of screen
                                try:
                                    # Refetch card after going back to get current position
                                    order_cards_after_back = self.driver.find_elements(By.ID, order_card_id) if order_card_id else []
                                    if not order_cards_after_back:
                                        order_cards_after_back = self.driver.find_elements(By.XPATH, order_card_xpath) if order_card_xpath else []
                                    
                                    if order_cards_after_back and card_index < len(order_cards_after_back):
                                        current_card = order_cards_after_back[card_index]
                                        card_location = current_card.location
                                        card_top_y = card_location['y']
                                        screen_size = self.driver.get_window_size()
                                        target_top_y = int(screen_size['height'] * 0.1)  # 10% from top
                                        scroll_needed = card_top_y - target_top_y
                                        
                                        if abs(scroll_needed) > 10:
                                            if scroll_needed > 0:
                                                # Card is below target, scroll content up (swipe down: from 70% to 30%)
                                                self.driver.swipe(
                                                    int(screen_size['width'] / 2),
                                                    int(screen_size['height'] * 0.7),
                                                    int(screen_size['width'] / 2),
                                                    int(screen_size['height'] * 0.3),
                                                    500
                                                )
                                            else:
                                                # Card is above target, scroll content down (swipe up: from 30% to 70%)
                                                self.driver.swipe(
                                                    int(screen_size['width'] / 2),
                                                    int(screen_size['height'] * 0.3),
                                                    int(screen_size['width'] / 2),
                                                    int(screen_size['height'] * 0.7),
                                                    500
                                                )
                                            time.sleep(0.5)
                                except:
                                    pass
                                
                                attempt += 1
                                card_found = True
                                break  # Break to refetch cards and click next card's image_carousel
                        
                        except Exception as e:
                            # Error processing this card, go back if we're on details page, then continue
                            try:
                                self.driver.back()
                                time.sleep(1)
                            except:
                                pass
                            attempt += 1
                            continue
                    
                    # If no card was found/processed, scroll down to load more
                    if not card_found:
                        screen_size = self.driver.get_window_size()
                        self.driver.swipe(
                            int(screen_size['width'] / 2),
                            int(screen_size['height'] * 0.7),
                            int(screen_size['width'] / 2),
                            int(screen_size['height'] * 0.3),
                            600
                        )
                        time.sleep(1)
                        attempt += 1
                
                except Exception as e:
                    return {"success": False, "message": f"Error checking orders: {str(e)}"}
            
            return {"success": False, "message": f"Could not find matching order for customer '{settings.customer_name}' after checking {max_attempts} orders"}
        
        except Exception as e:
            return {"success": False, "message": f"Failed to reorder: {str(e)}"}
    
    async def set_address_and_delivery(self) -> dict:
        """
        Set address and delivery option on home page.
        This should be called early as product listings change based on address.
        
        Steps:
        1. Open address accordion (click collapsed view)
        2. Click on delivery option
        3. Check if address in global_intent_center_expanded_large_card_top matches stored address
        4. If not, click on it and do scrolling/finding process with matching names
        
        Returns:
            Result dictionary
        """
        try:
            if not SELENIUM_AVAILABLE:
                return {"success": False, "message": "Selenium not installed. Please install: pip install selenium"}
            
            if not APPIUM_AVAILABLE or not self.driver:
                if not APPIUM_AVAILABLE:
                    return {"success": False, "message": "Appium not installed. Please install: pip install Appium-Python-Client"}
                if not self.driver:
                    return {"success": False, "message": "Device not connected. Please connect device first via /api/v1/automation/connect"}
            
            wait = WebDriverWait(self.driver, 10)
            
            # Helper to find element using multiple strategies
            def find_element_by_selector(uiselector: str = "", xpath: str = "", resource_id: str = "", by_type: str = "clickable"):
                """Find element using UiSelector first, then fallback to XPath or resource_id."""
                try:
                    if uiselector:
                        if by_type == "clickable":
                            return wait.until(EC.element_to_be_clickable((By.ANDROID_UIAUTOMATOR, uiselector)))
                        else:
                            return wait.until(EC.presence_of_element_located((By.ANDROID_UIAUTOMATOR, uiselector)))
                except:
                    pass
                
                if xpath:
                    try:
                        if by_type == "clickable":
                            return wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                        else:
                            return wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    except:
                        pass
                
                if resource_id:
                    try:
                        if by_type == "clickable":
                            return wait.until(EC.element_to_be_clickable((By.ID, resource_id)))
                        else:
                            return wait.until(EC.presence_of_element_located((By.ID, resource_id)))
                    except:
                        pass
                
                raise Exception(f"Element not found with UiSelector, XPath, or resource_id")
            
            # Step 1: Check if address is already correct in collapsed view
            if settings.customer_address:
                try:
                    collapsed_address_id = selectors.get("home_page_collapsed_address_text", {}).get("resource_id", "")
                    collapsed_address_xpath = selectors.get("home_page_collapsed_address_text", {}).get("xpath", "")
                    collapsed_address_uiselector = selectors.get("home_page_collapsed_address_text", {}).get("uiselector", "")
                    
                    collapsed_address_element = find_element_by_selector(
                        uiselector=collapsed_address_uiselector,
                        xpath=collapsed_address_xpath,
                        resource_id=collapsed_address_id,
                        by_type="presence"
                    )
                    
                    displayed_address = collapsed_address_element.text.strip() if collapsed_address_element.text else ""
                    if displayed_address and settings.customer_address.lower() in displayed_address.lower():
                        # Address already matches, no need to change
                        return {"success": True, "message": f"Address already set to {displayed_address}"}
                except:
                    # If we can't check collapsed view, continue with the flow
                    pass
            
            # Step 2: Open address accordion (click collapsed view)
            try:
                accordion_id = selectors.get("home_page_address_accordion", {}).get("resource_id", "")
                accordion_xpath = selectors.get("home_page_address_accordion", {}).get("xpath", "")
                accordion_uiselector = selectors.get("home_page_address_accordion", {}).get("uiselector", "")
                
                accordion = find_element_by_selector(
                    uiselector=accordion_uiselector,
                    xpath=accordion_xpath,
                    resource_id=accordion_id
                )
                accordion.click()
                time.sleep(2)  # Wait for accordion to expand
            except Exception as e:
                return {"success": False, "message": f"Step 2 failed - Could not open address accordion: {str(e)}"}
            
            # Step 3: Click on delivery option (only if not already selected)
            try:
                delivery_option_config = selectors.get("home_page_delivery_option", {})
                delivery_option_id = delivery_option_config.get("resource_id", "")
                delivery_option_xpath = delivery_option_config.get("xpath", "")
                delivery_option_uiselector = delivery_option_config.get("uiselector", "")
                
                if not delivery_option_id and not delivery_option_xpath and not delivery_option_uiselector:
                    return {"success": False, "message": "Delivery option selector not configured"}
                
                delivery_option = find_element_by_selector(
                    uiselector=delivery_option_uiselector,
                    xpath=delivery_option_xpath,
                    resource_id=delivery_option_id
                )
                
                # Check if delivery is already selected by looking for "Clear" in the icon's content-desc
                # The icon is inside the delivery option RelativeLayout
                try:
                    delivery_icon = delivery_option.find_element(By.ID, "com.walmart.android:id/global_intent_center_item_icon")
                    icon_content_desc = delivery_icon.get_attribute("content-desc") or ""
                    if "clear" in icon_content_desc.lower():
                        # Delivery is already selected, don't click it
                        print("Delivery option already selected, skipping click")
                    else:
                        # Delivery is not selected, click it
                        delivery_option.click()
                        time.sleep(2)  # Wait for delivery option to be selected
                except:
                    # If we can't find the icon, try clicking anyway (fallback)
                    delivery_option.click()
                    time.sleep(2)  # Wait for delivery option to be selected
            except Exception as e:
                return {"success": False, "message": f"Step 3 failed - Could not click delivery option: {str(e)}"}
            
            # Step 4: Check if address TextView in expanded view matches stored address
            # Only proceed to change address if it doesn't match
            if settings.customer_address:
                try:
                    expanded_address_id = selectors.get("home_page_expanded_address_text", {}).get("resource_id", "")
                    expanded_address_xpath = selectors.get("home_page_expanded_address_text", {}).get("xpath", "")
                    expanded_address_uiselector = selectors.get("home_page_expanded_address_text", {}).get("uiselector", "")
                    
                    if expanded_address_id or expanded_address_xpath or expanded_address_uiselector:
                        # Wait a bit for the expanded view to fully load after clicking delivery
                        time.sleep(1)
                        
                        expanded_address_element = find_element_by_selector(
                            uiselector=expanded_address_uiselector,
                            xpath=expanded_address_xpath,
                            resource_id=expanded_address_id,
                            by_type="presence"
                        )
                        
                        displayed_address = expanded_address_element.text.strip() if expanded_address_element.text else ""
                        target_address_lower = settings.customer_address.strip().lower()
                        
                        print(f"Checking address match - Displayed: '{displayed_address}', Target: '{target_address_lower}'")
                        
                        if displayed_address and target_address_lower in displayed_address.lower():
                            # Address matches, no need to change
                            print(f"Address already matches: {displayed_address}")
                            return {"success": True, "message": f"Address already matches stored address: {displayed_address}"}
                        
                        # Address doesn't match, click on the address TextView to change it
                        print(f"Address doesn't match, proceeding to change address")
                        # The TextView itself is clickable and navigates to address selection
                        # We already have the element, so just click it directly - no need to lookup the card container
                        expanded_address_element.click()
                        time.sleep(2)  # Wait for address selection screen to open
                    else:
                        # Selector not configured, skip address check
                        print("Address selector not configured, skipping address check")
                except Exception as e:
                    return {"success": False, "message": f"Step 4 failed - Could not check or click address card: {str(e)}"}
            else:
                # No customer_address configured, skip address checking
                return {"success": True, "message": "Delivery option set, but no address configured for matching"}
            
            # Step 5: Select address using home page address selection flow
            # When clicking address card from home page, it goes directly to address selection screen
            try:
                # Find and select address matching customer name using home_page selectors
                address_recycler_id = selectors.get("home_page_address_recycler_view", {}).get("resource_id", "")
                address_recycler_xpath = selectors.get("home_page_address_recycler_view", {}).get("xpath", "")
                address_recycler_uiselector = selectors.get("home_page_address_recycler_view", {}).get("uiselector", "")
                
                if not address_recycler_id and not address_recycler_xpath and not address_recycler_uiselector:
                    return {"success": False, "message": "Home page address RecyclerView selector not configured"}
                
                address_recycler = find_element_by_selector(
                    uiselector=address_recycler_uiselector,
                    xpath=address_recycler_xpath,
                    resource_id=address_recycler_id,
                    by_type="presence"
                )
                
                # Use home_page selector for radio buttons
                address_radio_button_id = selectors.get("home_page_address_name_radio_button", {}).get("resource_id", "")
                
                if not address_radio_button_id:
                    return {"success": False, "message": "Home page address radio button resource ID not configured"}
                
                target_username = settings.customer_name.strip().lower()
                checked_radio_buttons = set()
                max_scroll_attempts = 20
                scroll_attempt = 0
                address_found = False
                
                while scroll_attempt < max_scroll_attempts and not address_found:
                    all_radio_buttons = address_recycler.find_elements(By.ID, address_radio_button_id)
                    
                    if not all_radio_buttons:
                        if scroll_attempt == 0:
                            return {"success": False, "message": "No address radio buttons found in RecyclerView"}
                        break
                    
                    for radio_button in all_radio_buttons:
                        try:
                            try:
                                location = radio_button.location
                                size = radio_button.size
                                button_id = f"{location['x']}_{location['y']}_{location['x'] + size['width']}_{location['y'] + size['height']}"
                                
                                if button_id in checked_radio_buttons:
                                    continue
                                
                                checked_radio_buttons.add(button_id)
                            except:
                                radio_text = radio_button.text.strip() if radio_button.text else ""
                                if radio_text in checked_radio_buttons:
                                    continue
                                checked_radio_buttons.add(radio_text)
                            
                            radio_text = radio_button.text.strip() if radio_button.text else ""
                            
                            if radio_text:
                                radio_text_lower = radio_text.lower()
                                if target_username == radio_text_lower:
                                    radio_button.click()
                                    address_found = True
                                    time.sleep(1)
                                    break
                        except Exception as e:
                            continue
                    
                    if not address_found:
                        try:
                            recycler_location = address_recycler.location
                            recycler_size = address_recycler.size
                            screen_size = self.driver.get_window_size()
                            
                            start_x = recycler_location['x'] + int(recycler_size['width'] / 2)
                            start_y = recycler_location['y'] + int(recycler_size['height'] * 0.7)
                            end_x = start_x
                            end_y = recycler_location['y'] + int(recycler_size['height'] * 0.3)
                            
                            self.driver.swipe(start_x, start_y, end_x, end_y, 500)
                            time.sleep(0.8)
                            scroll_attempt += 1
                        except Exception as e:
                            break
                
                if not address_found:
                    return {"success": False, "message": f"Could not find address with username matching '{settings.customer_name}' after scrolling through {scroll_attempt} times"}
                
                # Click save button using home_page selector
                save_address_button_id = selectors.get("home_page_save_address_button", {}).get("resource_id", "")
                save_address_button_xpath = selectors.get("home_page_save_address_button", {}).get("xpath", "")
                save_address_button_uiselector = selectors.get("home_page_save_address_button", {}).get("uiselector", "")
                
                save_address_button = find_element_by_selector(
                    uiselector=save_address_button_uiselector,
                    xpath=save_address_button_xpath,
                    resource_id=save_address_button_id
                )
                save_address_button.click()
                time.sleep(2)  # Wait for address to be saved
                
            except Exception as e:
                return {"success": False, "message": f"Failed to select address: {str(e)}"}
            
            return {"success": True, "message": f"Successfully set address for {settings.customer_name}"}
        
        except Exception as e:
            return {"success": False, "message": f"Failed to set address and delivery: {str(e)}"}
    
    async def place_order(self, date_preference: Optional[str] = None, time_preference: Optional[str] = None) -> dict:
        """
        Place an order in Walmart app.
        
        Steps:
        1. Click cart_button
        2. Click on third card inside delivery_options LinearLayout
        3. Click cart_view_address_and_delivery_time_button
        3.1 Set correct address:
            3.1.1 Click cart_view_change_address_button (opens address menu)
            3.1.2 In address_recycler_view, for each viewgroup, check if name in 
                  address_name_radio_button matches stored name. If match, click the radio button
        
        Returns:
            Result dictionary
        """
        try:
            if not SELENIUM_AVAILABLE:
                return {"success": False, "message": "Selenium not installed. Please install: pip install selenium"}
            
            if not APPIUM_AVAILABLE:
                return {"success": False, "message": "Appium not installed. Please install: pip install Appium-Python-Client"}
            
            # Auto-connect if not connected
            if not self.connected:
                await self.connect_device()
            
            if not self.driver:
                return {"success": False, "message": "Device not connected. Please connect device first via /api/v1/automation/connect"}
            
            # Check if customer name is configured
            if not settings.customer_name:
                return {"success": False, "message": "Customer name not configured. Please set CUSTOMER_NAME in environment variables."}
            
            # Make sure Walmart app is open
            await self.open_walmart_app()
            time.sleep(2)
            
            wait = WebDriverWait(self.driver, 10)
            
            # Helper to find element using multiple strategies
            def find_element_by_selector(uiselector: str = "", xpath: str = "", resource_id: str = "", by_type: str = "clickable"):
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
            
            # Step 1: Click cart_button
            try:
                cart_button_id = selectors.get("cart_button", {}).get("resource_id", "")
                cart_button_xpath = selectors.get("cart_button", {}).get("xpath", "")
                cart_button_uiselector = selectors.get("cart_button", {}).get("uiselector", "")
                
                cart_button = find_element_by_selector(
                    uiselector=cart_button_uiselector,
                    xpath=cart_button_xpath,
                    resource_id=cart_button_id
                )
                cart_button.click()
                time.sleep(2)  # Wait for cart page to load
            except Exception as e:
                return {"success": False, "message": f"Step 1 failed - Could not click cart button: {str(e)}"}
            
            # Step 2: Click on third card inside delivery_options LinearLayout
            # First, check if accordion is collapsed and expand it if needed
            try:
                # Check if expand/collapse button exists and if accordion is collapsed
                expand_collapse_button_id = selectors.get("delivery_options_expand_collapse_button", {}).get("resource_id", "")
                expand_collapse_button_xpath = selectors.get("delivery_options_expand_collapse_button", {}).get("xpath", "")
                expand_collapse_button_uiselector = selectors.get("delivery_options_expand_collapse_button", {}).get("uiselector", "")
                
                # Try to find the expand/collapse button
                try:
                    expand_collapse_button = find_element_by_selector(
                        uiselector=expand_collapse_button_uiselector,
                        xpath=expand_collapse_button_xpath,
                        resource_id=expand_collapse_button_id,
                        by_type="presence"
                    )
                    
                    # Check if accordion is collapsed by checking content-desc or text
                    # If content-desc contains "Collapsed" (not "Expanded"), click to expand
                    try:
                        content_desc = expand_collapse_button.get_attribute("content-desc") or ""
                        # Check if it's collapsed (content-desc might say "Collapsed" or not contain "Expanded")
                        if "collapsed" in content_desc.lower() or ("expanded" not in content_desc.lower() and content_desc):
                            # Accordion is collapsed, click to expand it
                            expand_collapse_button.click()
                            time.sleep(1.5)  # Wait for accordion to expand
                    except:
                        # If we can't check content-desc, try clicking anyway (idempotent - won't hurt if already expanded)
                        try:
                            expand_collapse_button.click()
                            time.sleep(1.5)
                        except:
                            pass  # Button might not be clickable if already expanded
                except:
                    # Expand/collapse button not found, assume accordion is already expanded or doesn't exist
                    pass
                
                # Now try to click the third card
                delivery_options_third_card_xpath = selectors.get("delivery_options_third_card", {}).get("xpath", "")
                delivery_options_third_card_xpath_alt = selectors.get("delivery_options_third_card", {}).get("xpath_alt", "")
                delivery_options_third_card_uiselector = selectors.get("delivery_options_third_card", {}).get("uiselector", "")
                
                # Try primary XPath first
                third_card = None
                try:
                    third_card = find_element_by_selector(
                        uiselector=delivery_options_third_card_uiselector,
                        xpath=delivery_options_third_card_xpath
                    )
                except:
                    # If primary fails, try alternative XPath (using "Delivery" text)
                    if delivery_options_third_card_xpath_alt:
                        try:
                            third_card = find_element_by_selector(
                                xpath=delivery_options_third_card_xpath_alt
                            )
                        except:
                            pass
                
                if not third_card:
                    return {"success": False, "message": "Step 2 failed - Could not find third card (Delivery) in delivery_options"}
                
                third_card.click()
                time.sleep(2)  # Wait for delivery options to load
            except Exception as e:
                return {"success": False, "message": f"Step 2 failed - Could not click third card in delivery_options: {str(e)}"}
            
            # Step 3: Click cart_view_address_and_delivery_time_button
            try:
                address_delivery_button_id = selectors.get("cart_view_address_and_delivery_time_button", {}).get("resource_id", "")
                address_delivery_button_xpath = selectors.get("cart_view_address_and_delivery_time_button", {}).get("xpath", "")
                address_delivery_button_uiselector = selectors.get("cart_view_address_and_delivery_time_button", {}).get("uiselector", "")
                
                address_delivery_button = find_element_by_selector(
                    uiselector=address_delivery_button_uiselector,
                    xpath=address_delivery_button_xpath,
                    resource_id=address_delivery_button_id
                )
                address_delivery_button.click()
                time.sleep(2)  # Wait for address selection page to load
            except Exception as e:
                return {"success": False, "message": f"Step 3 failed - Could not click address and delivery time button: {str(e)}"}
            
            # Step 3.1: Set correct address
            # Step 3.1.1: Click cart_view_change_address_button
            try:
                change_address_button_id = selectors.get("cart_view_change_address_button", {}).get("resource_id", "")
                change_address_button_xpath = selectors.get("cart_view_change_address_button", {}).get("xpath", "")
                change_address_button_uiselector = selectors.get("cart_view_change_address_button", {}).get("uiselector", "")
                
                change_address_button = find_element_by_selector(
                    uiselector=change_address_button_uiselector,
                    xpath=change_address_button_xpath,
                    resource_id=change_address_button_id
                )
                change_address_button.click()
                time.sleep(2)  # Wait for address menu to open
            except Exception as e:
                return {"success": False, "message": f"Step 3.1.1 failed - Could not click change address button: {str(e)}"}
            
            # Step 3.1.2: In address_recycler_view, find all address_name_radio_button elements,
            #             check if the radio button's text matches stored username. If match, click it.
            # Note: The radio button's text attribute contains the exact username
            try:
                address_recycler_id = selectors.get("address_recycler_view", {}).get("resource_id", "")
                address_recycler_xpath = selectors.get("address_recycler_view", {}).get("xpath", "")
                address_recycler_uiselector = selectors.get("address_recycler_view", {}).get("uiselector", "")
                
                # Find the RecyclerView
                address_recycler = find_element_by_selector(
                    uiselector=address_recycler_uiselector,
                    xpath=address_recycler_xpath,
                    resource_id=address_recycler_id,
                    by_type="presence"
                )
                
                # Get the radio button resource ID
                address_radio_button_id = selectors.get("address_name_radio_button", {}).get("resource_id", "")
                
                if not address_radio_button_id:
                    return {"success": False, "message": "Address radio button resource ID not configured"}
                
                # Normalize customer name for comparison (case-insensitive, trimmed)
                target_username = settings.customer_name.strip().lower()
                
                # Track checked radio buttons to avoid checking the same ones multiple times
                checked_radio_buttons = set()
                max_scroll_attempts = 20  # Maximum number of scroll attempts
                scroll_attempt = 0
                address_found = False
                
                while scroll_attempt < max_scroll_attempts and not address_found:
                    # Find all radio buttons currently visible in the RecyclerView
                    all_radio_buttons = address_recycler.find_elements(By.ID, address_radio_button_id)
                    
                    if not all_radio_buttons:
                        # If no radio buttons found, try scrolling once more
                        if scroll_attempt == 0:
                            return {"success": False, "message": "No address radio buttons found in RecyclerView"}
                        break
                    
                    # Check each radio button's text for matching username
                    for radio_button in all_radio_buttons:
                        try:
                            # Get a unique identifier for this radio button to track if we've checked it
                            # Use location and text as identifier
                            try:
                                location = radio_button.location
                                size = radio_button.size
                                button_id = f"{location['x']}_{location['y']}_{location['x'] + size['width']}_{location['y'] + size['height']}"
                                
                                # Skip if we've already checked this button
                                if button_id in checked_radio_buttons:
                                    continue
                                
                                checked_radio_buttons.add(button_id)
                            except:
                                # If we can't get location, use text as fallback identifier
                                radio_text = radio_button.text.strip() if radio_button.text else ""
                                if radio_text in checked_radio_buttons:
                                    continue
                                checked_radio_buttons.add(radio_text)
                            
                            # Get the radio button's text (this contains the username)
                            radio_text = radio_button.text.strip() if radio_button.text else ""
                            
                            if radio_text:
                                radio_text_lower = radio_text.lower()
                                # Check if the radio button text matches the target username
                                if target_username == radio_text_lower:
                                    # Found matching username, click the radio button
                                    radio_button.click()
                                    address_found = True
                                    time.sleep(1)
                                    break
                        except Exception as e:
                            # Continue to next radio button if this one fails
                            continue
                    
                    # If address not found yet, scroll down to load more addresses
                    if not address_found:
                        try:
                            # Get RecyclerView location and size
                            recycler_location = address_recycler.location
                            recycler_size = address_recycler.size
                            screen_size = self.driver.get_window_size()
                            
                            # Calculate scroll coordinates (scroll down in RecyclerView)
                            start_x = recycler_location['x'] + int(recycler_size['width'] / 2)
                            start_y = recycler_location['y'] + int(recycler_size['height'] * 0.7)  # Start from 70% down
                            end_x = start_x
                            end_y = recycler_location['y'] + int(recycler_size['height'] * 0.3)  # End at 30% down (scroll up content)
                            
                            # Perform swipe to scroll
                            self.driver.swipe(start_x, start_y, end_x, end_y, 500)
                            time.sleep(0.8)  # Wait for new items to load
                            
                            scroll_attempt += 1
                        except Exception as e:
                            # If scrolling fails, break the loop
                            break
                
                if not address_found:
                    return {"success": False, "message": f"Could not find address with username matching '{settings.customer_name}' after scrolling through {scroll_attempt} times"}
                
                # Step 3.1.3: Click save_address_button to save the selected address
                try:
                    save_address_button_id = selectors.get("save_address_button", {}).get("resource_id", "")
                    save_address_button_xpath = selectors.get("save_address_button", {}).get("xpath", "")
                    save_address_button_uiselector = selectors.get("save_address_button", {}).get("uiselector", "")
                    
                    save_address_button = find_element_by_selector(
                        uiselector=save_address_button_uiselector,
                        xpath=save_address_button_xpath,
                        resource_id=save_address_button_id
                    )
                    save_address_button.click()
                    time.sleep(2)  # Wait for address to be saved and page to update
                except Exception as e:
                    return {"success": False, "message": f"Step 3.1.3 failed - Could not click save address button: {str(e)}"}
                
            except Exception as e:
                return {"success": False, "message": f"Step 3.1.2 failed - Could not select address: {str(e)}"}
            
            # Step 4: Select date and time for delivery
            # Step 4.1: Select date
            date_selected = await self._select_delivery_date(date_preference=date_preference)
            if not date_selected.get("success"):
                return {"success": False, "message": f"Step 4.1 failed - {date_selected.get('message', 'Could not select date')}"}
            
            # Step 4.2: Select time slot
            time_selected = await self._select_delivery_time(time_preference=time_preference)
            if not time_selected.get("success"):
                return {"success": False, "message": f"Step 4.2 failed - {time_selected.get('message', 'Could not select time')}"}
            
            # Step 4.3: Click reserve/confirm button
            reserve_result = await self._confirm_reservation()
            if not reserve_result.get("success"):
                return {"success": False, "message": f"Step 4.3 failed - {reserve_result.get('message', 'Could not confirm reservation')}"}
            
            return {
                "success": True,
                "message": f"Successfully placed order with address for {settings.customer_name}",
                "date": date_selected.get("date"),
                "time": time_selected.get("time")
            }
        
        except Exception as e:
            return {"success": False, "message": f"Failed to place order: {str(e)}"}
    
    async def _select_delivery_date(self, date_preference: Optional[str] = None) -> dict:
        """
        Select delivery date from the date selector.
        
        Args:
            date_preference: Optional date preference (e.g., "today", "tomorrow", "Tue 12/9", etc.)
                           If None, selects the first available date
        
        Returns:
            Result dictionary with selected date
        """
        try:
            if not SELENIUM_AVAILABLE or not APPIUM_AVAILABLE or not self.driver:
                return {"success": False, "message": "Device not connected or dependencies not available"}
            
            wait = WebDriverWait(self.driver, 10)
            
            # Helper to find element using multiple strategies
            def find_element_by_selector(uiselector: str = "", xpath: str = "", resource_id: str = "", by_type: str = "clickable"):
                """Find element using UiSelector first, then fallback to XPath or resource_id."""
                try:
                    if uiselector:
                        if by_type == "clickable":
                            return wait.until(EC.element_to_be_clickable((By.ANDROID_UIAUTOMATOR, uiselector)))
                        else:
                            return wait.until(EC.presence_of_element_located((By.ANDROID_UIAUTOMATOR, uiselector)))
                except:
                    pass
                
                if xpath:
                    try:
                        if by_type == "clickable":
                            return wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                        else:
                            return wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    except:
                        pass
                
                if resource_id:
                    try:
                        if by_type == "clickable":
                            return wait.until(EC.element_to_be_clickable((By.ID, resource_id)))
                        else:
                            return wait.until(EC.presence_of_element_located((By.ID, resource_id)))
                    except:
                        pass
                
                raise Exception(f"Element not found with UiSelector, XPath, or resource_id")
            
            # Get date selector configuration (to be added by user)
            date_selector_config = selectors.get("delivery_date_selector", {})
            date_selector_id = date_selector_config.get("resource_id", "")
            date_selector_xpath = date_selector_config.get("xpath", "")
            date_selector_uiselector = date_selector_config.get("uiselector", "")
            
            if not date_selector_id and not date_selector_xpath and not date_selector_uiselector:
                return {"success": False, "message": "Date selector not configured"}
            
            # Find all available date options
            # This will need to be updated based on actual selector structure
            # For now, placeholder logic
            if date_preference:
                # Try to find date matching preference
                # This is a placeholder - actual implementation depends on selector structure
                pass
            else:
                # Select first available date (not "Full")
                # This is a placeholder - actual implementation depends on selector structure
                pass
            
            # Placeholder return - to be implemented once selectors are added
            return {"success": True, "message": "Date selection placeholder", "date": date_preference or "default"}
        
        except Exception as e:
            return {"success": False, "message": f"Failed to select date: {str(e)}"}
    
    async def _select_delivery_time(self, time_preference: Optional[str] = None) -> dict:
        """
        Select delivery time slot from the time selector.
        
        Args:
            time_preference: Optional time preference (e.g., "6am-8am", "7am-9am", "morning", "afternoon", etc.)
                           If None, selects the first available time slot
        
        Returns:
            Result dictionary with selected time
        """
        try:
            if not SELENIUM_AVAILABLE or not APPIUM_AVAILABLE or not self.driver:
                return {"success": False, "message": "Device not connected or dependencies not available"}
            
            wait = WebDriverWait(self.driver, 10)
            
            # Helper to find element using multiple strategies
            def find_element_by_selector(uiselector: str = "", xpath: str = "", resource_id: str = "", by_type: str = "clickable"):
                """Find element using UiSelector first, then fallback to XPath or resource_id."""
                try:
                    if uiselector:
                        if by_type == "clickable":
                            return wait.until(EC.element_to_be_clickable((By.ANDROID_UIAUTOMATOR, uiselector)))
                        else:
                            return wait.until(EC.presence_of_element_located((By.ANDROID_UIAUTOMATOR, uiselector)))
                except:
                    pass
                
                if xpath:
                    try:
                        if by_type == "clickable":
                            return wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                        else:
                            return wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    except:
                        pass
                
                if resource_id:
                    try:
                        if by_type == "clickable":
                            return wait.until(EC.element_to_be_clickable((By.ID, resource_id)))
                        else:
                            return wait.until(EC.presence_of_element_located((By.ID, resource_id)))
                    except:
                        pass
                
                raise Exception(f"Element not found with UiSelector, XPath, or resource_id")
            
            # Get time selector configuration (to be added by user)
            time_selector_config = selectors.get("delivery_time_selector", {})
            time_selector_id = time_selector_config.get("resource_id", "")
            time_selector_xpath = time_selector_config.get("xpath", "")
            time_selector_uiselector = time_selector_config.get("uiselector", "")
            
            if not time_selector_id and not time_selector_xpath and not time_selector_uiselector:
                return {"success": False, "message": "Time selector not configured"}
            
            # Find all available time slots
            # This will need to be updated based on actual selector structure
            # For now, placeholder logic
            if time_preference:
                # Try to find time slot matching preference
                # This is a placeholder - actual implementation depends on selector structure
                pass
            else:
                # Select first available time slot
                # This is a placeholder - actual implementation depends on selector structure
                pass
            
            # Placeholder return - to be implemented once selectors are added
            return {"success": True, "message": "Time selection placeholder", "time": time_preference or "default"}
        
        except Exception as e:
            return {"success": False, "message": f"Failed to select time: {str(e)}"}
    
    async def _confirm_reservation(self) -> dict:
        """
        Click the reserve/confirm button to finalize the date and time selection.
        
        Returns:
            Result dictionary
        """
        try:
            if not SELENIUM_AVAILABLE or not APPIUM_AVAILABLE or not self.driver:
                return {"success": False, "message": "Device not connected or dependencies not available"}
            
            wait = WebDriverWait(self.driver, 10)
            
            # Helper to find element using multiple strategies
            def find_element_by_selector(uiselector: str = "", xpath: str = "", resource_id: str = "", by_type: str = "clickable"):
                """Find element using UiSelector first, then fallback to XPath or resource_id."""
                try:
                    if uiselector:
                        if by_type == "clickable":
                            return wait.until(EC.element_to_be_clickable((By.ANDROID_UIAUTOMATOR, uiselector)))
                        else:
                            return wait.until(EC.presence_of_element_located((By.ANDROID_UIAUTOMATOR, uiselector)))
                except:
                    pass
                
                if xpath:
                    try:
                        if by_type == "clickable":
                            return wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                        else:
                            return wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    except:
                        pass
                
                if resource_id:
                    try:
                        if by_type == "clickable":
                            return wait.until(EC.element_to_be_clickable((By.ID, resource_id)))
                        else:
                            return wait.until(EC.presence_of_element_located((By.ID, resource_id)))
                    except:
                        pass
                
                raise Exception(f"Element not found with UiSelector, XPath, or resource_id")
            
            # Get reserve button configuration (to be added by user)
            reserve_button_config = selectors.get("reserve_time_button", {})
            reserve_button_id = reserve_button_config.get("resource_id", "")
            reserve_button_xpath = reserve_button_config.get("xpath", "")
            reserve_button_uiselector = reserve_button_config.get("uiselector", "")
            
            if not reserve_button_id and not reserve_button_xpath and not reserve_button_uiselector:
                return {"success": False, "message": "Reserve button not configured"}
            
            # Find and click reserve button
            reserve_button = find_element_by_selector(
                uiselector=reserve_button_uiselector,
                xpath=reserve_button_xpath,
                resource_id=reserve_button_id
            )
            reserve_button.click()
            time.sleep(2)  # Wait for reservation to be confirmed
            
            return {"success": True, "message": "Reservation confirmed"}
        
        except Exception as e:
            return {"success": False, "message": f"Failed to confirm reservation: {str(e)}"}
    
    def disconnect(self):
        """Disconnect from device."""
        if self.driver:
            self.driver.quit()
            self.driver = None
        self.connected = False

