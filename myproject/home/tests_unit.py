from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from home.models import RoommatePost, Property
from home.forms import RoommatePostForm, CustomRegisterForm
import json


# Roommate Post Form
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
        checks if Roommate form is valid
        """
        self.assertTrue(RoommatePostForm(data=self._valid_data()).is_valid())

    def test_missing_message_invalid(self):
        """
        Message field should be valid
        """
        form = RoommatePostForm(data=self._valid_data(message=''))
        self.assertFalse(form.is_valid())
        self.assertIn('message', form.errors)

    def test_missing_date_invalid(self):
        """
        Date should be valid
        """
        form = RoommatePostForm(data=self._valid_data(date=''))
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_rent_is_optional(self):
        """
        Rent is optional
        """
        self.assertTrue(RoommatePostForm(data=self._valid_data(rent='')).is_valid())

    def test_invalid_status(self):
        """
        Status should either be open or closed not "maybe"
        """
        self.assertFalse(RoommatePostForm(data=self._valid_data(status='maybe')).is_valid())



# Roommate Post Model
class RoommatePostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', password='pass')

    def test_default_status_is_open(self):
        """
        Check if status is open by default
        """
        post = RoommatePost.objects.create(user=self.user, message='Hi', date='2026-03-01')
        self.assertEqual(post.status, 'open')

    def test_rent_is_optional(self):
        """
        Rent is optional
        """
        post = RoommatePost.objects.create(user=self.user, message='Hi', date='2026-03-01')
        self.assertIsNone(post.rent)

    def test_property_type_defaults_to_empty(self):
        """
        Property type defaults to empty string
        """
        post = RoommatePost.objects.create(user=self.user, message='Hi', date='2026-03-01')
        self.assertEqual(post.property_type, '')

    def test_user_deletion_cascades(self):
        """
        Deleting user = deleting posts
        """
        RoommatePost.objects.create(user=self.user, message='Hi', date='2026-03-01')
        self.user.delete()
        self.assertEqual(RoommatePost.objects.count(), 0)



# Property Model
class PropertyModelTest(TestCase):
    def test_description_is_optional(self):
        """
        DEscription of House is optional
        """
        prop = Property.objects.create(
            title='Test', location='Denver, CO',
            listing_type='rent', property_type='house', price=900
        )
        self.assertEqual(prop.description, '')

    def test_lat_lng_nullable(self):
        """
        Langitude and latitude can be null
        """
        prop = Property.objects.create(
            title='NoCoords', location='Denver, CO',
            listing_type='rent', property_type='house', price=900
        )
        self.assertIsNone(prop.latitude)
        self.assertIsNone(prop.longitude)

    def test_str_returns_title(self):
        prop = Property.objects.create(
            title='My Place', location='Boulder, CO',
            listing_type='rent', property_type='apartment', price=1000
        )
        self.assertEqual(str(prop), 'My Place')



# Custom Register Form
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
        self.assertTrue(CustomRegisterForm(data=self._valid_data()).is_valid())

    def test_email_is_optional(self):
        """
        Email is optional
        """
        self.assertTrue(CustomRegisterForm(data=self._valid_data(email='')).is_valid())

    def test_mismatched_passwords_invalid(self):
        """
        If there's a mismatch when confirming password, the form is rejected
        """
        self.assertFalse(CustomRegisterForm(data=self._valid_data(password2='different')).is_valid())

    def test_missing_username_invalid(self):
        """
        Username is mandatory
        """
        self.assertFalse(CustomRegisterForm(data=self._valid_data(username='')).is_valid())



# Rentcast API
# Patch API_KEY so the function doesn't bail out before hitting requests.get
class RentcastAPITest(TestCase):
    @patch('home.rentcast_api.API_KEY', 'fake-key')
    @patch('home.rentcast_api.requests.get')
    def test_returns_list_on_200(self, mock_get):
        """
        API returns json/ is successful
        """
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{'formattedAddress': '123 Main St', 'price': 1200}],
            text='[...]',
        )
        from home.rentcast_api import get_properties
        result = get_properties('Denver, CO')
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    @patch('home.rentcast_api.API_KEY', 'fake-key')
    @patch('home.rentcast_api.requests.get')
    def test_returns_empty_list_on_non_200(self, mock_get):
        mock_get.return_value = MagicMock(status_code=404, text='not found')
        from home.rentcast_api import get_properties
        result = get_properties('Denver, CO')
        self.assertEqual(result, [])

    @patch('home.rentcast_api.API_KEY', None)
    def test_returns_empty_list_when_no_api_key(self):
        """
        If no API key, no list is returned
        """
        from home.rentcast_api import get_properties
        result = get_properties('Denver, CO')
        self.assertEqual(result, [])

    @patch('home.rentcast_api.API_KEY', 'fake-key')
    @patch('home.rentcast_api.requests.get')
    def test_filters_by_min_price(self, mock_get):
        """
        Testing API by min price
        """
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{'price': 900}, {'price': 1500}, {'price': 500}],
            text='[...]',
        )
        from home.rentcast_api import get_properties
        result = get_properties('Denver, CO', min_price=1000)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['price'], 1500)

    @patch('home.rentcast_api.API_KEY', 'fake-key')
    @patch('home.rentcast_api.requests.get')
    def test_filters_by_max_price(self, mock_get):
        """
        Testing API by max price
        """
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{'price': 900}, {'price': 1500}],
            text='[...]',
        )
        from home.rentcast_api import get_properties
        result = get_properties('Denver, CO', max_price=1000)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['price'], 900)

    @patch('home.rentcast_api.API_KEY', 'fake-key')
    @patch('home.rentcast_api.requests.get')
    def test_property_type_mapped_to_rentcast_value(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: [], text='[]'
        )
        from home.rentcast_api import get_properties
        get_properties('Denver, CO', property_type='apartment')
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs['params']['propertyType'], 'Apartment')

    @patch('home.rentcast_api.API_KEY', 'fake-key')
    @patch('home.rentcast_api.requests.get')
    def test_response_wrapping_in_data_key(self, mock_get):
        """API sometimes wraps results under a 'data' key."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {'data': [{'price': 1000}]},
            text='{...}',
        )
        from home.rentcast_api import get_properties
        result = get_properties('Denver, CO')
        self.assertEqual(len(result), 1)



