# BearEstate – Feature Overview

This iteration of our project focuses on improving the housing search experience for students by adding price filtering, integrating external listings, and enhancing the roommate posting interface.
Live Website: https://bearestate.me/
---

## Features Implemented

### 1. Price Range Filtering
We added a price range filter to help users find housing within their budget more easily.

A dropdown menu was added to the search bar with options such as:
- Any Price  
- Under $900  
- $900 – $1,400  
- $1,400 – $2,000  
- $2,000+  

When the user submits the search:
- The selected range is split into a minimum and maximum price  
- The system filters properties in the database using those values  

This allows users to quickly narrow down listings that match their budget.

---

### 2. RentCast API Integration
To expand the number of available listings, we integrated the RentCast API.

When a user searches by location:
- The system sends a request to the API  
- Additional listings are returned and displayed under **"Additional Listings"**

Each API listing includes:
- Property address  
- City  
- Property type  
- Bedrooms and bathrooms  
- Square footage  
- Year built  

This ensures users can still find housing options even if the database has limited results.

---

### 3. Roommate Posting UI (Frontend Work)

The roommate posting page was redesigned and expanded.

**Tasks completed:**
- Created a roommate posting HTML page  
- Reused the homepage layout (banner, search bar, styling)  
- Added input fields for roommate posts  
- Built expandable post view (click to zoom in/out)  
- Implemented a carousel to browse posts  

**How it works:**
- Users can scroll through roommate posts horizontally  
- Clicking a post expands it to show full details  
- Clicking again closes the expanded view  

---

### 4. Testing Approach (TDD)

We followed a test-driven development (TDD) approach using the **red–green–refactor cycle**.

- Red: Wrote tests before implementation  
- Green: Implemented features until tests passed  
- Refactor: Cleaned and improved code  

**Tests included:**
- Registration tests (signup, login, invalid inputs)  
- Property search tests (location filtering, price filtering, API mocking)  
- Roommate posting tests (create, view, close, delete, permission checks)  

Overall, the project achieved approximately **91% code coverage**.

---

## Files Updated

### views.py
- Handles search filtering logic  
- Applies price range filtering  
- Calls the RentCast API  
- Passes results to templates  

### rentcast_api.py
- Sends requests to the RentCast API  
- Returns property listing data  

### bear_estate_homepage.html
- Added budget dropdown  
- Displays database and API listings  

### models.py
- Updated for roommate postings  
- Integrated with Django REST Framework  

---

## Example Search

**Input:**
- Location: Denver  
- Type: Apartment  
- Budget: $900 – $1,400  

**Output:**
- Matching properties from the database  
- Additional listings from the RentCast API  

---

## Dependencies

```bash
pip install requests
pip install djangorestframework
```

Django REST Framework is required for roommate post handling.

---

## AI Usage

Claude AI was used during frontend development to:
- Structure HTML/CSS  
- Debug errors  
- Implement UI features like expand/collapse and carousel layouts  

ChatGPT was used for:
- RentCast API implementation  
- Debugging API issues  
- Ensuring correct data fetching and display  

---

## Summary

This feature improves the user experience by:
- Allowing price-based filtering  
- Expanding listings using an external API  
- Providing an interactive roommate posting interface  

Overall, it helps students find housing more efficiently while giving them more options.