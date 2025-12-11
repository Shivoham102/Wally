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
            
            # # Set address and delivery option early (product listings change based on address)
            # address_result = await self.set_address_and_delivery()
            # if not address_result.get("success"):
            #     # Log warning but don't fail - app is still open
            #     return {
            #         "success": True,
            #         "message": "Walmart app opened",
            #         "address_set": False,
            #         "address_warning": address_result.get("message", "Could not set address")
            #     }
            
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
                            
                            # Step 3c: Scroll and check for customer name at each scroll iteration
                            customer_name_id = selectors.get("order_details_customer_name", {}).get("resource_id", "")
                            customer_name_xpath = selectors.get("order_details_customer_name", {}).get("xpath", "")
                            
                            customer_name_element = None
                            customer_name_found = False
                            should_proceed_to_reorder = False
                            name_mismatch = False
                            max_scroll_attempts = 8  # Reduced to prevent excessive scrolling
                            scroll_attempt = 0
                            
                            while scroll_attempt < max_scroll_attempts:
                                # Check if customer name exists on screen
                                customer_name_element = None
                                if customer_name_id:
                                    try:
                                        customer_name_element = self.driver.find_element(By.ID, customer_name_id)
                                        # Check if element is actually visible on screen
                                        if customer_name_element.is_displayed():
                                            customer_name_found = True
                                    except:
                                        pass
                                
                                if not customer_name_element and customer_name_xpath:
                                    try:
                                        customer_name_element = self.driver.find_element(By.XPATH, customer_name_xpath)
                                        # Check if element is actually visible on screen
                                        if customer_name_element.is_displayed():
                                            customer_name_found = True
                                    except:
                                        pass
                                
                                # If customer name found, check if it matches
                                if customer_name_found and customer_name_element:
                                    try:
                                        order_customer_name = customer_name_element.text.strip()
                                        
                                        # If name doesn't match, exit immediately
                                        if order_customer_name.lower() != settings.customer_name.lower():
                                            # Name doesn't match, set flag and break out of scroll loop
                                            # We'll handle going back and scrolling after breaking out
                                            name_mismatch = True
                                            break  # Break out of scroll loop
                                        else:
                                            # Name matches! Set flag and break out of scroll loop to proceed to reorder button
                                            should_proceed_to_reorder = True
                                            break
                                    except:
                                        # Error reading customer name, continue scrolling
                                        customer_name_found = False
                                        customer_name_element = None
                                
                                # If customer name not found yet, continue scrolling
                                if not customer_name_found:
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
                                else:
                                    # Customer name found and matched, break out of scroll loop
                                    break
                            
                            # If name doesn't match or customer name element still doesn't exist after all scrolls, go back and try next
                            if name_mismatch or not customer_name_found or not customer_name_element:
                                # Go back to purchase history page
                                try:
                                    self.driver.back()
                                    time.sleep(2)  # Wait for page to load
                                    
                                    # Verify we're back on purchase history by checking for order cards
                                    # This helps prevent crashes if we went back too far
                                    try:
                                        verify_cards = self.driver.find_elements(By.ID, order_card_id) if order_card_id else []
                                        if not verify_cards and order_card_xpath:
                                            verify_cards = self.driver.find_elements(By.XPATH, order_card_xpath)
                                        if not verify_cards:
                                            # We're not on purchase history page, might have gone back too far
                                            # Break and let outer loop handle - it will refetch and detect the issue
                                            break
                                    except:
                                        pass  # If verification fails, continue anyway
                                except Exception as e:
                                    # If back fails, we might already be on purchase history or app crashed
                                    pass
                                
                                # Mark this card as checked so we don't process it again
                                try:
                                    checked_card_positions.add(card_position)
                                except:
                                    try:
                                        checked_card_positions.add(card_index)
                                    except:
                                        pass
                                
                                attempt += 1
                                card_found = True
                                break  # Break out of for loop to let outer while loop refetch cards
                            
                            # Step 3d: Customer name found and matched, proceed to reorder button
                            # Only proceed if we found a matching customer name
                            if should_proceed_to_reorder and customer_name_found and customer_name_element:
                                # Get customer name text (already retrieved above, but ensure we have it)
                                try:
                                    order_customer_name = customer_name_element.text.strip()
                                except:
                                    # Fallback: try to get it again
                                    order_customer_name = customer_name_element.text.strip() if customer_name_element else ""
                                
                                # Step 3e: Name matches (already verified in scroll loop), scroll to and click reorder button
                                if order_customer_name.lower() == settings.customer_name.lower():
                                    # Name matches! Now scroll to reorder button and click it
                                    reorder_button_id = selectors.get("reorder_all_items_button", {}).get("resource_id", "")
                                    reorder_button_xpath = selectors.get("reorder_all_items_button", {}).get("xpath", "")
                                    
                                    reorder_button = None
                                    # Try to find reorder button, scrolling if necessary
                                    max_reorder_scroll_attempts = 5
                                    reorder_scroll_attempt = 0
                                    
                                    while reorder_scroll_attempt < max_reorder_scroll_attempts:
                                        if reorder_button_id:
                                            try:
                                                reorder_button = self.driver.find_element(By.ID, reorder_button_id)
                                                if reorder_button.is_displayed():
                                                    # Check if button is visible on screen
                                                    button_location = reorder_button.location
                                                    screen_size = self.driver.get_window_size()
                                                    if button_location['y'] < screen_size['height']:
                                                        break
                                            except:
                                                pass
                                        
                                        if not reorder_button and reorder_button_xpath:
                                            try:
                                                reorder_button = self.driver.find_element(By.XPATH, reorder_button_xpath)
                                                if reorder_button.is_displayed():
                                                    # Check if button is visible on screen
                                                    button_location = reorder_button.location
                                                    screen_size = self.driver.get_window_size()
                                                    if button_location['y'] < screen_size['height']:
                                                        break
                                            except:
                                                pass
                                        
                                        # Button not visible, scroll down to bring it into view
                                        screen_size = self.driver.get_window_size()
                                        self.driver.swipe(
                                            int(screen_size['width'] / 2),
                                            int(screen_size['height'] * 0.7),
                                            int(screen_size['width'] / 2),
                                            int(screen_size['height'] * 0.3),
                                            500
                                        )
                                        time.sleep(0.5)
                                        reorder_scroll_attempt += 1
                                    
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
                            # Error processing this card, go back if we're on details page, then break to refetch
                            try:
                                # Try to go back - might already be on purchase history page
                                self.driver.back()
                                time.sleep(2)  # Wait for page to load
                            except:
                                # If back fails, we might already be on purchase history page
                                pass
                            
                            # Mark this card as checked so we don't process it again
                            try:
                                checked_card_positions.add(card_position)
                            except:
                                try:
                                    checked_card_positions.add(card_index)
                                except:
                                    pass
                            
                            attempt += 1
                            card_found = True
                            break  # Break out of for loop to let outer while loop refetch cards
                    
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
        
        Note: Delivery option and address selection are handled at app startup, so this flow
        assumes they are already configured.
        
        Steps:
        1. Click cart_button
        2. Click cart_view_address_and_delivery_time_button (to get to date/time selection)
        3. Select delivery date (if date_preference provided)
        4. Select delivery time slot (if time_preference provided)
        5. Confirm reservation
        
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
            
            # Step 2: Click cart_view_address_and_delivery_time_button to get to date/time selection
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
                time.sleep(2)  # Wait for date/time selection page to load
            except Exception as e:
                return {"success": False, "message": f"Step 2 failed - Could not click address and delivery time button: {str(e)}"}
            
            # Step 3: Select date and time for delivery
            # Step 3.1: Select date
            date_selected = await self._select_delivery_date(date_preference=date_preference)
            if not date_selected.get("success"):
                return {"success": False, "message": f"Step 3.1 failed - {date_selected.get('message', 'Could not select date')}"}
            
            # Step 3.2: Select time slot
            time_selected = await self._select_delivery_time(time_preference=time_preference)
            if not time_selected.get("success"):
                return {"success": False, "message": f"Step 3.2 failed - {time_selected.get('message', 'Could not select time')}"}
            
            # Step 3.3: Click reserve/confirm button
            reserve_result = await self._confirm_reservation()
            if not reserve_result.get("success"):
                return {"success": False, "message": f"Step 3.3 failed - {reserve_result.get('message', 'Could not confirm reservation')}"}
            
            return {
                "success": True,
                "message": "Successfully placed order",
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
            
            # Get date RecyclerView configuration
            date_recycler_config = selectors.get("delivery_day_date_recycler_view", {})
            date_recycler_id = date_recycler_config.get("resource_id", "")
            date_recycler_xpath = date_recycler_config.get("xpath", "")
            date_recycler_uiselector = date_recycler_config.get("uiselector", "")
            
            if not date_recycler_id and not date_recycler_xpath and not date_recycler_uiselector:
                return {"success": False, "message": "Date RecyclerView not configured"}
            
            # Find the date RecyclerView
            date_recycler = find_element_by_selector(
                uiselector=date_recycler_uiselector,
                xpath=date_recycler_xpath,
                resource_id=date_recycler_id,
                by_type="presence"
            )
            
            # Helper function to find and filter date ViewGroups
            def find_date_viewgroups():
                date_viewgroups_raw = date_recycler.find_elements(By.XPATH, ".//android.view.ViewGroup[contains(@content-desc, 'Radio Button')]")
                parent_date_viewgroups = []
                for vg in date_viewgroups_raw:
                    try:
                        content_desc = vg.get_attribute("content-desc") or ""
                        is_clickable = vg.get_attribute("clickable") == "true"
                        is_selected = "Selected" in content_desc
                        if "Radio Button" in content_desc and (is_clickable or is_selected):
                            parent_date_viewgroups.append(vg)
                    except Exception:
                        continue
                return parent_date_viewgroups
            
            # Try to find date ViewGroups, scroll if needed
            date_viewgroups = find_date_viewgroups()
            max_scroll_attempts = 5
            scroll_attempts = 0
            
            # Parse date preference if provided
            selected_date_viewgroup = None
            selected_date_text = None
            
            if date_preference:
                # Normalize date preference for matching
                date_pref_lower = date_preference.lower().strip()
                
                # Try to match date preference with scrolling
                while scroll_attempts < max_scroll_attempts and not selected_date_viewgroup:
                    # Try to match date preference
                    if date_pref_lower == "today":
                        # Find "Today" by "Selected" in content-desc
                        for vg in date_viewgroups:
                            try:
                                content_desc = vg.get_attribute("content-desc") or ""
                                if "Today" in content_desc and "Selected" in content_desc:
                                    viewgroup_text_lower = content_desc.lower()
                                    if "full" not in viewgroup_text_lower:
                                        selected_date_viewgroup = vg
                                        selected_date_text = content_desc.split("Radio Button")[0].strip()
                                        break
                            except Exception:
                                continue
                    elif date_pref_lower == "tomorrow":
                        # Tomorrow is always the second item (index 1)
                        if len(date_viewgroups) > 1:
                            try:
                                tomorrow_vg = date_viewgroups[1]
                                content_desc = tomorrow_vg.get_attribute("content-desc") or ""
                                viewgroup_text_lower = content_desc.lower()
                                if "full" not in viewgroup_text_lower:
                                    selected_date_viewgroup = tomorrow_vg
                                    selected_date_text = content_desc.split("Radio Button")[0].strip()
                            except Exception:
                                pass
                    else:
                        # Match by day name (e.g., "Thursday", "Thu") or date format (e.g., "12/11")
                        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                        day_abbrevs = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
                        
                        # Check if preference matches a day name
                        matched_day = None
                        for day_name, day_abbrev in zip(day_names, day_abbrevs):
                            if day_name in date_pref_lower or day_abbrev in date_pref_lower:
                                matched_day = (day_name, day_abbrev)
                                break
                        
                        # Try to match day name or date format
                        for viewgroup in date_viewgroups:
                            try:
                                content_desc = viewgroup.get_attribute("content-desc") or ""
                                content_desc_lower = content_desc.lower()
                                
                                # Skip if it says "Full"
                                if "full" in content_desc_lower:
                                    continue
                                
                                # Match by day name if we found a day match
                                if matched_day:
                                    day_name, day_abbrev = matched_day
                                    if day_name in content_desc_lower or day_abbrev in content_desc_lower:
                                        selected_date_viewgroup = viewgroup
                                        selected_date_text = content_desc.split("Radio Button")[0].strip()
                                        break
                                
                                # Try matching date format (e.g., "12/11", "12-11")
                                if not selected_date_viewgroup and any(char.isdigit() for char in date_pref_lower):
                                    pref_date_parts = re.findall(r'\d+', date_pref_lower)
                                    viewgroup_date_parts = re.findall(r'\d+', content_desc_lower)
                                    
                                    if pref_date_parts and viewgroup_date_parts:
                                        if all(part in viewgroup_date_parts for part in pref_date_parts):
                                            selected_date_viewgroup = viewgroup
                                            selected_date_text = content_desc.split("Radio Button")[0].strip()
                                            break
                            except Exception:
                                continue
                    
                    # If not found, scroll and try again
                    if not selected_date_viewgroup:
                        # Scroll right (swipe left) to see more dates
                        self._scroll_recycler_horizontal(date_recycler, direction="right")
                        scroll_attempts += 1
                        date_viewgroups = find_date_viewgroups()
                
                if not selected_date_viewgroup:
                    return {"success": False, "message": f"Could not find date matching preference '{date_preference}' after scrolling"}
            else:
                # No preference - select first available date (not "Full")
                for viewgroup in date_viewgroups:
                    try:
                        viewgroup_text = viewgroup.text.strip() if viewgroup.text else ""
                        viewgroup_text_lower = viewgroup_text.lower()
                        
                        # Skip if it says "Full"
                        if "full" not in viewgroup_text_lower:
                            selected_date_viewgroup = viewgroup
                            selected_date_text = viewgroup_text
                            break
                    except Exception as e:
                        continue
                
                if not selected_date_viewgroup:
                    return {"success": False, "message": "No available dates found (all dates may be full)"}
            
            # Click the selected date ViewGroup
            if selected_date_viewgroup:
                try:
                    selected_date_viewgroup.click()
                    time.sleep(2)  # Wait for date selection to register and time slots to load
                except Exception as e:
                    return {"success": False, "message": f"Failed to click date ViewGroup: {str(e)}"}
            
            return {"success": True, "message": f"Date selected: {selected_date_text}", "date": selected_date_text}
        
        except Exception as e:
            return {"success": False, "message": f"Failed to select date: {str(e)}"}
    
    def _scroll_recycler_horizontal(self, recycler_element, direction: str = "right", scroll_amount: int = 300) -> None:
        """
        Scroll a RecyclerView horizontally.
        
        Args:
            recycler_element: The RecyclerView WebElement
            direction: "right" to scroll right (swipe left), "left" to scroll left (swipe right)
            scroll_amount: Pixels to scroll (default 300)
        """
        try:
            location = recycler_element.location
            size = recycler_element.size
            
            center_x = location['x'] + size['width'] / 2
            center_y = location['y'] + size['height'] / 2
            
            if direction == "right":
                # Swipe left to scroll right (to see items on the right)
                start_x = int(center_x + scroll_amount / 2)
                end_x = int(center_x - scroll_amount / 2)
            else:  # left
                # Swipe right to scroll left (to see items on the left)
                start_x = int(center_x - scroll_amount / 2)
                end_x = int(center_x + scroll_amount / 2)
            
            self.driver.swipe(start_x, int(center_y), end_x, int(center_y), 300)
            time.sleep(0.5)  # Wait for scroll to complete
        except Exception:
            pass
    
    def _scroll_recycler_vertical(self, recycler_element, direction: str = "down", scroll_amount: int = 400) -> None:
        """
        Scroll a RecyclerView vertically.
        
        Args:
            recycler_element: The RecyclerView WebElement
            direction: "down" to scroll down (swipe up), "up" to scroll up (swipe down)
            scroll_amount: Pixels to scroll (default 400)
        """
        try:
            location = recycler_element.location
            size = recycler_element.size
            
            center_x = location['x'] + size['width'] / 2
            center_y = location['y'] + size['height'] / 2
            
            if direction == "down":
                # Swipe up to scroll down (to see items below)
                start_y = int(center_y + scroll_amount / 2)
                end_y = int(center_y - scroll_amount / 2)
            else:  # up
                # Swipe down to scroll up (to see items above)
                start_y = int(center_y - scroll_amount / 2)
                end_y = int(center_y + scroll_amount / 2)
            
            self.driver.swipe(int(center_x), start_y, int(center_x), end_y, 300)
            time.sleep(0.5)  # Wait for scroll to complete
        except Exception:
            pass
    
    def _parse_time_to_minutes(self, time_str: str) -> Optional[int]:
        """
        Parse a time string (e.g., "8am", "2pm", "6am-8am") to minutes since midnight.
        
        Args:
            time_str: Time string in formats like "8am", "2pm", "6am-8am"
        
        Returns:
            Minutes since midnight, or None if parsing fails
        """
        try:
            time_str = time_str.lower().strip()
            
            # Handle time ranges - extract start time
            if "-" in time_str or " to " in time_str:
                # Extract first time from range (e.g., "6am-8am" -> "6am")
                time_str = re.split(r'[- ]to[ ]', time_str)[0].strip()
            
            # Extract hour and am/pm (Walmart only uses 12-hour format)
            match = re.match(r'(\d+)\s*(am|pm)', time_str)
            if match:
                hour = int(match.group(1))
                period = match.group(2)
                
                # Convert to 24-hour format
                if period == "am":
                    if hour == 12:
                        hour = 0
                    minutes = hour * 60
                else:  # pm
                    if hour != 12:
                        hour += 12
                    minutes = hour * 60
                
                return minutes
            
            return None
        except Exception:
            return None
    
    def _parse_time_range(self, time_range_str: str) -> Optional[tuple]:
        """
        Parse a time range string (e.g., "6am-8am", "6am to 8am") to (start_minutes, end_minutes).
        
        Args:
            time_range_str: Time range string
        
        Returns:
            Tuple of (start_minutes, end_minutes) or None if parsing fails
        """
        try:
            time_range_str = time_range_str.lower().strip()
            
            # Split by "-" or " to "
            parts = re.split(r'[- ]to[ ]', time_range_str)
            if len(parts) != 2:
                return None
            
            start_time = parts[0].strip()
            end_time = parts[1].strip()
            
            start_minutes = self._parse_time_to_minutes(start_time)
            end_minutes = self._parse_time_to_minutes(end_time)
            
            if start_minutes is not None and end_minutes is not None:
                return (start_minutes, end_minutes)
            
            return None
        except Exception:
            return None
    
    def _time_falls_in_range(self, specific_time: str, time_range_str: str) -> bool:
        """
        Check if a specific time falls within a time range.
        
        Args:
            specific_time: Specific time (e.g., "8am", "2pm")
            time_range_str: Time range string (e.g., "6am-8am", "1pm-3pm")
        
        Returns:
            True if specific_time falls within the range, False otherwise
        """
        try:
            specific_minutes = self._parse_time_to_minutes(specific_time)
            if specific_minutes is None:
                return False
            
            range_tuple = self._parse_time_range(time_range_str)
            if range_tuple is None:
                return False
            
            start_minutes, end_minutes = range_tuple
            
            # Check if specific time falls within range
            # For delivery slots, we use inclusive start and inclusive end
            # So "8am" matches both "6am-8am" (end) and "8am-10am" (start)
            # We'll match if it's within the range OR exactly at the start
            return start_minutes <= specific_minutes <= end_minutes
        except Exception:
            return False
    
    async def _select_delivery_time(self, time_preference: Optional[str] = None) -> dict:
        """
        Select delivery time slot from the time selector.
        
        Args:
            time_preference: Optional time preference (e.g., "6am-8am", "7am-9am", "morning", "afternoon", "8am", "2pm", etc.)
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
            
            # Get time RecyclerView configuration
            time_recycler_config = selectors.get("delivery_time_recycler_view", {})
            time_recycler_id = time_recycler_config.get("resource_id", "")
            time_recycler_xpath = time_recycler_config.get("xpath", "")
            time_recycler_uiselector = time_recycler_config.get("uiselector", "")
            
            if not time_recycler_id and not time_recycler_xpath and not time_recycler_uiselector:
                return {"success": False, "message": "Time RecyclerView not configured"}
            
            # Find the time RecyclerView and wait for it to be ready
            time_recycler = find_element_by_selector(
                uiselector=time_recycler_uiselector,
                xpath=time_recycler_xpath,
                resource_id=time_recycler_id,
                by_type="presence"
            )
            
            # Wait a bit for time slots to load after date selection
            time.sleep(1)
            
            # Helper function to find and filter time slot ViewGroups
            def find_time_slots():
                time_slot_item_layout_id = "com.walmart.android:id/bookslot_slot_item_layout"
                time_slot_viewgroups = time_recycler.find_elements(By.ID, time_slot_item_layout_id)
                
                if not time_slot_viewgroups:
                    return []
                
                actual_time_slots = []
                for i, vg in enumerate(time_slot_viewgroups):
                    try:
                        # Check if this ViewGroup contains wplus_signup_card (promotion)
                        wplus_cards = vg.find_elements(By.ID, "com.walmart.android:id/wplus_signup_card")
                        if wplus_cards:
                            continue
                        
                        # Check if this is the store info layout (first one)
                        store_info_layouts = vg.find_elements(By.ID, "com.walmart.android:id/bookslot_delivery_store_info_layout")
                        if store_info_layouts and i == 0:
                            continue
                        
                        # This is an actual time slot - get the time TextView from it
                        time_text_view_id = "com.walmart.android:id/bookslot_slot_time_text_view"
                        time_text_views = vg.find_elements(By.ID, time_text_view_id)
                        if time_text_views:
                            actual_time_slots.append({
                                "viewgroup": vg,
                                "time_text": time_text_views[0].text.strip() if time_text_views[0].text else ""
                            })
                    except Exception:
                        continue
                
                return actual_time_slots
            
            # Try to find time slots, scroll if needed
            actual_time_slots = find_time_slots()
            
            if not actual_time_slots:
                return {"success": False, "message": "No valid time slots found after filtering"}
            
            # Parse time preference if provided
            selected_time_viewgroup = None
            selected_time_text = None
            
            if time_preference:
                # Normalize time preference for matching
                time_pref_lower = time_preference.lower().strip()
                
                # Check if it's a specific time (e.g., "8am", "2pm") vs a range or period
                is_specific_time = bool(re.match(r'^\d+\s*(am|pm)$', time_pref_lower))
                is_time_range = bool(re.search(r'\d+\s*(am|pm)\s*[- ]to[ ]\s*\d+\s*(am|pm)', time_pref_lower) or 
                                     re.search(r'\d+\s*(am|pm)\s*-\s*\d+\s*(am|pm)', time_pref_lower))
                
                # Try to match time preference with scrolling until end is reached
                best_match = None  # Store best match for specific times
                seen_time_texts = set()  # Track seen time slots to detect end of list
                max_scroll_attempts = 50  # Increased limit, but we'll stop when we reach the end
                scroll_attempts = 0
                no_new_items_count = 0  # Count consecutive scrolls with no new items
                
                while scroll_attempts < max_scroll_attempts:
                    # Try to match time preference
                    for slot in actual_time_slots:
                        try:
                            vg = slot["viewgroup"]
                            viewgroup_text = slot["time_text"]
                            viewgroup_text_lower = viewgroup_text.lower()
                            
                            if not viewgroup_text:
                                continue
                            
                            # Skip if it says "Full" or "Unavailable"
                            viewgroup_full_text = vg.text.strip() if vg.text else ""
                            viewgroup_content_desc = vg.get_attribute("content-desc") or ""
                            if "full" in viewgroup_full_text.lower() or "unavailable" in viewgroup_full_text.lower() or "full" in viewgroup_content_desc.lower():
                                continue
                            
                            # Match patterns: "morning", "afternoon", "evening", specific time ranges, or specific times
                            if time_pref_lower == "morning":
                                # Morning is typically 6am-12pm, look for early times
                                if any(time_str in viewgroup_text_lower for time_str in ["6am", "7am", "8am", "9am", "10am", "11am", "12pm"]):
                                    selected_time_viewgroup = vg
                                    selected_time_text = viewgroup_text
                                    break
                            elif time_pref_lower == "afternoon":
                                # Afternoon is typically 12pm-5pm
                                if any(time_str in viewgroup_text_lower for time_str in ["12pm", "1pm", "2pm", "3pm", "4pm", "5pm"]):
                                    selected_time_viewgroup = vg
                                    selected_time_text = viewgroup_text
                                    break
                            elif time_pref_lower == "evening":
                                # Evening is typically 5pm-9pm
                                if any(time_str in viewgroup_text_lower for time_str in ["5pm", "6pm", "7pm", "8pm", "9pm"]):
                                    selected_time_viewgroup = vg
                                    selected_time_text = viewgroup_text
                                    break
                            elif is_specific_time:
                                # Specific time like "8am" - find slot where time is in the middle of the range
                                time_range_match = re.search(r'(\d+)\s*(am|pm)\s*-\s*(\d+)\s*(am|pm)', viewgroup_text_lower)
                                if time_range_match:
                                    start_hour = int(time_range_match.group(1))
                                    start_period = time_range_match.group(2)
                                    end_hour = int(time_range_match.group(3))
                                    end_period = time_range_match.group(4)
                                    
                                    start_minutes = self._parse_time_to_minutes(f"{start_hour}{start_period}")
                                    end_minutes = self._parse_time_to_minutes(f"{end_hour}{end_period}")
                                    target_minutes = self._parse_time_to_minutes(time_preference)
                                    
                                    if start_minutes is not None and end_minutes is not None and target_minutes is not None:
                                        range_midpoint = (start_minutes + end_minutes) / 2
                                        
                                        # Check if target is within range and closer to middle than edges
                                        if start_minutes < target_minutes < end_minutes:
                                            distance_to_mid = abs(target_minutes - range_midpoint)
                                            distance_to_start = abs(target_minutes - start_minutes)
                                            distance_to_end = abs(target_minutes - end_minutes)
                                            
                                            # Prefer slot where time is closer to middle than to edges
                                            if distance_to_mid < distance_to_start and distance_to_mid < distance_to_end:
                                                selected_time_viewgroup = vg
                                                selected_time_text = viewgroup_text
                                                break
                                            elif not best_match:
                                                # Keep first match as fallback
                                                best_match = {"viewgroup": vg, "time_text": viewgroup_text}
                            elif is_time_range:
                                # Try exact range matching first (e.g., "12pm-2pm" should match "12pm-2pm")
                                # Normalize both to compare (remove spaces, lowercase)
                                normalized_pref = re.sub(r'\s+', '', time_pref_lower)
                                normalized_slot = re.sub(r'\s+', '', viewgroup_text_lower)
                                
                                if normalized_pref in normalized_slot or normalized_slot in normalized_pref:
                                    selected_time_viewgroup = vg
                                    selected_time_text = viewgroup_text
                                    break
                                
                                # Try to parse and compare time ranges
                                pref_range_match = re.search(r'(\d+)\s*(am|pm)\s*[- ]to[ ]\s*(\d+)\s*(am|pm)', time_pref_lower) or \
                                                  re.search(r'(\d+)\s*(am|pm)\s*-\s*(\d+)\s*(am|pm)', time_pref_lower)
                                slot_range_match = re.search(r'(\d+)\s*(am|pm)\s*-\s*(\d+)\s*(am|pm)', viewgroup_text_lower)
                                
                                if pref_range_match and slot_range_match:
                                    pref_start_hour = int(pref_range_match.group(1))
                                    pref_start_period = pref_range_match.group(2)
                                    pref_end_hour = int(pref_range_match.group(3))
                                    pref_end_period = pref_range_match.group(4)
                                    
                                    slot_start_hour = int(slot_range_match.group(1))
                                    slot_start_period = slot_range_match.group(2)
                                    slot_end_hour = int(slot_range_match.group(3))
                                    slot_end_period = slot_range_match.group(4)
                                    
                                    pref_start_min = self._parse_time_to_minutes(f"{pref_start_hour}{pref_start_period}")
                                    pref_end_min = self._parse_time_to_minutes(f"{pref_end_hour}{pref_end_period}")
                                    slot_start_min = self._parse_time_to_minutes(f"{slot_start_hour}{slot_start_period}")
                                    slot_end_min = self._parse_time_to_minutes(f"{slot_end_hour}{slot_end_period}")
                                    
                                    # Check if ranges match exactly
                                    if (pref_start_min == slot_start_min and pref_end_min == slot_end_min):
                                        selected_time_viewgroup = vg
                                        selected_time_text = viewgroup_text
                                        break
                            else:
                                # Try to match specific time range (e.g., "6am-8am", "7am-9am")
                                if time_pref_lower in viewgroup_text_lower:
                                    selected_time_viewgroup = vg
                                    selected_time_text = viewgroup_text
                                    break
                                
                                # Extract time numbers from preference and check if they match
                                # Only use this as last resort for non-range preferences
                                time_numbers = re.findall(r'\d+', time_pref_lower)
                                if time_numbers:
                                    if all(num in viewgroup_text_lower for num in time_numbers):
                                        selected_time_viewgroup = vg
                                        selected_time_text = viewgroup_text
                                        break
                        except Exception:
                            continue
                    
                    # Track seen time slots
                    current_time_texts = {slot["time_text"] for slot in actual_time_slots if slot["time_text"]}
                    new_items = current_time_texts - seen_time_texts
                    seen_time_texts.update(current_time_texts)
                    
                    # If we found a match, break out of the while loop
                    if selected_time_viewgroup:
                        break
                    
                    # If we have a best match for specific time, use it
                    if best_match and is_specific_time and not selected_time_viewgroup:
                        selected_time_viewgroup = best_match["viewgroup"]
                        selected_time_text = best_match["time_text"]
                        break
                    
                    # If not found, scroll down and try again
                    if not selected_time_viewgroup:
                        # Check if we've reached the end (no new items after scrolling)
                        if not new_items:
                            no_new_items_count += 1
                            # If we've scrolled 3 times with no new items, we've reached the end
                            if no_new_items_count >= 3:
                                break
                        else:
                            no_new_items_count = 0  # Reset counter when we find new items
                        
                        self._scroll_recycler_vertical(time_recycler, direction="down")
                        scroll_attempts += 1
                        actual_time_slots = find_time_slots()
                        if not actual_time_slots:
                            break
                
                # Use best match if we have one but didn't find perfect match
                if not selected_time_viewgroup and best_match:
                    selected_time_viewgroup = best_match["viewgroup"]
                    selected_time_text = best_match["time_text"]
                
                if not selected_time_viewgroup:
                    return {"success": False, "message": f"Could not find time slot matching preference '{time_preference}' after scrolling"}
            else:
                # No preference - select first available time slot (not "Full" or "Unavailable")
                for slot in actual_time_slots:
                    try:
                        vg = slot["viewgroup"]
                        viewgroup_text = slot["time_text"]
                        if not viewgroup_text:
                            continue
                        
                        viewgroup_full_text = vg.text.strip() if vg.text else ""
                        viewgroup_content_desc = vg.get_attribute("content-desc") or ""
                        
                        # Skip if it says "Full" or "Unavailable"
                        if "full" not in viewgroup_full_text.lower() and "unavailable" not in viewgroup_full_text.lower() and "full" not in viewgroup_content_desc.lower():
                            selected_time_viewgroup = vg
                            selected_time_text = viewgroup_text
                            break
                    except Exception:
                        continue
                
                if not selected_time_viewgroup:
                    return {"success": False, "message": "No available time slots found (all slots may be full or unavailable)"}
            
            # Click the selected time ViewGroup
            if selected_time_viewgroup:
                try:
                    selected_time_viewgroup.click()
                    time.sleep(1)  # Wait for time selection to register
                except Exception as e:
                    return {"success": False, "message": f"Failed to click time ViewGroup: {str(e)}"}
            
            return {"success": True, "message": f"Time slot selected: {selected_time_text}", "time": selected_time_text}
        
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

