from behave import given, when, then
from django.contrib.auth.models import User
from home.models import RoommatePost, Property
from unittest.mock import patch
import json


# Registration
# Given Statement
@given('I am on the homepage')
def step_on_homepage(context):
    context.response = context.test.client.get('/')

# When Statement
@when('I submit the registration form with username "{username}" and password "{password}"')
def step_register(context, username, password):
    context.test.client.post('/register/', {
        'username': username,
        'password1': password,
        'password2': password,
    })

# When Statement
@when('I submit the registration form with mismatched passwords')
def step_register_mismatch(context):
    context.test.client.post('/register/', {
        'username': 'baduser',
        'password1': 'StrongPassword@123',
        'password2': 'DifferentPassword@123',
    })
# Then Statement
@then('a user with username "{username}" exists in the database')
def step_user_exists(context, username):
    assert User.objects.filter(username=username).exists()

# Then Statement
@then('no new user is created')
def step_no_user_created(context):
    assert not User.objects.filter(username='baduser').exists()



# Shared auth helpers
# Given Statement
@given('a user "{username}" exists and is logged in')
def step_user_logged_in(context, username):
    user, _ = User.objects.get_or_create(username=username)
    user.set_password('Password123!')
    user.save()
    context.user = user
    context.test.client.login(username=username, password='Password123!')

# Given Statement
@given('a logged-in user "{username}" with email "{email}"')
def step_user_with_email_logged_in(context, username, email):
    user, _ = User.objects.get_or_create(username=username)
    user.set_password('Password123!')
    user.email = email
    user.save()
    context.user = user
    context.test.client.login(username=username, password='Password123!')

# Given Statement
@given('user "{username}" is logged in')
def step_other_user_logged_in(context, username):
    user, _ = User.objects.get_or_create(username=username)
    user.set_password('Password123!')
    user.save()
    context.test.client.login(username=username, password='Password123!')

# Given Statement
@given('the user logs out')
def step_user_logs_out(context):
    context.test.client.logout()



# Roommate Postings
# Given Statement
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
# When Statement
@when('I submit a roommate post with message "{message}"')
def step_create_post(context, message):
    context.test.client.post('/roommate-posts/create/', {
        'message': message,
        'date': '2026-03-11',
        'status': 'open',
        'rent': 1000,
        'property_type': 'apartment',
    })

# When Statement
@when('I close the post')
def step_close_post(context):
    context.test.client.post(f'/roommate-posts/{context.post.id}/close/')

# When Statement
@when('I delete the post')
def step_delete_post(context):
    context.test.client.post(f'/roommate-posts/{context.post.id}/delete/')

# When Statement
@when('"{username}" tries to delete the post')
def step_other_delete_post(context, username):
    context.test.client.post(f'/roommate-posts/{context.post.id}/delete/')

# Then Statement
@then('the post "{message}" appears on the listings page')
def step_post_in_listings(context, message):
    response = context.test.client.get('/roommate-posts/')
    assert message in response.content.decode()

# Then Statement
@then('the post status is "{status}"')
def step_post_status(context, status):
    context.post.refresh_from_db()
    assert context.post.status == status

# Then Statement
@then('the post no longer exists in the database')
def step_post_deleted(context):
    assert not RoommatePost.objects.filter(id=context.post.id).exists()

# Then Statement
@then('the post still exists in the database')
def step_post_still_exists(context):
    assert RoommatePost.objects.filter(id=context.post.id).exists()



# Property Map Search (replacing old property-filter steps)
# Given Statement
@given('the Rentcast API returns a property at "{address}"')
def step_api_returns_property(context, address):
    context.mock_api_result = [{
        'formattedAddress': address,
        'latitude': 40.01,
        'longitude': -105.27,
        'propertyType': 'Apartment',
        'price': 1200,
    }]

# When Statement
@when('I visit the map page')
def step_visit_map(context):
    context.response = context.test.client.get('/map/')

# When Statement
@when('I search the map with city "{city}" and state "{state}"')
def step_search_map_city_state(context, city, state):
    api_result = getattr(context, 'mock_api_result', [])
    with patch('home.views.get_properties', return_value=api_result):
        context.response = context.test.client.get(
            '/map/', {'city': city, 'state': state}
        )

# When Statement
@when('I search the map with city "{city}" and no state')
def step_search_map_city_only(context, city):
    with patch('home.views.get_properties', return_value=[]):
        context.response = context.test.client.get('/map/', {'city': city})

# When Statement
@when('I search the map with city "{city}" state "{state}" and budget "{budget}"')
def step_search_map_with_budget(context, city, state, budget):
    api_result = getattr(context, 'mock_api_result', [])
    with patch('home.views.get_properties', return_value=api_result):
        context.response = context.test.client.get(
            '/map/', {'city': city, 'state': state, 'budget': budget}
        )

# Then Statement
@then('the map page returns 200')
def step_map_200(context):
    assert context.response.status_code == 200, (
        f"Expected 200, got {context.response.status_code}"
    )

# Then Statement
@then('the map context has at least 1 property')
def step_map_has_properties(context):
    data = json.loads(context.response.context['properties'])
    assert len(data) >= 1, f"Expected >= 1 property, got {len(data)}"

# Then Statement
@then('the map context has 0 properties')
def step_map_has_no_properties(context):
    data = json.loads(context.response.context['properties'])
    assert len(data) == 0, f"Expected 0 properties, got {len(data)}"



