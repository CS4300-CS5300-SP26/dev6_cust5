Feature: Property Search
  As a visitor
  I want to search for properties by location, type, and price
  So that I can find housing that fits my needs

  Background:
    Given the following properties exist:
      | title               | price | type      | location |
      | Cheap Apartment     | 850   | apartment | Denver   |
      | Expensive Apartment | 2500  | apartment | Denver   |
      | Cheap House         | 800   | house     | Denver   |

  Scenario: Search by location returns all matches
    When I search for location "Denver"
    Then I see "Cheap Apartment" in the results
    And I see "Cheap House" in the results

  Scenario: Search filters by property type
    When I search for location "Denver" and type "apartment"
    Then I see "Cheap Apartment" in the results
    And I do not see "Cheap House" in the results

  Scenario: Search filters by price range
    When I search for location "Denver" and budget "800-1000"
    Then I see "Cheap Apartment" in the results
    And I do not see "Expensive Apartment" in the results