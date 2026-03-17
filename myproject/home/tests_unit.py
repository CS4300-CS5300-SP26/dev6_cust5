from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from home.models import RoommatePost, Property
from home.forms import RoommatePostForm, CustomRegisterForm

class RoommatePostFormTest(TestCase):
    def _valid_data(self, **overrides):
        data = {
            'message': 'Looking for a roommate.',
            'date': '2026-03-11',
            'status': 'open',
            'rent': 1000,
            'property_type': 'apartment',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        """
        Roommate Post form should be valid
        """
        form = RoommatePostForm(data=self._valid_data())
        self.assertTrue(form.is_valid())

    def test_missing_message_invalid(self):
        """
        If message is empty, the form is not valid
        """
        form = RoommatePostForm(data=self._valid_data(message=''))
        self.assertFalse(form.is_valid())
        self.assertIn('message', form.errors)

    def test_missing_date_invalid(self):
        """
        The form rejects submission when the date is missing
        """
        form = RoommatePostForm(data=self._valid_data(date=''))
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_rent_is_optional(self):
        form = RoommatePostForm(data=self._valid_data(rent=''))
        self.assertTrue(form.is_valid())

    def test_invalid_status(self):
        """
        Status can only be Open or Closed
        """
        form = RoommatePostForm(data=self._valid_data(status='maybe'))
        self.assertFalse(form.is_valid())

class RoommatePostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', password='pass')

    def test_default_status_is_open(self):
        """
        Tests that a new roommate post gets status open by default
        """
        post = RoommatePost.objects.create(
            user=self.user, message='Hi', date='2026-03-01'
        )
        self.assertEqual(post.status, 'open')

    def test_rent_is_optional(self):
        """
        Rent could be optional
        """
        post = RoommatePost.objects.create(
            user=self.user, message='Hi', date='2026-03-01'
        )
        self.assertIsNone(post.rent)

    def test_property_type_defaults_to_empty(self):
        """
        If not property type, returns string
        """
        post = RoommatePost.objects.create(
            user=self.user, message='Hi', date='2026-03-01'
        )
        self.assertEqual(post.property_type, '')

    def test_user_deletion_cascades(self):
        """
        If user is deleted, their posts are also deleted
        """
        RoommatePost.objects.create(
            user=self.user, message='Hi', date='2026-03-01'
        )
        self.user.delete()
        self.assertEqual(RoommatePost.objects.count(), 0)


class PropertyModelTest(TestCase):
    def test_description_is_optional(self):
        """
        Decription is optional
        """
        prop = Property.objects.create(
            title='Test', location='Denver, CO',
            listing_type='rent', property_type='house', price=900
        )
        self.assertEqual(prop.description, '')




class CustomRegisterFormTest(TestCase):
    def _valid_data(self, **overrides):
        data = {
            'username': 'newuser',
            'email': '',
            'password1': 'StrongPassword@123',
            'password2': 'StrongPassword@123',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        """
        Form is valid
        """
        form = CustomRegisterForm(data=self._valid_data())
        self.assertTrue(form.is_valid())

    def test_email_is_optional(self):
        """
        Email is optional
        """
        form = CustomRegisterForm(data=self._valid_data(email=''))
        self.assertTrue(form.is_valid())

    def test_mismatched_passwords_invalid(self):
        """
        If the password is mismatched, then you won't be able to register - form invalid
        """
        form = CustomRegisterForm(data=self._valid_data(password2='different'))
        self.assertFalse(form.is_valid())

    def test_missing_username_invalid(self):
        """
        Username is not optional
        """
        form = CustomRegisterForm(data=self._valid_data(username=''))
        self.assertFalse(form.is_valid())



class RentcastAPITest(TestCase):
    @patch('home.rentcast_api.requests.get')
    def test_returns_list_on_200(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{'formattedAddress': '123 Main St', 'price': 1200}]
        )
        from home.rentcast_api import get_properties
        result = get_properties('Denver, CO')
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    @patch('home.rentcast_api.requests.get')
    def test_returns_empty_list_on_non_200(self, mock_get):
        mock_get.return_value = MagicMock(status_code=404)
        from home.rentcast_api import get_properties
        result = get_properties('Denver, CO')
        self.assertEqual(result, [])

    @patch('home.rentcast_api.API_KEY', None)
    def test_returns_empty_list_when_no_api_key(self):
        from home.rentcast_api import get_properties
        result = get_properties('Denver, CO')
        self.assertEqual(result, [])

    @patch('home.rentcast_api.requests.get')
    def test_filters_by_min_price(self, mock_get):
        """
        Tests that the function removes properties below the minimum price
        """
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {'price': 900},
                {'price': 1500},
                {'price': 500},
            ]
        )
        from home.rentcast_api import get_properties
        result = get_properties('Denver, CO', min_price=1000)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['price'], 1500)

    @patch('home.rentcast_api.requests.get')
    def test_filters_by_max_price(self, mock_get):
        """
        Tests that the function removes properties below the maximum price
        """
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {'price': 900},
                {'price': 1500},
            ]
        )
        from home.rentcast_api import get_properties
        result = get_properties('Denver, CO', max_price=1000)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['price'], 900)