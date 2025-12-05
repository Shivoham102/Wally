# Walmart App UI Element Mapping Guide

## Step-by-Step Element Discovery

### **1. Open Walmart App in Inspector**

1. **In Appium Inspector**, you should see your phone's home screen
2. **Find Walmart app icon** and tap it (or use `open_walmart_app` API first)
3. **Wait for app to load** - you'll see the Walmart app interface

### **2. Map Search Elements**

#### **A. Find Search Bar**
1. **Look for the search bar** at the top of Walmart app
2. **Click on it** in Inspector
3. **In the element details panel**, look for:
   - **resource-id**: Usually `com.walmart.android:id/search_src_text` or similar
   - **XPath**: Copy the full XPath
   - **content-desc**: Accessibility label
4. **Record the selector** (prefer resource-id, fallback to XPath)

#### **B. Find Search Button**
1. **After typing in search bar**, look for search/magnifying glass button
2. **Click on it** in Inspector
3. **Record**:
   - resource-id
   - XPath
   - content-desc

### **3. Map Product List Elements**

#### **A. Find Product List Container**
1. **After searching**, products appear in a list
2. **Click on the list container** (not individual products)
3. **Record**:
   - resource-id (e.g., `com.walmart.android:id/recycler_view`)
   - XPath to list

#### **B. Find Individual Product Items**
1. **Click on first product** in results
2. **Record**:
   - resource-id for product item
   - XPath pattern (usually `//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[1]`)

#### **C. Find Product Name Element**
1. **Within a product item**, find the product name text
2. **Record**:
   - resource-id
   - XPath

### **4. Map Add to Cart Elements**

#### **A. Find "Add to Cart" Button**
1. **On product page or in list**, find "Add to Cart" button
2. **Click on it** in Inspector
3. **Record**:
   - resource-id (e.g., `com.walmart.android:id/add_to_cart_button`)
   - XPath
   - Text: "Add to cart" or "Add"

#### **B. Find Quantity Selector (if needed)**
1. **Some products** have quantity +/- buttons
2. **Record** if present

### **5. Map Navigation Elements**

#### **A. Back Button**
- Usually system back button, but check if Walmart has custom back

#### **B. Cart Icon**
- Find cart icon to verify items added
- resource-id or XPath

## Element Selector Priority

**Best to Worst:**
1. **resource-id** (most reliable)
2. **content-desc** (accessibility label)
3. **XPath** (can break with UI changes)
4. **Text** (last resort)

## Recording Your Findings

Create a file or document with:

```json
{
  "search_bar": {
    "resource_id": "com.walmart.android:id/search_src_text",
    "xpath": "//android.widget.EditText[@resource-id='com.walmart.android:id/search_src_text']",
    "fallback": "content-desc"
  },
  "search_button": {
    "resource_id": "com.walmart.android:id/search_go_btn",
    "xpath": "..."
  },
  "product_list": {
    "resource_id": "com.walmart.android:id/recycler_view",
    "xpath": "..."
  },
  "product_item": {
    "xpath_pattern": "//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[{index}]"
  },
  "add_to_cart_button": {
    "resource_id": "com.walmart.android:id/add_to_cart_button",
    "text": "Add to cart"
  }
}
```

## Common Walmart App Element Patterns

**Note:** These are examples - you need to verify with Inspector:

- Search bar: Usually `search_src_text` or `search_box`
- Product list: Usually `recycler_view` or `product_list`
- Add to cart: Usually `add_to_cart` or `btn_add_to_cart`
- Product name: Usually `product_title` or `item_name`

## Tips

1. **Use Inspector's "Select Elements" mode** - hover to see element details
2. **Take screenshots** of element details for reference
3. **Test selectors** - click "Tap" in Inspector to verify element is found
4. **Handle dynamic content** - product lists use RecyclerView, items are dynamic
5. **Wait for elements** - use explicit waits in code, not fixed sleep times

## Next Steps

Once you have all selectors:
1. Update `automation.py` with real selectors
2. Test each action individually
3. Handle edge cases (out of stock, variants, etc.)

