from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch
import json

class RegisterTest(TestCase):
    def test_register_page_success(self):
        """
        Tests that the registration page loads without crashing
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_register_creates_user(self):
        """
        Tests that submitting valid registration data actually creates a user in the database
        """
        self.client.post('/register/', {
            'username': 'testuser',
            'password1': 'StrongPassword@123',
            'password2': 'StrongPassword@123',
        })
        self.assertTrue(User.objects.filter(username='testuser').exists())


class LoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='StrongPassword@123'
        )

    def test_login_page_success(self):
        """
        ests that the login page is accessible and doesn't crash
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_valid_login_redirect(self):
        """
        Tests that valid login credentials successfully log the user in and trigger a redirect
        """
        response = self.client.post('/', {
            'username': 'testuser',
            'password': 'StrongPassword@123',
        })
        self.assertEqual(response.status_code, 302)


class PropertyFilterTests(TestCase):
    def setUp(self):
        from home.models import Property
        Property.objects.create(
            title="Affordable Apartment", price=1000,
            property_type="apartment", listing_type="rent", location="test"
        )
        Property.objects.create(
            title="Luxury Apartment", price=2000,
            property_type="apartment", listing_type="rent", location="test"
        )
        Property.objects.create(
            title="Affordable House", price=900,
            property_type="house", listing_type="rent", location="test"
        )
        Property.objects.create(
            title="Expensive House", price=3000,
            property_type="house", listing_type="rent", location="test"
        )

    @patch('home.views.get_properties', return_value=[])
    def test_filter_by_price_range_and_property_type_returns_only_matching_properties(self, mock_api):
        """
        Tests that filtering by BOTH price range AND property type returns only the correct properties
        """
        response = self.client.get('/', {
            'location': 'test',
            'budget': '800-1000',
            'type': 'apartment',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Affordable Apartment")   
        self.assertNotContains(response, "Luxury Apartment")   
        self.assertNotContains(response, "Affordable House")    
        self.assertNotContains(response, "Expensive House")     


class RoommatePostingTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='poster', password='Password123!')
        self.other_user = User.objects.create_user(username='other', password='Password123!')
        self.client.login(username='poster', password='Password123!')

    def _create_post(self):
        from home.models import RoommatePost
        return RoommatePost.objects.create(
            user=self.user,
            message='Looking for a roommate near campus.',
            date='2026-03-11',
            status='open',
            rent=1000,
            property_type='apartment',
        )

    def test_roommate_list_returns_200(self):
        """
        Tests that the roommate posts list page loads correctly
        """
        response = self.client.get('/roommate-posts/')
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_cannot_access_create(self):
        """
        Tests that only logged-in users can access the create-post page
        """
        self.client.logout()
        response = self.client.get('/roommate-posts/create/')
        self.assertNotEqual(response.status_code, 200)  # redirects to login

    def test_create_post_saves_to_database(self):
        """
        Tests that submitting the create-post form actually saves a roommate post
        """
        from home.models import RoommatePost
        self.client.post('/roommate-posts/create/', {
            'message': 'Looking for a roommate near campus.',
            'date': '2026-03-11',
            'status': 'open',
            'rent': 1000,
            'property_type': 'apartment',
        })
        self.assertEqual(RoommatePost.objects.count(), 1)

    def test_owner_can_delete_post(self):
        from home.models import RoommatePost
        post = self._create_post()
        self.client.post(f'/roommate-posts/{post.id}/delete/')
        self.assertEqual(RoommatePost.objects.count(), 0)

    def test_non_owner_cannot_delete_post(self):
        from home.models import RoommatePost
        post = self._create_post()
        self.client.login(username='other', password='Password123!')
        self.client.post(f'/roommate-posts/{post.id}/delete/')
        self.assertEqual(RoommatePost.objects.count(), 1)  # post still exists

    def test_owner_can_close_post(self):
        from home.models import RoommatePost
        post = self._create_post()
        self.client.post(f'/roommate-posts/{post.id}/close/')
        post.refresh_from_db()
        self.assertEqual(post.status, 'closed')

    def test_non_owner_cannot_close_post(self):
        from home.models import RoommatePost
        post = self._create_post()
        self.client.login(username='other', password='Password123!')
        self.client.post(f'/roommate-posts/{post.id}/close/')
        post.refresh_from_db()
        self.assertEqual(post.status, 'open')  


class PropertyMapTest(TestCase):
    # A dedicated map endpoint must exist and be reachable
    def test_property_map_endpoint_returns_200(self):
        response = self.client.get('/map/', {'location': 'Boulder, CO'})
        self.assertEqual(response.status_code, 200)
 
   
    # The response must include coordinate data for each listing
    @patch('home.views.get_properties')
    def test_map_response_includes_coordinates_for_listings(self, mock_api):
        mock_api.return_value = [
            {
                'id': 'abc123',
                'addressLine1': '123 Main St',
                'city': 'Boulder',
                'state': 'CO',
                'price': 1500,
                'latitude': 40.0150,
                'longitude': -105.2705,
                'propertyType': 'Apartment',
            }
        ]
 
        response = self.client.get('/map/', {'location': 'Boulder, CO'})
        self.assertEqual(response.status_code, 200)
 
        # The view must expose map_properties in its context so the template
        # Each item must carry lat/lng.
        map_properties = response.context.get('map_properties', [])
        self.assertTrue(len(map_properties) > 0, "map_properties context key is empty")
 
        first = map_properties[0]
        self.assertIn('latitude', first,  "latitude missing from map property")
        self.assertIn('longitude', first, "longitude missing from map property")

class KeywordSearchTests(TestCase):
    def setUp(self):
        from home.models import Property
        Property.objects.create(
            title="Cozy Studio near CU Campus",
            price=900,
            property_type="studio",
            listing_type="rent",
            location="Boulder, CO",
            amenities="gym, parking, laundry",
        )
        Property.objects.create(
            title="Downtown Loft with Rooftop",
            price=1800,
            property_type="apartment",
            listing_type="rent",
            location="Denver, CO",
            amenities="rooftop, concierge, pool",
        )
        Property.objects.create(
            title="Quiet House near Flatirons",
            price=2200,
            property_type="house",
            listing_type="rent",
            location="Boulder, CO",
            amenities="garage, backyard, pet-friendly",
        )
 
    # The search endpoint must exist and return 200 for a keyword query
    def test_keyword_search_endpoint_returns_200(self):
        response = self.client.get('/search/', {'q': 'studio'})
        self.assertEqual(response.status_code, 200)
 
    # A keyword matching part of a title must return that listing
    def test_search_by_title_keyword_returns_matching_property(self):
        response = self.client.get('/search/', {'q': 'Loft'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Downtown Loft with Rooftop")
        self.assertNotContains(response, "Cozy Studio near CU Campus")
        self.assertNotContains(response, "Quiet House near Flatirons")
 
    # A keyword matching a location must surface listings in that location
    def test_search_by_location_keyword_returns_matching_properties(self):
        response = self.client.get('/search/', {'q': 'Boulder'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cozy Studio near CU Campus")
        self.assertContains(response, "Quiet House near Flatirons")
        self.assertNotContains(response, "Downtown Loft with Rooftop")
 
 
class DirectMessagingTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='Pass123!')
        self.bob   = User.objects.create_user(username='bob',   password='Pass123!')
        self.carol = User.objects.create_user(username='carol', password='Pass123!')
        self.client.login(username='alice', password='Pass123!')
 
 
    # The inbox endpoint must exist and be accessible to authenticated users
    def test_inbox_endpoint_returns_200_for_authenticated_user(self):
        response = self.client.get('/messages/')
        self.assertEqual(response.status_code, 200)
 
    # Unauthenticated users must be redirected away from the inbox
    def test_unauthenticated_user_cannot_access_inbox(self):
        self.client.logout()
        response = self.client.get('/messages/')
        self.assertNotEqual(response.status_code, 200)
 
 
    # Sending a message must persist it to the database
    def test_send_message_saves_to_database(self):
        from home.models import DirectMessage
        self.client.post('/messages/send/', {
            'recipient': self.bob.id,
            'body': 'Hi Bob, is the room still available?',
        })
        self.assertEqual(DirectMessage.objects.count(), 1)
 
 
class TwoFactorAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='secureuser', password='StrongPass@99'
        )
        self.client.login(username='secureuser', password='StrongPass@99')
 
    # The 2FA setup page must exist and be accessible to authenticated users
    def test_2fa_setup_page_returns_200(self):
        response = self.client.get('/auth/2fa/setup/')
        self.assertEqual(response.status_code, 200)
 
    # Unauthenticated users must not be able to reach the 2FA setup page
    def test_unauthenticated_user_cannot_access_2fa_setup(self):
        self.client.logout()
        response = self.client.get('/auth/2fa/setup/')
        self.assertNotEqual(response.status_code, 200)
 
    # The setup page must provide a TOTP secret (QR or base32 key) in context
    def test_2fa_setup_provides_totp_secret_in_context(self):
        response = self.client.get('/auth/2fa/setup/')
        self.assertIn('totp_secret', response.context)
        secret = response.context['totp_secret']
        self.assertTrue(len(secret) > 0)