# Keyword Search
# Given Statement
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

# When Statement
@when('I search by keyword "{keyword}"')
def step_search_keyword(context, keyword):
    context.response = context.test.client.get(
        '/roommate-posts/search/', {'q': keyword}
    )

# When Statement
@when('I visit the search page with no keyword')
def step_visit_search_no_keyword(context):
    context.response = context.test.client.get('/roommate-posts/search/')

# Then Statement
@then('the search page returns 200')
def step_search_200(context):
    assert context.response.status_code == 200, (
        f"Expected 200, got {context.response.status_code}"
    )

# Then Statement
@then('I see "{text}" in the results')
def step_see_in_results(context, text):
    assert text in context.response.content.decode(), \
        f'Expected "{text}" in response but not found'

# Then Statement
@then('I do not see "{text}" in the results')
def step_not_see_in_results(context, text):
    assert text not in context.response.content.decode(), \
        f'Expected "{text}" NOT in response but it was found'



# Instant Messaging
# Given Statement
@given('a message "{content}" is sent on the posting')
def step_message_sent(context, content):
    from chat.models import Message
    sender = getattr(context, 'user', None)
    Message.objects.create(
        posting_id=context.post.id,
        inquirer_id=sender.id if sender else None,
        sender=sender,
        sender_label=sender.username if sender else 'anonymous',
        content=content,
    )

# When Statement
@when('I visit the chat inbox')
def step_visit_inbox(context):
    context.response = context.test.client.get('/chat/inbox/')

# When Statement
@when('I open the chat room for the posting')
def step_open_chat_room(context):
    user = getattr(context, 'user', None)
    user_id = user.id if user else 0
    context.response = context.test.client.get(f'/chat/{context.post.id}/{user_id}/')

# Then Statement
@then('the inbox returns 200')
def step_inbox_200(context):
    assert context.response.status_code == 200, (
        f"Expected 200, got {context.response.status_code}"
    )

# Then Statement
@then('the chat room returns 200')
def step_chat_room_200(context):
    assert context.response.status_code == 200, (
        f"Expected 200, got {context.response.status_code}"
    )

# Then Statement
@then('I am redirected away from the page')
def step_redirected(context):
    assert context.response.status_code != 200, (
        f"Expected redirect, got {context.response.status_code}"
    )

# Then Statement
@then('the inbox shows {count:d} message for that post')
def step_inbox_message_count(context, count):
    posts_with_chats = context.response.context['posts_with_chats']
    assert len(posts_with_chats) > 0, "No posts in inbox"
    actual = posts_with_chats[0]['message_count']
    assert actual == count, f"Expected {count} messages, got {actual}"



# Two-Factor Authentication
# When Statement
@when('I visit the 2FA setup page')
def step_visit_2fa(context):
    context.response = context.test.client.get('/auth/2fa/setup/')
# Then Statement
@then('the setup page returns 200')
def step_2fa_200(context):
    assert context.response.status_code == 200, (
        f"Expected 200, got {context.response.status_code}"
    )
# Then Statement
@then('the response context contains a non-empty "{key}"')
def step_context_has_key(context, key):
    value = context.response.context.get(key)
    assert value, f'Expected non-empty "{key}" in context, got: {value}'

# When Statement
@when('I submit a wrong TOTP code on the setup page')
def step_submit_wrong_totp(context):
    import pyotp
    secret = pyotp.random_base32()
    session = context.test.client.session
    session['totp_secret'] = secret
    session.save()
    context.response = context.test.client.post('/auth/2fa/setup/', {
        'method': 'totp_verify',
        'otp_code': '000000',
    })

# Then Statement
@then('the setup page shows a TOTP error')
def step_totp_error_shown(context):
    assert context.response.status_code == 200
    assert 'totp_error' in context.response.context, \
        "Expected totp_error in context"

# When Statement
@when('I request an email verification code')
def step_request_email_code(context):
    with patch('django.core.mail.send_mail'):
        context.response = context.test.client.post(
            '/auth/2fa/setup/', {'method': 'email_send'}
        )

# Then Statement
@then('the setup page confirms the email was sent')
def step_email_sent_confirmed(context):
    assert context.response.status_code == 200
    assert context.response.context.get('email_sent'), \
        "Expected email_sent to be truthy in context"



# Property Map — extra steps
# When Statement
@when('I search the map with city "{city}" state "{state}" and type "{ptype}"')
def step_search_map_with_type(context, city, state, ptype):
    api_result = getattr(context, 'mock_api_result', [])
    with patch('home.views.get_properties', return_value=api_result):
        context.response = context.test.client.get(
            '/map/', {'city': city, 'state': state, 'type': ptype}
        )
# Given Statement
@given('a local property with coordinates exists')
def step_local_property_with_coords(context):
    from home.models import Property
    Property.objects.create(
        title='Local Prop', location='Boulder, CO',
        listing_type='rent', property_type='apartment', price=1000,
        latitude=40.01, longitude=-105.27,
    )
# Then Statement
@then('every property in the map context has coordinates')
def step_all_have_coords(context):
    import json
    data = json.loads(context.response.context['properties'])
    assert len(data) > 0, "No properties in map context"
    for prop in data:
        assert 'latitude' in prop, f"Missing latitude: {prop}"
        assert 'longitude' in prop, f"Missing longitude: {prop}"