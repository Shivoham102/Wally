"""Walmart app UI selectors loader."""
import json
import os
from typing import Dict, Any


class WalmartSelectors:
    """Load and provide access to Walmart app UI selectors."""
    
    def __init__(self):
        self.selectors = self._load_selectors()
    
    def _load_selectors(self) -> Dict[str, Any]:
        """Load selectors from JSON file."""
        # Get the path to selectors.json (in utils folder, same directory as this file)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        selectors_path = os.path.join(current_dir, "walmart_app_selectors.json")
        
        try:
            with open(selectors_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Selectors file not found: {selectors_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in selectors file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get selector value by key."""
        return self.selectors.get(key, default)
    
    @property
    def search_bar_id(self) -> str:
        """Get search bar resource ID."""
        return self.get("search_bar", {}).get("resource_id", "")
    
    @property
    def search_bar_uiselector(self) -> str:
        """Get search bar UiSelector."""
        return self.get("search_bar", {}).get("uiselector", "")
    
    @property
    def clear_search_id(self) -> str:
        """Get clear search button resource ID."""
        return self.get("clear_search_bar", {}).get("resource_id", "")
    
    @property
    def clear_search_uiselector(self) -> str:
        """Get clear search button UiSelector."""
        return self.get("clear_search_bar", {}).get("uiselector", "")
    
    @property
    def products_recycler_id(self) -> str:
        """Get products RecyclerView resource ID."""
        return self.get("product_list", {}).get("resource_id", "")
    
    @property
    def products_recycler_uiselector(self) -> str:
        """Get products RecyclerView UiSelector."""
        return self.get("product_list", {}).get("uiselector", "")
    
    @property
    def first_product_xpath(self) -> str:
        """Get first product XPath."""
        return self.get("product_item", {}).get("first_product_xpath", "")
    
    @property
    def first_product_uiselector(self) -> str:
        """Get first product UiSelector."""
        return self.get("product_item", {}).get("first_product_uiselector", "")
    
    @property
    def add_to_cart_xpath(self) -> str:
        """Get add to cart button XPath."""
        return self.get("add_to_cart_button", {}).get("xpath", "")
    
    @property
    def add_to_cart_uiselector(self) -> str:
        """Get add to cart button UiSelector."""
        return self.get("add_to_cart_button", {}).get("uiselector", "")
    
    @property
    def cart_plus_button_id(self) -> str:
        """Get cart plus button resource ID."""
        return self.get("cart_plus_button", {}).get("resource_id", "")
    
    @property
    def cart_plus_button_uiselector(self) -> str:
        """Get cart plus button UiSelector."""
        return self.get("cart_plus_button", {}).get("uiselector", "")
    
    @property
    def cart_minus_button_id(self) -> str:
        """Get cart minus button resource ID."""
        return self.get("cart_minus_button", {}).get("resource_id", "")
    
    @property
    def cart_minus_button_uiselector(self) -> str:
        """Get cart minus button UiSelector."""
        return self.get("cart_minus_button", {}).get("uiselector", "")


# Global instance
selectors = WalmartSelectors()

