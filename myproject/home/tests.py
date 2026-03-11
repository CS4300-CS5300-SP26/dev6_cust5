from django.test import TestCase
from django.contrib.auth.models import User

class RegisterTest(TestCase):
    def test_register_page_success(self):
        response = self.client.get('/register/')
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
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_valid_login_redirect(self):
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'StrongPassword@123',
        })
        self.assertEqual(response.status_code, 302)



class RoommatePostingTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='poster', password='Password123!')
        self.client.login(username='poster', password='Password123!')

    def test_roommate_list_returns_200(self):
        response = self.client.get('/roommates/')
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_cannot_post(self):
        self.client.logout()
        response = self.client.get('/roommates/post/')
        self.assertNotEqual(response.status_code, 200) 

    def test_create_post_saves_to_database(self):
        from home.models import RoommatePosting
        self.client.post('/roommates/post/', {
        'message': 'Looking for a roommate near campus.',
        'date_posted': '2026-03-11',
        'status': 'open'
    })
        self.assertEqual(RoommatePosting.objects.count(), 1)