# BearEstate – Feature Overview

This iteration of our project focuses on improving the housing search experience for students by adding price filtering, integrating external listings, and enhancing the roommate posting interface.


This iteration we implemented the following features keyword search, instant messaging, property map feature and secure user authentication.

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

### 4. Instant Messaging
Instant Messaging (IM) was implemented using **Django Channels** to support real-time communication without relying on repeated API polling.

**What was added:**
- Real-time messaging between validated users
- Persistent conversations stored in the database
- A **Chat** page that loads all conversations for a user
- Automatic chat updates when new messages are received


**How it works:**
- Users connect through **WebSockets**
- Messages are cached using a **Redis** daemon running in the background
- Messages are then saved to the Django database
- Each chat belongs to a user and updates automatically when the other user sends a new message
- **Daphne** is used as the **ASGI** server to support asynchronous updates


---

### 5. Interactive Map
The interactive map was updated using **Leaflet** and **OpenStreetMap** to help users view listings visually.

**What was added:**
- Property markers placed on the map using coordinates
- Support for geocoding when coordinates are not available
- Homepage search integration with map redirection
- Search inputs passed from the landing page to the map page

**How it works:**
- RentCast API listings provide latitude and longitude when available
- If coordinates are missing, geocoding is performed using the **US Census Data API**
- The geocoding uses the address, city, and state to find coordinates
- Coordinates are converted into clickable markers
- Each marker displays property information when clicked

**Note:**
- Geocoding is currently only applicable to US addresses

---

### 6. Keyword-Based Search
A keyword-based search feature was implemented to allow users to filter property listings using relevant terms such as location, price, or description.

**How it works:**
- Users can search using meaningful terms related to listings
- Matching properties are filtered based on relevant listing data

This improves usability by helping users quickly find listings that better match their needs.

---

### 7. Secure Authentication
A secure authentication system was implemented using both **Time-based One-Time Passwords (TOTP)** and **email-based verification**.

**What was added:**
- TOTP authentication using dynamically generated codes from authenticator applications
- Email verification using one-time codes

**How it works:**
- A one-time code is sent to the user’s registered email
- The code is temporarily stored in the session
- The system validates the submitted code against the stored value
- TOTP provides an additional secure login method through authenticator apps

This improves account security and helps prevent unauthorized access.

---



### 8. Neighborhood Price Filters

We added Neighborhood Price Filters to help users compare the true monthly cost of living in different areas, not just the rent price.

**What was added:** 
- Neighborhood-based cost breakdown for listings
- Separate display of rent, utilities, and service costs
- Total monthly cost calculation
- Amenity-based filtering
- Price and total-cost sorting on the map page

**How it works:**

- When a user searches on the map page, listings are retrieved and matched with neighborhood cost profiles
- Each listing is enriched with:
- Rent
- Estimated utilities
- Estimated service costs
- Nearby amenities
- Total monthly cost

Users can filter listings by amenities such as:
- Grocery
- Gym
- Transit
- Restaurants
- Coffee

Users can sort listings by:

- Rent: Low to High
- Rent: High to Low
- Total Cost: Low to High
- Total Cost: High to Low

**Map popup details include:**

- Neighborhood name
- Rent
- Utilities
- Services
- Total monthly cost
- Matching amenity
- All nearby amenities

This feature helps users better understand affordability across neighborhoods and compare listings beyond base rent alone.

--- 

 ### 9. AI Listing Agent and AI Chatbot

We implemented an **AI Listing Agent** and an **AI-powered chatbot** to make the housing search experience more interactive, personalized, and responsive.

**What was added:**
- An AI chatbot built on **WebSockets** for real-time interaction  
- Deployment using **Daphne** with Django’s **ASGI** interface  
- Tool-calling functionality for dynamic backend function execution  
- Personalized listing recommendations based on user history  
- A scoring system to rank listings according to relevance  

**How it works:**
- The chatbot communicates with users in real time through **WebSocket** connections  
- **Daphne** serves the Django application through **ASGI**, allowing it to efficiently handle concurrent connections  
- The model can invoke backend functions through tool calling to retrieve and process listing data dynamically  
- Based on user queries, the system can interpret filters, keywords, and preferences, fetch relevant listing data, and return structured, context-aware responses  
- The AI Listing Agent maintains a history of user interactions and prior searches  
- This history is used to generate personalized recommendations  
- A scoring mechanism ranks listings using user preferences, prior queries, and relevant listing attributes  

