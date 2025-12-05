# Walmart App Element Mapping - Quick Guide

## Using Appium Inspector to Find Elements

### **Step 1: Open Walmart App**
1. In Inspector, tap Walmart app icon (or use API: `POST /api/v1/automation/open-walmart`)
2. Wait for app to fully load

### **Step 2: Find Search Bar**
1. **Look at top of screen** - there's usually a search bar
2. **Click on search bar** in Inspector
3. **In right panel**, look for:
   - **resource-id**: Copy this (e.g., `com.walmart.android:id/search_src_text`)
   - **XPath**: Also copy this as backup
4. **Test it**: Click "Tap" button in Inspector to verify

### **Step 3: Find Search Button**
1. **After clicking search bar**, keyboard appears
2. **Look for search/magnifying glass icon** next to search bar
3. **Click on it** in Inspector
4. **Record resource-id** and XPath

### **Step 4: Find Product List**
1. **Type "milk" in search** (manually or via Inspector)
2. **Tap search button**
3. **Wait for results** - products appear in a list
4. **Click on the list container** (not individual products)
5. **Record resource-id** (usually `recycler_view` or `product_list`)

### **Step 5: Find First Product**
1. **Click on first product** in the list
2. **Record**:
   - Container XPath pattern
   - Product name element
   - Price element (optional)

### **Step 6: Find "Add to Cart" Button**
1. **On product page** (after clicking product), find "Add to Cart" button
2. **Click on it** in Inspector
3. **Record resource-id** (e.g., `com.walmart.android:id/add_to_cart_button`)
4. **Also check if button has text** like "Add to cart"

## Quick Element Checklist

- [ ] Search bar resource-id: `_________________`
- [ ] Search button resource-id: `_________________`
- [ ] Product list resource-id: `_________________`
- [ ] First product XPath pattern: `_________________`
- [ ] Add to Cart button resource-id: `_________________`
- [ ] Add to Cart button text (if any): `_________________`

## Common Walmart Element IDs (Verify These!)

These are common patterns - **verify with Inspector**:

- Search: `com.walmart.android:id/search_src_text`
- Search button: `com.walmart.android:id/search_go_btn` or `com.walmart.android:id/search_button`
- Product list: `com.walmart.android:id/recycler_view`
- Add to cart: `com.walmart.android:id/add_to_cart_button` or `com.walmart.android:id/btn_add_to_cart`

## Testing Selectors

In Inspector, you can:
1. **Select element** → See details
2. **Click "Tap"** → Test if element is found
3. **Use "Send Keys"** → Test typing
4. **Take screenshot** → Save for reference

## Next: Update Code

Once you have all selectors, update `automation.py` with the real values.

