from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch
from home.models import RoommatePost, Property


class AuthFlowIntegrationTest(TestCase):
    """Full register → login → logout flow."""

    def test_register_then_login_flow(self):
        # register
        self.client.post('/register/', {
            'username': 'flowuser',
            'password1': 'StrongPassword@123',
            'password2': 'StrongPassword@123',
        })
        self.assertTrue(User.objects.filter(username='flowuser').exists())

        # login
        response = self.client.post('/', {
            'username': 'flowuser',
            'password': 'StrongPassword@123',
        })
        self.assertEqual(response.status_code, 302)

    def test_invalid_login_stays_on_page(self):
        response = self.client.post('/', {
            'username': 'nobody',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

    def test_duplicate_username_rejected(self):
        User.objects.create_user(username='existing', password='pass')
        response = self.client.post('/register/', {
            'username': 'existing',
            'password1': 'StrongPassword@123',
            'password2': 'StrongPassword@123',
        })
        self.assertEqual(User.objects.filter(username='existing').count(), 1)


class RoommatePostFlowIntegrationTest(TestCase):
    """Full create → view → close → delete flow."""

    def setUp(self):
        self.user = User.objects.create_user(username='poster', password='Password123!')
        self.other = User.objects.create_user(username='other', password='Password123!')
        self.client.login(username='poster', password='Password123!')

    def _create_post(self):
        return RoommatePost.objects.create(
            user=self.user,
            message='Need a roommate ASAP.',
            date='2026-03-11',
            status='open',
            rent=950,
            property_type='apartment',
        )

    def test_create_then_view_post(self):
        self.client.post('/roommate-posts/create/', {
            'message': 'Need a roommate ASAP.',
            'date': '2026-03-11',
            'status': 'open',
            'rent': 950,
            'property_type': 'apartment',
        })
        response = self.client.get('/roommate-posts/')
        self.assertContains(response, 'Need a roommate ASAP.')

    def test_create_then_close_then_status_shows_closed(self):
        post = self._create_post()
        self.client.post(f'/roommate-posts/{post.id}/close/')
        post.refresh_from_db()
        self.assertEqual(post.status, 'closed')

        response = self.client.get('/roommate-posts/')
        self.assertContains(response, 'Closed')

    def test_create_then_delete_removes_from_list(self):
        post = self._create_post()
        self.client.post(f'/roommate-posts/{post.id}/delete/')
        response = self.client.get('/roommate-posts/')
        self.assertNotContains(response, 'Need a roommate ASAP.')

    def test_unauthenticated_create_redirects_to_login(self):
        self.client.logout()
        response = self.client.get('/roommate-posts/create/')
        self.assertRedirects(response, '/?next=/roommate-posts/create/')

    def test_other_user_delete_returns_404(self):
        post = self._create_post()
        self.client.login(username='other', password='Password123!')
        response = self.client.post(f'/roommate-posts/{post.id}/delete/')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(RoommatePost.objects.count(), 1)

    def test_other_user_close_returns_404(self):
        post = self._create_post()
        self.client.login(username='other', password='Password123!')
        response = self.client.post(f'/roommate-posts/{post.id}/close/')
        self.assertEqual(response.status_code, 404)
        post.refresh_from_db()
        self.assertEqual(post.status, 'open')


class PropertySearchIntegrationTest(TestCase):
    """Property search filtering with mocked API."""

    def setUp(self):
        Property.objects.create(
            title='Cheap Apt', price=900,
            property_type='apartment', listing_type='rent', location='Denver'
        )
        Property.objects.create(
            title='Expensive Apt', price=2500,
            property_type='apartment', listing_type='rent', location='Denver'
        )
        Property.objects.create(
            title='Cheap House', price=900,
            property_type='house', listing_type='rent', location='Denver'
        )

    @patch('home.views.get_properties', return_value=[])
    def test_search_by_location_returns_all_matches(self, _):
        response = self.client.get('/', {'location': 'Denver'})
        self.assertContains(response, 'Cheap Apt')
        self.assertContains(response, 'Expensive Apt')
        self.assertContains(response, 'Cheap House')

    @patch('home.views.get_properties', return_value=[])
    def test_search_filters_by_type(self, _):
        response = self.client.get('/', {
            'location': 'Denver', 'type': 'apartment'
        })
        self.assertContains(response, 'Cheap Apt')
        self.assertNotContains(response, 'Cheap House')

    @patch('home.views.get_properties', return_value=[])
    def test_search_filters_by_price_range(self, _):
        response = self.client.get('/', {
            'location': 'Denver', 'budget': '900-1000'
        })
        self.assertContains(response, 'Cheap Apt')
        self.assertNotContains(response, 'Expensive Apt')

    @patch('home.views.get_properties', return_value=[])
    def test_no_location_returns_no_api_results(self, mock_api):
        self.client.get('/')
        mock_api.assert_not_called()