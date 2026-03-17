from behave import given, when, then
from django.contrib.auth.models import User
from home.models import RoommatePost, Property
from unittest.mock import patch


# ── Registration steps ────────────────────────────────────────────────────────

@given('I am on the homepage')
def step_on_homepage(context):
    context.response = context.test.client.get('/')

@when('I submit the registration form with username "{username}" and password "{password}"')
def step_register(context, username, password):
    context.test.client.post('/register/', {
        'username': username,
        'password1': password,
        'password2': password,
    })

@when('I submit the registration form with mismatched passwords')
def step_register_mismatch(context):
    context.test.client.post('/register/', {
        'username': 'baduser',
        'password1': 'StrongPassword@123',
        'password2': 'DifferentPassword@123',
    })

@then('a user with username "{username}" exists in the database')
def step_user_exists(context, username):
    assert User.objects.filter(username=username).exists()

@then('no new user is created')
def step_no_user_created(context):
    assert not User.objects.filter(username='baduser').exists()


# ── Roommate posting steps ────────────────────────────────────────────────────

@given('a user "{username}" exists and is logged in')
def step_user_logged_in(context, username):
    user, _ = User.objects.get_or_create(username=username)
    user.set_password('Password123!')
    user.save()
    context.user = user
    context.test.client.login(username=username, password='Password123!')

@given('user "{username}" is logged in')
def step_other_user_logged_in(context, username):
    user, _ = User.objects.get_or_create(username=username)
    user.set_password('Password123!')
    user.save()
    context.test.client.login(username=username, password='Password123!')

@given('a roommate post exists for "{username}"')
def step_post_exists(context, username):
    user = User.objects.get(username=username)
    context.post = RoommatePost.objects.create(
        user=user,
        message='Test post message',
        date='2026-03-11',
        status='open',
        rent=1000,
        property_type='apartment',
    )

@when('I submit a roommate post with message "{message}"')
def step_create_post(context, message):
    context.test.client.post('/roommate-posts/create/', {
        'message': message,
        'date': '2026-03-11',
        'status': 'open',
        'rent': 1000,
        'property_type': 'apartment',
    })

@when('I close the post')
def step_close_post(context):
    context.test.client.post(f'/roommate-posts/{context.post.id}/close/')

@when('I delete the post')
def step_delete_post(context):
    context.test.client.post(f'/roommate-posts/{context.post.id}/delete/')

@when('"{username}" tries to delete the post')
def step_other_delete_post(context, username):
    context.test.client.post(f'/roommate-posts/{context.post.id}/delete/')

@then('the post "{message}" appears on the listings page')
def step_post_in_listings(context, message):
    response = context.test.client.get('/roommate-posts/')
    assert message in response.content.decode()

@then('the post status is "{status}"')
def step_post_status(context, status):
    context.post.refresh_from_db()
    assert context.post.status == status

@then('the post no longer exists in the database')
def step_post_deleted(context):
    assert not RoommatePost.objects.filter(id=context.post.id).exists()

@then('the post still exists in the database')
def step_post_still_exists(context):
    assert RoommatePost.objects.filter(id=context.post.id).exists()


# ── Property search steps ─────────────────────────────────────────────────────

@given('the following properties exist:')
def step_properties_exist(context):
    for row in context.table:
        Property.objects.create(
            title=row['title'],
            price=int(row['price']),
            property_type=row['type'],
            listing_type='rent',
            location=row['location'],
        )

@when('I search for "{location}"')
def step_search_location(context, location):
    with patch('home.views.get_properties', return_value=[]):
        context.response = context.test.client.get('/', {'location': location})

@when('I search by type "{ptype}" in "{location}"')
def step_search_location_type(context, ptype, location):
    with patch('home.views.get_properties', return_value=[]):
        context.response = context.test.client.get('/', {
            'location': location, 'type': ptype
        })

@when('I search by budget "{budget}" in "{location}"')
def step_search_location_budget(context, budget, location):
    with patch('home.views.get_properties', return_value=[]):
        context.response = context.test.client.get('/', {
            'location': location, 'budget': budget
        })

@then('I see "{text}" in the results')
def step_see_in_results(context, text):
    assert text in context.response.content.decode(), \
        f'Expected "{text}" in response but not found'

@then('I do not see "{text}" in the results')
def step_not_see_in_results(context, text):
    assert text not in context.response.content.decode(), \
        f'Expected "{text}" to not be in response but it was found'