# geocode_residential - US Census geocoding helper
class GeocodeResidentialTest(TestCase):
    @patch('home.views.requests.get')
    def test_returns_coords_on_match(self, mock_get):
        """
        Returns Lat/Long coords when there's a match
        """
        mock_get.return_value = MagicMock(
            json=lambda: {
                'result': {
                    'addressMatches': [
                        {'coordinates': {'y': 40.01, 'x': -105.27}}
                    ]
                }
            }
        )
        from home.views import geocode_residential
        lat, lng = geocode_residential('123 Main St, Boulder CO')
        self.assertAlmostEqual(lat, 40.01)
        self.assertAlmostEqual(lng, -105.27)

    @patch('home.views.requests.get')
    def test_returns_none_when_no_match(self, mock_get):
        mock_get.return_value = MagicMock(
            json=lambda: {'result': {'addressMatches': []}}
        )
        from home.views import geocode_residential
        result = geocode_residential('Completely Fake Address, XX 00000')
        self.assertIsNone(result)



# fetch_filtered_properties - wraps get_properties with price parsing
class FetchFilteredPropertiesTest(TestCase):
    @patch('home.views.get_properties', return_value=[])
    def test_returns_empty_when_api_empty(self, _):
        from home.views import fetch_filtered_properties
        self.assertEqual(fetch_filtered_properties('Boulder, CO'), [])

    @patch('home.views.get_properties', side_effect=Exception('API down'))
    def test_returns_empty_on_exception(self, _):
        from home.views import fetch_filtered_properties
        self.assertEqual(fetch_filtered_properties('Boulder, CO'), [])

    @patch('home.views.get_properties', return_value=[])
    def test_price_range_parsed_and_passed_to_api(self, mock_api):
        from home.views import fetch_filtered_properties
        fetch_filtered_properties('Boulder, CO', price_range='800-1500')
        mock_api.assert_called_once_with(
            'Boulder, CO', property_type=None, min_price=800, max_price=1500
        )

    @patch('home.views.get_properties', return_value=[])
    def test_invalid_price_range_silently_ignored(self, mock_api):
        from home.views import fetch_filtered_properties
        result = fetch_filtered_properties('Boulder, CO', price_range='bad-range')
        self.assertEqual(result, [])
        # min/max fall back to None when parsing fails
        mock_api.assert_called_once_with(
            'Boulder, CO', property_type=None, min_price=None, max_price=None
        )



