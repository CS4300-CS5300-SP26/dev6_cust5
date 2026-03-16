from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch


class RegisterTest(TestCase):
    def test_register_page_success(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_register_creates_user(self):
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
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_valid_login_redirect(self):
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
        response = self.client.get('/', {
            'location': 'test',
            'budget': '800-1000',
            'type': 'apartment',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Affordable Apartment")   # $1000 apartment ✓
        self.assertNotContains(response, "Luxury Apartment")    # $2000 — too expensive
        self.assertNotContains(response, "Affordable House")    # wrong type
        self.assertNotContains(response, "Expensive House")     # wrong type + price


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
        response = self.client.get('/roommate-posts/')
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_cannot_access_create(self):
        self.client.logout()
        response = self.client.get('/roommate-posts/create/')
        self.assertNotEqual(response.status_code, 200)  # redirects to login

    def test_create_post_saves_to_database(self):
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