This feature improves the housing search experience by making recommendations smarter, more personalized, and more responsive to user needs.

---


### 10. Social Posts Feed

This sprint, we implemented the **Social Posts** functionality, which creates a feed of the most recently posted listings for users to view directly from the homepage.

**What was added:**
- A homepage feed showing the latest listing posts
- Real-time updating behavior using **ASGI**
- Direct navigation from the homepage feed to listing pages
- Backend integration to pull listing data from the database
- Frontend updates to support feed display and user interaction

**How it works:**
- The homepage repeatedly checks for newly created posts using **ASGI-based** updates
- Newly added listings are displayed in a feed so users can quickly see the most recent posts
- Users can click on listings from the homepage feed to view more details or navigate to the listing creation flow
- The feature connects frontend page updates with backend database retrieval to keep the feed current and interactive

---

### 11. Additional Testing Contributions

During this sprint, we also took over a portion of the **functional, unit, and integration testing** . In particular, we created tests for the **Neighborhood Price Comparison** feature and the **Social Posts** feature.

We developed tests to verify:
- Page load status
- Correct application of filter logic
- Real-time broadcasting behavior

---

### 12. Testing Approach (TDD)

We followed a test-driven development (TDD) approach using the **red–green–refactor cycle**.

- Red: Wrote tests before implementation  
- Green: Implemented features until tests passed  
- Refactor: Cleaned and improved code  

**Tests included:**
- Registration tests (signup, login, invalid inputs)  
- Property search tests (location filtering, price filtering, API mocking)  
- Roommate posting tests (create, view, close, delete, permission checks)  

Overall, the project achieved approximately **85% code coverage**.


## Files Updated

### views.py
- Handles search filtering logic  
- Applies price range filtering  
- Calls the RentCast API  
- Passes results to templates  
- Supports keyword search and map-related search behavior
- Added neighborhood cost enrichment for map listings
- Added amenity filtering and total-cost sorting
- Added agent recommendation scoring and curated listing logic

### rentcast_api.py
- Sends requests to the RentCast API  
- Returns property listing data
- Supplies coordinate data when available 


### bear_estate_homepage.html
- Added budget dropdown  
- Displays database and API listings  
- Connects homepage search to other features such as the interactive map

### models.py
- Updated for roommate postings  
- Integrated with Django REST Framework  
- Supports messaging-related data storage


---

### Roommate posting templates
- Added input fields for roommate posts
- Supports expandable post view
- Includes carousel browsing behavior


### Messaging-related files
- Added Django Channels support
- Added WebSocket routing
- Added ASGI configuration with Daphne
- Added Redis-based message handling

### map.html

- Added neighborhood cost breakdown in map popups
- Added matching amenity and full amenity display
- Added Agent Picks sidebar with curated recommendations

### Map-related frontend files
- Updated interactive map using Leaflet and OpenStreetMap
- Added marker rendering and click behavior
- Added geocoding support for missing coordinates

--- 

## Example Search

**Input:**
- Location: Denver  
- Type: Apartment  
- Budget: $900 – $1,400  

**Output:**
- Matching properties from the database  
- Additional listings from the RentCast API  
- Map-based results when applicable

---

## Dependencies

```bash
pip install requests
pip install djangorestframework
pip install channels
pip install channels-redis
pip install daphne

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
- Debugging issues  
- Ensuring correct data fetching and display  
- implementing leaflet 

---

## Summary

This feature improves the user experience by:
- Allowing price-based filtering  
- Expanding listings using an external API  
- Providing an interactive roommate posting interface  
- Supporting keyword-based property search  
- Enabling real-time instant messaging between users  
- Adding an interactive map for visual property browsing  
- Strengthening account security through secure authentication 
- Comparing neighborhood-level living costs through Neighborhood Price Filters
- Generating curated agent recommendations through Agent Advertising

Overall, it helps students find housing more efficiently, communicate more easily, and explore more options in a secure and user-friendly platform.