# map_view - POST path (search bar on the map page itself)
class MapViewPostTest(TestCase):
    """
    How Map looks after POST
    """
    @patch('home.views.get_properties', return_value=[])
    def test_post_returns_200(self, _):
        response = self.client.post('/map/', {'city': 'Boulder', 'state': 'CO'})
        self.assertEqual(response.status_code, 200)

    @patch('home.views.get_properties')
    def test_post_with_api_results_puts_data_in_context(self, mock_api):
        mock_api.return_value = [{
            'latitude': 40.01, 'longitude': -105.27,
            'formattedAddress': '1 Test Ave, Boulder, CO',
            'propertyType': 'apartment', 'price': 1000,
            'bedrooms': 2, 'bathrooms': 1, 'squareFootage': 800,
        }]
        response = self.client.post('/map/', {'city': 'Boulder', 'state': 'CO'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.context['properties'])
        self.assertEqual(len(data), 1)
        self.assertIn('latitude', data[0])

    @patch('home.views.get_properties')
    def test_map_geocodes_when_no_lat_lng(self, mock_api):
        """When API returns a property without coords, geocode_residential is called."""
        mock_api.return_value = [{
            'formattedAddress': '1 Test Ave, Boulder, CO',
            'propertyType': 'apartment', 'price': 1000,
            # no latitude/longitude
        }]
        with patch('home.views.geocode_residential', return_value=(40.01, -105.27)):
            response = self.client.get('/map/', {'city': 'Boulder', 'state': 'CO'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.context['properties'])
        self.assertEqual(len(data), 1)


# roommate_create GET path
class RoommateCreateGetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', password='pass')
        self.client.login(username='u', password='pass')

    def test_get_create_page_returns_form(self):
        """
        Create Page returns a form
        """
        response = self.client.get('/roommate-posts/create/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)



# register — invalid form path
class RegisterErrorTest(TestCase):
    """
    Checking invalid cases while registering new users
    """
    def test_register_with_mismatched_passwords_shows_errors(self):
        response = self.client.post('/register/', {
            'username': 'u',
            'password1': 'StrongPass@123',
            'password2': 'Different@456',
        })
        #View renders homepage with errors (200) or redirects (302)
        self.assertIn(response.status_code, [200, 302])

    def test_duplicate_username_register_fails(self):
        User.objects.create_user(username='existing', password='pass')
        self.client.post('/register/', {
            'username': 'existing',
            'password1': 'StrongPass@123',
            'password2': 'StrongPass@123',
        })
        #Only one user with that name should exist
        self.assertEqual(User.objects.filter(username='existing').count(), 1)



# setup_2fa - POST paths (totp_verify, email_send, email_verify)
class TwoFAPostTest(TestCase):
    """
    Verifies QR code and Email
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username='u', password='StrongPass@99', email='u@example.com'
        )
        self.client.login(username='u', password='StrongPass@99')

    def _set_session(self, **kwargs):
        session = self.client.session
        for k, v in kwargs.items():
            session[k] = v
        session.save()

    def test_totp_verify_wrong_code_shows_error(self):
        import pyotp
        self._set_session(totp_secret=pyotp.random_base32())
        response = self.client.post('/auth/2fa/setup/', {
            'method': 'totp_verify', 'otp_code': '000000',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('totp_error', response.context)

    def test_totp_verify_correct_code_redirects(self):
        import pyotp
        secret = pyotp.random_base32()
        self._set_session(totp_secret=secret)
        valid_code = pyotp.TOTP(secret).now()
        response = self.client.post('/auth/2fa/setup/', {
            'method': 'totp_verify', 'otp_code': valid_code,
        })
        self.assertEqual(response.status_code, 302)

    @patch('django.core.mail.send_mail')
    def test_email_send_with_valid_email_sends_mail(self, mock_mail):
        response = self.client.post('/auth/2fa/setup/', {'method': 'email_send'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_mail.called)
        self.assertIn('email_sent', response.context)

    def test_email_send_without_email_shows_error(self):
        self.user.email = ''
        self.user.save()
        response = self.client.post('/auth/2fa/setup/', {'method': 'email_send'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('email_error', response.context)

    def test_email_verify_correct_code_redirects(self):
        self._set_session(email_otp='123456')
        response = self.client.post('/auth/2fa/setup/', {
            'method': 'email_verify', 'email_code': '123456',
        })
        self.assertEqual(response.status_code, 302)

    def test_email_verify_wrong_code_shows_error(self):
        self._set_session(email_otp='123456')
        response = self.client.post('/auth/2fa/setup/', {
            'method': 'email_verify', 'email_code': '999999',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('email_error', response.context)


# chat Message model
class MessageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', password='pass')

    def test_message_str(self):
        """
        Creating message
        """
        from chat.models import Message
        msg = Message.objects.create(
            posting_id=1,
            sender=self.user,
            sender_label='user',
            content='Hello there',
        )
        self.assertIn('Hello there', str(msg))

    def test_message_ordering_by_timestamp(self):
        """
        Ordering messages by their timestamp
        """
        from chat.models import Message
        m1 = Message.objects.create(posting_id=1, sender=self.user, sender_label='user', content='First')
        m2 = Message.objects.create(posting_id=1, sender=self.user, sender_label='user', content='Second')
        messages = list(Message.objects.filter(posting_id=1))
        self.assertEqual(messages[0].id, m1.id)
        self.assertEqual(messages[1].id, m2.id)

    def test_message_sender_nullable(self):
        from chat.models import Message
        msg = Message.objects.create(
            posting_id=1, sender=None, sender_label='anonymous', content='Hi'
        )
        self.assertIsNone(msg.sender)



# WebSocket consumer - connect, receive, disconnect
# Overrides CHANNEL_LAYERS to use the in-memory backend (no Redis needed)
@override_settings(CHANNEL_LAYERS={'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}})
class ChatConsumerTest(TestCase):
    """
    Checks connection and if messages can be received
    """
    def setUp(self):
        self.user = User.objects.create_user(username='wsuser', password='pass')

    def _make_app(self):
        from channels.routing import URLRouter
        from channels.auth import AuthMiddlewareStack
        import chat.routing
        return AuthMiddlewareStack(URLRouter(chat.routing.websocket_urlpatterns))

    def test_consumer_connects_and_disconnects(self):
        """
        Check Connection and Disconnection
        """
        from channels.testing import WebsocketCommunicator
        from asgiref.sync import async_to_sync

        app = self._make_app()
        user_id = self.user.id

        async def run():
            comm = WebsocketCommunicator(app, f'ws/chat/1/{user_id}/')
            comm.scope['user'] = self.user  # inject authenticated user
            connected, _ = await comm.connect()
            assert connected, "WebSocket did not connect"
            await comm.disconnect()

        async_to_sync(run)()

    def test_save_message_persists_to_db(self):
        """
        save_message() writes a Message row without needing a live WebSocket
        """
        from chat.consumers import ChatConsumer
        from chat.models import Message
        from asgiref.sync import async_to_sync

        consumer = ChatConsumer()
        consumer.posting_id = 99
        consumer.inquirer_id = self.user.id
        async_to_sync(consumer.save_message)(self.user, 'direct save')
        self.assertEqual(Message.objects.filter(posting_id=99).count(), 1)

    def test_get_history_returns_existing_messages(self):
        from chat.consumers import ChatConsumer
        from chat.models import Message
        from asgiref.sync import async_to_sync

        Message.objects.create(
            posting_id=77, inquirer_id=self.user.id, sender=self.user,
            sender_label='user', content='History msg'
        )
        consumer = ChatConsumer()
        consumer.posting_id = 77
        consumer.inquirer_id = self.user.id
        consumer.scope = {'user': self.user}  # add this
        history = async_to_sync(consumer.get_history)()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['message'], 'History msg')

    def test_consumer_serves_message_history_on_connect(self):
        """
        Messages already in DB for a posting are sent on connect
        """
        from channels.testing import WebsocketCommunicator
        from chat.models import Message
        from asgiref.sync import async_to_sync

        # Pre-seed a message
        Message.objects.create(
            posting_id=1, inquirer_id=self.user.id, sender=self.user,
            sender_label='user', content='Old message'
        )

        app = self._make_app()
        user_id = self.user.id

        async def run():
            comm = WebsocketCommunicator(app, f'ws/chat/1/{user_id}/')
            comm.scope['user'] = self.user  # inject authenticated user
            connected, _ = await comm.connect()
            assert connected, "WebSocket did not connect"
            await comm.disconnect()

        async_to_sync(run)()

    def test_anonymous_user_saved_with_none_sender(self):
        """
        save_message() stores None for anonymous users
        """
        from chat.consumers import ChatConsumer
        from chat.models import Message
        from django.contrib.auth.models import AnonymousUser
        from asgiref.sync import async_to_sync

        consumer = ChatConsumer()
        consumer.posting_id = 88
        consumer.inquirer_id = 0  # anonymous has no user id;
        anon = AnonymousUser()
        async_to_sync(consumer.save_message)(anon, 'anon message')
        msg = Message.objects.get(posting_id=88)
        self.assertIsNone(msg.sender)
        self.assertEqual(msg.sender_label, 'anonymous')