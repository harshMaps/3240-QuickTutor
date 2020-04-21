from django.test import TestCase, Client
from .models import *
import datetime
from django.utils import timezone
from io import BytesIO
import re

'''
NOTES | from https://docs.djangoproject.com/en/3.0/topics/testing/tools/

- Use test client to simulate GET and POST requests
- Test client does not need server to be running
- When retrieving pages, remember to specify path (relative) of URL, not the whole domain
- Make a class to group similar tests
- EVERY TEST METHOD MUST START WITH THE WORD 'test'

setUp()
- called before every test function to set up any objects that may be modified by the test

setUpTestData()
- called once at beginning of the test run for class-level setup to create objects that aren't going to be modified

GET requests
- client.get(path, data=None, follow=False)
- data is in form of dictionary
- returns a Response object
- if you set follow to true, it will follow any redirects

**POST requests are pretty much the same. client.post

Response objects
- response.status_code returns the HTTP status of the response
- response.templates returns list of Template instances used to render the final content


'''


# Testing login process
class LoginTestCases(TestCase):
	# Create a user before tests
	def setUp(self):
		User.objects.create_user('mamba@gmail.com', 'CS3240!!')

	def test_login(self):
		client = Client()

		# Test that login is successful
		self.assertTrue(client.login(username='mamba@gmail.com', password='CS3240!!'), 'Login unsuccessful.')



# Testing login process Boundary Case (Testing Capitalization in password.)
class LoginTestCasesboundary(TestCase):
	# Create a user before tests
	def setUp(self):
		User.objects.create_user('mamba@gmail.com', 'CS3240!!')

	def test_login_wrong_password(self):
		client = Client()

		# Test that login is unsuccessful
		self.assertFalse(client.login(username='mamba@gmail.com', password='cs3240!!'), 'Login unsuccessful.')


# Testing login process (Capitalization in Username)
class LoginTestCasesCapitalization(TestCase):
	# Create a user before tests
	def setUp(self):
		User.objects.create_user('mamba@gmail.com', 'CS3240!!')

	def test_login_wrong_username(self):
		client = Client()

		# Test that login is unsuccessful
		self.assertFalse(client.login(username='MAMBA@gmail.com', password='cs3240!!'), 'Login unsuccessful.')


# Testing navigation around website
class NavigationTestCases(TestCase):
	# Create a user before tests
	def setUp(self):
		User.objects.create_user('mamba@gmail.com', 'CS3240!!')

	def test_navigation_before_login(self):
		client = Client()

		# Test that before logging in, accessing any URL brings them to index.html (the login page)
		urls = ['/', '/feed/', '/myRequest/', '/profile/', '/contacts/', '/messages/']
		for url in urls:
			response = client.get(url, follow=True)
			self.assertEqual(response.templates[0].name, 'app/index.html', 'User was able to access restricted page without logging in.')

	def test_navigation_after_login(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Accessing base URL redirects them to feed page
		response = client.get('/', follow=True)
		self.assertEqual(response.templates[0].name, 'app/feed.html', 'Base URL did not redirect to feed page.')

		# Accessing any other URL brings them to corresponding page
		urls = ['/', '/feed/', '/myRequest/', '/profile/', '/contacts/', '/messages/']
		page_names = ['', 'feed', 'myRequest', 'profile', 'contacts', 'messages']  # no slashes for concatenation purposes

		for i in range(1, len(urls)):  # don't want to include the base URL... so start index at 1
			response = client.get(urls[i], follow=True)
			name = 'app/' + page_names[i] + '.html'
			self.assertEqual(response.templates[0].name, name, 'Could not access ' + page_names[i] + ' page.')


class RequestTestCases(TestCase):
	# Create users before tests and post requests
	def setUp(self):
		# Create user
		User.objects.create_user('mamba@gmail.com', 'CS3240!!')
		User.objects.create_user('mamba@yahoo.com', 'password')
		User.objects.create_user('mamba_blankfield@yahoo.com', 'password')

		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to myRequest page to create a new request
		client.post('/myRequest/', {'action': 'Submit', 'title': 'Help me!', 'location': 'Clark',
											   'description': 'I really need help. $5'}, follow=True)

		# Login as other user and create second request
		client.login(username='mamba@yahoo.com', password='password')
		client.post('/myRequest/', {'action': 'Submit', 'title': 'Help me 2!', 'location': 'Clem',
									'description': 'I really need help. $10'}, follow=True)


		client.login(username='mamba_blankfield@yahoo.com', password='password')
		client.post('/myRequest/', {'action': 'Submit', 'title': '', 'location': 'Clark',
											   'description': ''}, follow=True)



	# Check that user's boolean is set when they create a request
	def test_has_active_request(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		user = User.objects.get(email='mamba@gmail.com')
		self.assertTrue(user.has_active_request, 'has_active_request boolean was not set.')

	# Check that user's boolean is set when they create a request / making sure user boolean is still avaliable even if a field is blank.
	def test_has_active_request_blankfield(self):
		# Create client and login
		client = Client()
		client.login(username='mamba_blankfield@yahoo.com', password='password')

		user = User.objects.get(email='mamba_blankfield@yahoo.com')
		self.assertTrue(user.has_active_request, 'has_active_request boolean was not set.')

	# Check that user's created request is displayed on myRequest page, with the correct information
	def test_request_creation_blankfield(self):
		# Create client and login
		client = Client()
		client.login(username='mamba_blankfield@yahoo.com', password='password')

		# Send GET request to myRequest page to view your already made request
		response = client.get('/myRequest/', follow=True)
		request = response.context['request']

		# Make sure data matches
		self.assertIsNotNone(request.title, 'empty string  DNE.')
		self.assertEqual(request.location, 'Clark', 'Location does not match.')
		self.assertIsNotNone(request.description, 'Description does not match.')

	# Check that user's created request is displayed on myRequest page, with the correct information
	def test_request_creation(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send GET request to myRequest page to view your already made request
		response = client.get('/myRequest/', follow=True)
		request = response.context['request']

		# Make sure data matches
		self.assertEqual(request.title, 'Help me!', 'Title does not match.')
		self.assertEqual(request.location, 'Clark', 'Location does not match.')
		self.assertEqual(request.description, 'I really need help. $5', 'Description does not match.')

	# Check that a user can't create two requests via two POST requests
	def test_second_request(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		client.post('/myRequest/', {'action': 'Submit', 'title': 'Help', 'location': 'Clem',
									'description': 'Please.'}, follow=True)

		# Get user
		user = User.objects.get(email='mamba@gmail.com')

		# See if the second request was created
		request_search = Request.objects.filter(user=user.email)

		# Should be of length 1
		self.assertEqual(len(request_search), 1, 'User has two active requests.')

	# When user deletes request, their boolean should be set back to false, and the Request.objects list should
	# no longer contain the request
	def test_delete_request(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to myRequest page to delete request
		client.post('/myRequest/', {'action': 'Delete'})

		# Get user
		user = User.objects.get(email='mamba@gmail.com')

		# See if their request still exists - should return set of length 0
		request_search = Request.objects.filter(user=user.email)

		self.assertEqual(len(request_search), 0, 'Deletion failed; user still has active request.')
		self.assertFalse(user.has_active_request, 'has_active_request boolean was not set to false.')

	# When a user edits a request, make sure that they are taken to request editor with their own request info
	# filled in
	def test_request_editor_rendered(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to myRequest page to edit request
		response = client.post('/myRequest/', {'action': 'Edit'}, follow=True)

		# Context should be filled with the user's request data
		title = response.context['title']
		location = response.context['location']
		description = response.context['description']

		self.assertEqual(title, 'Help me!', 'Title does not match.')
		self.assertEqual(location, 'Clark', 'Location does not match.')
		self.assertEqual(description, 'I really need help. $5', 'Description does not match.')

		# Should have rendered the request editor template 'app/requestEditor.html'
		template = response.templates[0].name
		self.assertEqual(template, 'app/requestEditor.html', 'Request editor template was not rendered.')



	# When a user updates a request with new information via the request editor page, check that the request
	# is actually updated with the new data.
	def test_request_update(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to myRequest page to edit request
		client.post('/myRequest/', {'action': 'Edit'}, follow=True)

		# Send POST request to myRequest page to update the request
		client.post('/myRequest/', {'action': 'Update', 'title': 'New title!', 'location': 'New location!',
											   'description': 'New description!'}, follow=True)

		# Get user
		user = User.objects.get(email='mamba@gmail.com')

		# See if their request has been updated with the new info
		request = Request.objects.filter(user=user.email)[0]
		self.assertEqual('New title!', request.title, 'Title does not match.')
		self.assertEqual('New location!', request.location, 'Location does not match.')
		self.assertEqual('New description!', request.description, 'Description does not match.')

	# Make sure that when two different users create requests, accessing myRequest page displays correct one.
	def test_multiple_users_and_requests(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Login as other user and create second request
		client.login(username='mamba@yahoo.com', password='password')

		# Check myRequest page for the correct request
		response = client.get('/myRequest/')
		request = response.context['request']

		self.assertEqual('Help me 2!', request.title, 'Title does not match.')
		self.assertEqual('Clem', request.location, 'Location does not match.')
		self.assertEqual('I really need help. $10', request.description, 'Description does not match.')

		# Login as first user and check myRequest page for their request
		client.login(username='mamba@gmail.com', password='CS3240!!')
		response = client.get('/myRequest/')
		request = response.context['request']

		self.assertEqual('Help me!', request.title, 'Title does not match.')
		self.assertEqual('Clark', request.location, 'Location does not match.')
		self.assertEqual('I really need help. $5', request.description, 'Description does not match.')

	# Make sure printed timestamps are correct
	def test_timestamp_request(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Get user
		user = User.objects.get(email='mamba@gmail.com')

		# Get request
		request = Request.objects.filter(user=user.email)[0]

		# ***Testing "Just now"
		# Send GET request to see what timestamp is printed
		response = client.get('/myRequest/')
		timestamp = response.context['time_since_request']

		# Should be 'Just now'
		self.assertEqual(timestamp, 'Just now', 'Timestamp did not say "Just now"')

		# ***Testing "59 minutes ago"
		# Change pub_date to 59 minutes ago
		new_pub_date = timezone.now() - datetime.timedelta(minutes=59)
		request.pub_date = new_pub_date
		request.save()

		# Send GET request to see what timestamp is printed
		response = client.get('/myRequest/')
		timestamp = response.context['time_since_request']

		# Should be '59 minutes ago'
		self.assertEqual(timestamp, '59 minutes ago', 'Timestamp did not say "59 minutes ago"')

		# ***Testing "1 hour ago"
		# Change pub_date to one hour ago
		new_pub_date = timezone.now() - datetime.timedelta(hours=1)
		request.pub_date = new_pub_date
		request.save()

		# Send GET request to see what timestamp is printed
		response = client.get('/myRequest/')
		timestamp = response.context['time_since_request']

		# Should be '1 hour ago'
		self.assertEqual(timestamp, '1 hour ago', 'Timestamp did not say "1 hour ago"')

		# ***Testing "23 hours ago"
		# Change pub_date to 23 hours ago
		new_pub_date = timezone.now() - datetime.timedelta(hours=23)
		request.pub_date = new_pub_date
		request.save()

		# Send GET request to see what timestamp is printed
		response = client.get('/myRequest/')
		timestamp = response.context['time_since_request']

		# Should be '23 hours ago'
		self.assertEqual(timestamp, '23 hours ago', 'Timestamp did not say "23 hours ago"')

		# ***Testing "1 day ago"
		# Change pub_date to one day ago
		new_pub_date = timezone.now() - datetime.timedelta(days=1)
		request.pub_date = new_pub_date
		request.save()

		# Send GET request to see what timestamp is printed
		response = client.get('/myRequest/')
		timestamp = response.context['time_since_request']

		# Should be '1 day ago'
		self.assertEqual(timestamp, '1 day ago', 'Timestamp did not say "1 day ago"')

		# ***Testing "7 days ago"
		# Change pub_date to seven days ago
		new_pub_date = timezone.now() - datetime.timedelta(days=7)
		request.pub_date = new_pub_date
		request.save()

		# Send GET request to see what timestamp is printed
		response = client.get('/myRequest/')
		timestamp = response.context['time_since_request']

		# Should be '7 days ago'
		self.assertEqual(timestamp, '7 days ago', 'Timestamp did not say "7 days ago"')

	# Test that when a user offers help on a request, the tutee can see their email on the myRequest page
	def test_offer_help_request(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to feed page to offer help
		client.post('/feed/', {'action': 'Offer Help', 'tutee': 'mamba@yahoo.com'})

		# Login as mamba@yahoo.com
		client.login(username='mamba@yahoo.com', password='password')

		# Send GET request to myRequest page to check tutor list
		response = client.get('/myRequest/')

		# Test that mamba@gmail.com appears in tutor list
		self.assertContains(response, '<li>mamba@gmail.com', count=1)

	# Test that when a user revokes their offer on a request, the tutee can no longer see their email on the myRequest page
	def test_revoke_offer_request(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to feed page to offer help
		client.post('/feed/', {'action': 'Offer Help', 'tutee': 'mamba@yahoo.com'})

		# Send POST request to feed page to revoke offer
		client.post('/feed/', {'action': 'Revoke Offer', 'tutee': 'mamba@yahoo.com'})

		# Login as mamba@yahoo.com
		client.login(username='mamba@yahoo.com', password='password')

		# Send GET request to myRequest page to check tutor list
		response = client.get('/myRequest/')

		# Test that mamba@gmail.com does NOT appear in tutor list
		self.assertNotContains(response, '<li>mamba@gmail.com')


	# Test that when a user tries to view a tutor's profile (from myRequest page), they are directed to their profile page
	def test_view_profile_request(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to feed page to offer help
		client.post('/feed/', {'action': 'Offer Help', 'tutee': 'mamba@yahoo.com'})

		# Login as other user
		client.login(username='mamba@yahoo.com', password='password')

		# Send POST request to view profile
		response = client.post('/myRequest/', {'action': 'View Profile', 'tutor': 'mamba@gmail.com'})

		# Test that the proper profile page is displayed
		self.assertContains(response, 'mamba@gmail.com')

		# Make sure update profile is not displayed
		self.assertNotContains(response, 'Update Profile')

	# Test that when a user accepts a tutor's help, the request is deleted, they are redirected to messages, and the user
	# is added as a contact
	def test_accept_and_delete(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to feed page to offer help
		client.post('/feed/', {'action': 'Offer Help', 'tutee': 'mamba@yahoo.com'})

		# Login as other user
		client.login(username='mamba@yahoo.com', password='password')

		# Send POST request to accept and delete
		response = client.post('/myRequest/', {'action': 'Accept and Delete', 'tutor': 'mamba@gmail.com'})

		# Test that the request was deleted
		request = Request.objects.filter(user='mamba@yahoo.com')
		self.assertEqual(len(request), 0, "A request in this user's name still exists, and should not.")

		# Test that the user's boolean was properly set
		tutee = User.objects.get(email='mamba@yahoo.com')
		self.assertFalse(tutee.has_active_request, 'User has_active_request was not properly set to false.')

		# Test that the tutee can now review this tutor
		self.assertTrue(tutee.reviewable_user == 'mamba@gmail.com', 'Tutee cannot review tutor.')

		# Test that the tutor can now review this tutee
		tutor = User.objects.get(email='mamba@gmail.com')
		self.assertTrue(tutor.reviewable_user == 'mamba@yahoo.com', 'Tutor cannot review tutee.')

		# Test that both users were added to each other's contacts
		self.assertTrue(tutee in tutor.contacts.all(), 'Tutee was not properly added to the tutor contacts.')
		self.assertTrue(tutor in tutee.contacts.all(), 'Tutor was not properly added to the tutee contacts.')

		# Test that a conversation object was created with these users as participants
		participants = Conversation.objects.all()[0].participants
		self.assertTrue(tutor in participants.all(), 'Tutor not in the conversation object participants.')
		self.assertTrue(tutee in participants.all(), 'Tutee not in the conversation object participants.')

		# Test that the messages page was rendered
		self.assertEquals(response.templates[0].name, 'app/messages.html', 'User was not redirected to messages page.')


class FeedTestCases(TestCase):
	# Create users before tests and post some requests
	def setUp(self):
		# Create users
		User.objects.create_user('mamba@gmail.com', 'CS3240!!')
		User.objects.create_user('mamba@yahoo.com', 'password')
		User.objects.create_user('sean@gmail.com', 'sean')

		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to myRequest page to create a new request
		client.post('/myRequest/', {'action': 'Submit', 'title': 'Help me!', 'location': 'Clark',
									'description': 'I really need help. $5'}, follow=True)

		# Login as next user and create a new request
		client.login(username='mamba@yahoo.com', password='password')
		client.post('/myRequest/', {'action': 'Submit', 'title': 'Math help', 'location': 'Clem',
									'description': 'Integrals'}, follow=True)

		# Login as next user and create a new request
		client.login(username='sean@gmail.com', password='sean')
		client.post('/myRequest/', {'action': 'Submit', 'title': 'Science help', 'location': 'Alderman',
									'description': 'Acids and bases'}, follow=True)

	# Test that if no requests have been posted, the proper message is displayed.
	def test_no_requests_on_feed(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Delete all requests
		Request.objects.all().delete()

		# Send GET request to feed page
		response = client.get('/feed/')

		# Test that the message appears on the page
		message = 'No requests found.'
		self.assertContains(response, message, count=1)

	# Test that the requests are both listed in the correct order and with the proper timestamps
	def test_timestamps_feed(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Set mamba@gmail.com request's pub_date to 2 days ago
		user = User.objects.get(email='mamba@gmail.com')
		request = Request.objects.filter(user=user.email)[0]
		new_pub_date = timezone.now() - datetime.timedelta(days=2)
		request.pub_date = new_pub_date
		request.save()

		# Set mamba@yahoo.com request's pub_date to an hour and a half ago
		user = User.objects.get(email='mamba@yahoo.com')
		request = Request.objects.filter(user=user.email)[0]
		new_pub_date = timezone.now() - datetime.timedelta(minutes=30, hours=1)
		request.pub_date = new_pub_date
		request.save()

		# Set sean@gmail.com request's pub_date to just now
		user = User.objects.get(email='sean@gmail.com')
		request = Request.objects.filter(user=user.email)[0]
		new_pub_date = timezone.now()
		request.pub_date = new_pub_date
		request.save()

		# Send GET request to feed view
		response = client.get('/feed/')

		# Check that the requests_list is in order of pub_date
		requests_list = response.context['requests_list']
		pub_dates = []
		for item in requests_list:
			pub_dates.append(item.pub_date)

		# Iterate through pub_dates and make sure each datetime is greater than the next
		for i in range(0, len(pub_dates) - 1):
			self.assertTrue(pub_dates[i] > pub_dates[i+1], 'Feed was not printed in chronological order.')

		# Iterate through the requests_list and make sure the order of usernames is correct
		self.assertEqual(requests_list[0].user, 'sean@gmail.com', "First request should be sean@gmail.com's.")
		self.assertEqual(requests_list[1].user, 'mamba@yahoo.com', "Second request should be mamba@yahoo.com's.")
		self.assertEqual(requests_list[2].user, 'mamba@gmail.com', "Third request should be mamba@gmail.com's.")

		# Get the HTML rendered by template
		content = str(response.content)

		# Use regex to find the timestamps in order of appearance, and place them all in a list
		timestamps = re.findall('id="timestamp">[\w\s]*', content)

		# Chop off the leading HTML
		for i in range(0, len(timestamps)):
			timestamps[i] = timestamps[i][15:]

		# List should now read ['Just now', '1 hour ago', '2 days ago']
		self.assertEqual(timestamps[0], 'Just now', 'First timestamp should read "Just now".')
		self.assertEqual(timestamps[1], '1 hour ago', 'Second timestamp should read "1 hour ago".')
		self.assertEqual(timestamps[2], '2 days ago', 'Third timestamp should read "2 days ago".')

	# Test that when a user offers help on a request, they are added to that request's tutor list
	def test_offer_help_feed(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to feed page to offer help
		client.post('/feed/', {'action': 'Offer Help', 'tutee': 'sean@gmail.com'})

		# Test that mamba@gmail.com appears in tutor list
		request = Request.objects.filter(user='sean@gmail.com')[0]
		tutor = request.tutors.all()[0].email
		self.assertEqual(tutor, 'mamba@gmail.com', 'Tutor was not added to tutor list when Offer Help was pressed.')

		# Login as a different client and offer help
		client.login(username='mamba@yahoo.com', password='password')

		# Send POST request to feed page to offer help
		client.post('/feed/', {'action': 'Offer Help', 'tutee': 'sean@gmail.com'})

		# Make sure that two tutors are on the list
		tutors = request.tutors.all()
		self.assertEqual(2, len(tutors), "There should be two tutors on the request's tutor list.")

		# Make sure that second tutor is mamba@yahoo.com
		self.assertEqual('mamba@yahoo.com', tutors[1].email, "Second tutor was improperly added to request's tutor list.")

	# Test that when a user revokes help on a request, they are removed from that request's tutor list
	def test_revoke_offer_feed(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to feed page to offer help
		client.post('/feed/', {'action': 'Offer Help', 'tutee': 'sean@gmail.com'})

		# Test that mamba@gmail.com appears in tutor list
		request = Request.objects.filter(user='sean@gmail.com')[0]
		tutor = request.tutors.all()[0].email
		self.assertEqual(tutor, 'mamba@gmail.com', 'Tutor was not added to tutor list when Offer Help was pressed.')

		# Send POST request to feed page to revoke offer
		client.post('/feed/', {'action': 'Revoke Offer', 'tutee': 'sean@gmail.com'})

		# Test that mamba@gmail.com no longer appears in tutor list
		tutors = request.tutors.all()
		self.assertEqual(0, len(tutors), 'Tutor was not removed from the tutor list.')

	# Test that when a user tries to view a tutee's profile (from feed page), they are directed to their profile page
	def test_view_profile_feed(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to view profile
		response = client.post('/feed/', {'action': 'View Profile', 'tutee': 'mamba@yahoo.com'})

		# Test that the proper profile page is displayed
		self.assertContains(response, 'mamba@yahoo.com')

		# Make sure update profile is not displayed
		self.assertNotContains(response, 'Update Profile')


class ProfileTestCases(TestCase):
	def setUp(self):
		# Create users
		User.objects.create_user('mamba@gmail.com', 'CS3240!!')
		User.objects.create_user('mamba@yahoo.com', 'password')
		User.objects.create_user('sean@gmail.com', 'sean')

	# Test that the user's profile page is properly rendered.
	def test_profile_rendered(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send GET request to view profile page
		response = client.get('/profile/')

		# Test that the correct profile page was fetched, as well as the ability to update it
		self.assertContains(response, 'mamba@gmail.com')
		self.assertContains(response, 'Update Profile')

	# Test that the user can successfully update his profile.
	def test_update_profile(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to update profile page
		img = BytesIO(b'1010')
		img.name = 'pic.jpg'
		client.post('/profile/', {'action': 'Update Profile', 'description': 'my bio', 'img': img})

		# Test that the profile has been successfully updated
		user = User.objects.get(email='mamba@gmail.com')
		description = user.description
		self.assertEqual(description, 'my bio', 'User description not properly set.')

		image = user.image
		self.assertNotEqual(image, 'default.jpg', 'Image error.')

	# Test that the user's profile picture is not updated if a non-image file is uploaded.
	def test_update_profile_incorrect_file_type(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to update profile page
		img = BytesIO(b'1010')
		img.name = 'pic.doc'
		client.post('/profile/', {'action': 'Update Profile', 'description': 'my bio', 'img': img})

		# Test that the profile has been successfully updated
		user = User.objects.get(email='mamba@gmail.com')
		description = user.description
		self.assertEqual(description, 'my bio', 'User description not properly set.')

		image = user.image
		self.assertEqual(image, 'default.jpg', 'Image error.')

	# Test that the user's profile description is updated even if no image is uploaded.
	def test_update_profile_no_image(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to update profile page
		client.post('/profile/', {'action': 'Update Profile', 'description': 'my bio'})

		# Test that the profile has been successfully updated
		user = User.objects.get(email='mamba@gmail.com')
		description = user.description
		self.assertEqual(description, 'my bio', 'User description not properly set.')

		image = user.image
		self.assertEqual(image, 'default.jpg', 'Image error.')


class RatingTestCases(TestCase):
	# Create users before tests and post some requests
	def setUp(self):
		# Create users
		User.objects.create_user('mamba@gmail.com', 'CS3240!!')
		User.objects.create_user('mamba@yahoo.com', 'password')
		User.objects.create_user('sean@gmail.com', 'sean')

		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to myRequest page to create a new request
		client.post('/myRequest/', {'action': 'Submit', 'title': 'Help me!', 'location': 'Clark',
									'description': 'I really need help. $5'}, follow=True)

		# Login as next user and create a new request
		client.login(username='mamba@yahoo.com', password='password')
		client.post('/myRequest/', {'action': 'Submit', 'title': 'Math help', 'location': 'Clem',
									'description': 'Integrals'}, follow=True)

		# Login as next user and create a new request
		client.login(username='sean@gmail.com', password='sean')
		client.post('/myRequest/', {'action': 'Submit', 'title': 'Science help', 'location': 'Alderman',
									'description': 'Acids and bases'}, follow=True)

	# Test that users have the option to review each other after working together, and that rating is reflected
	# on the profile page
	def test_basic_review(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Offer help to mamba@yahoo.com
		client.post('/feed/', {'action': 'Offer Help', 'tutee': 'mamba@yahoo.com'})

		# Login as other account and accept help
		client.login(username='mamba@yahoo.com', password='password')
		client.post('/myRequest/', {'action': 'Accept and Delete', 'tutor': 'mamba@gmail.com'})

		# Check that both users now appear in each other's reviewable user field
		gmail = User.objects.get(email='mamba@gmail.com')
		yahoo = User.objects.get(email='mamba@yahoo.com')
		self.assertEqual(gmail.reviewable_user, yahoo.email)
		self.assertEqual(yahoo.reviewable_user, gmail.email)

		# Send get request to contacts page and make sure review button appears
		response = client.get('/contacts/')
		self.assertContains(response, 'Review')

		# Send get request to make sure review page displays proper reviewee
		response = client.get('/review/')
		self.assertContains(response, 'mamba@gmail.com')

		# Review the gmail user
		client.post('/review/', {'action': 'Submit', 'rating': 5, 'description': 'Great'})

		# Check that the gmail user now reflects the review
		gmail = User.objects.get(email='mamba@gmail.com')
		self.assertEqual(gmail.avg_rating, 5, 'Average rating not properly set.')

		# Login as gmail user and review the yahoo user
		client.login(username='mamba@gmail.com', password='CS3240!!')
		client.post('/review/', {'action': 'Submit', 'rating': 3, 'description': 'Okay'})

		# Check that the yahoo user now reflects the review
		yahoo = User.objects.get(email='mamba@yahoo.com')
		self.assertEqual(yahoo.avg_rating, 3, 'Average rating not properly set.')

		# Check that the review is displayed on the profile page
		response = client.get('/profile/')
		self.assertContains(response, 'Great')

		# Check that the users can no longer review each other
		response = client.get('/review/')
		self.assertContains(response, 'Currently no user to review')

	# Test that average rating is properly calculated
	def test_multiple_reviews(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Offer help to mamba@yahoo.com
		client.post('/feed/', {'action': 'Offer Help', 'tutee': 'mamba@yahoo.com'})

		# Login as other account and accept help
		client.login(username='mamba@yahoo.com', password='password')
		client.post('/myRequest/', {'action': 'Accept and Delete', 'tutor': 'mamba@gmail.com'})

		# Review the gmail user
		client.post('/review/', {'action': 'Submit', 'rating': 5, 'description': 'Great'})

		# Post a new request
		client.post('/myRequest/', {'action': 'Submit', 'title': 'Math help', 'location': 'Clem',
								'description': 'Integrals'}, follow=True)

		# Login as mamba@gmail.com and offer help again
		client.login(username='mamba@gmail.com', password='CS3240!!')
		client.post('/feed/', {'action': 'Offer Help', 'tutee': 'mamba@yahoo.com'})

		# Login as other account and accept help, and review user again
		client.login(username='mamba@yahoo.com', password='password')
		client.post('/myRequest/', {'action': 'Accept and Delete', 'tutor': 'mamba@gmail.com'})
		client.post('/review/', {'action': 'Submit', 'rating': 2, 'description': 'meh'})

		# Check that the gmail user's average rating is now 3.5
		gmail = User.objects.get(email='mamba@gmail.com')
		self.assertEqual(gmail.avg_rating, 3.5, 'Average rating incorrectly calculated.')

		# Check that the gmail user's profile displays both reviews
		response = client.post('/feed/', {'action': 'View Profile', 'tutee': 'mamba@gmail.com'})
		self.assertContains(response, 'meh')
		self.assertContains(response, 'Great')

		# Check that the gmail user's profile displays both reviews when accessed from that account
		client.login(username='mamba@gmail.com', password='CS3240!!')
		response = client.get('/profile/')
		self.assertContains(response, 'meh')
		self.assertContains(response, 'Great')

class ContactTestCases(TestCase):
	# Create users before tests and post some requests
	def setUp(self):
		# Create users
		User.objects.create_user('mamba@gmail.com', 'CS3240!!')
		User.objects.create_user('mamba@yahoo.com', 'password')
		User.objects.create_user('sean@gmail.com', 'sean')

		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to myRequest page to create a new request
		client.post('/myRequest/', {'action': 'Submit', 'title': 'Help me!', 'location': 'Clark',
									'description': 'I really need help. $5'}, follow=True)

		# Login as next user and create a new request
		client.login(username='mamba@yahoo.com', password='password')
		client.post('/myRequest/', {'action': 'Submit', 'title': 'Math help', 'location': 'Clem',
									'description': 'Integrals'}, follow=True)

		# Login as next user and create a new request
		client.login(username='sean@gmail.com', password='sean')
		client.post('/myRequest/', {'action': 'Submit', 'title': 'Science help', 'location': 'Alderman',
									'description': 'Acids and bases'}, follow=True)

	# Test that users can add each other as a contact
	def test_add_contact(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Add yahoo account as a contact
		client.post('/contacts/', {'action': 'Add', 'new_contact': 'mamba@yahoo.com'})

		# Check that both users were added to each others contacts
		gmail = User.objects.get(email='mamba@gmail.com')
		yahoo = User.objects.get(email='mamba@yahoo.com')
		self.assertTrue(yahoo in gmail.contacts.all())
		self.assertTrue(gmail in yahoo.contacts.all())

		# Check that the yahoo user now appears on the contacts page
		response = client.get('/contacts/')
		self.assertContains(response, 'mamba@yahoo.com')

	# Test that users cannot add themselves as a contact, or a non-existent user
	def test_invalid_contact(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Add invalid account as a contact
		client.post('/contacts/', {'action': 'Add', 'new_contact': 'random@yahoo.com'})

		# Check that the contacts list is still empty
		gmail = User.objects.get(email='mamba@gmail.com')
		self.assertTrue(len(gmail.contacts.all()) == 0, 'Invalid contact was added.')

		# Try to add yourself as a contact
		client.post('/contacts/', {'action': 'Add', 'new_contact': 'mamba@gmail.com'})

		# Check that the contacts list is still empty
		gmail = User.objects.get(email='mamba@gmail.com')
		self.assertTrue(len(gmail.contacts.all()) == 0, 'Invalid contact was added.')


class MessageTestCases(TestCase):
	# Create users before tests and post some requests
	def setUp(self):
		# Create users
		User.objects.create_user('mamba@gmail.com', 'CS3240!!')
		User.objects.create_user('mamba@yahoo.com', 'password')
		User.objects.create_user('sean@gmail.com', 'sean')

		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Send POST request to myRequest page to create a new request
		client.post('/myRequest/', {'action': 'Submit', 'title': 'Help me!', 'location': 'Clark',
									'description': 'I really need help. $5'}, follow=True)

		# Login as next user and create a new request
		client.login(username='mamba@yahoo.com', password='password')
		client.post('/myRequest/', {'action': 'Submit', 'title': 'Math help', 'location': 'Clem',
									'description': 'Integrals'}, follow=True)

		# Login as next user and create a new request
		client.login(username='sean@gmail.com', password='sean')
		client.post('/myRequest/', {'action': 'Submit', 'title': 'Science help', 'location': 'Alderman',
									'description': 'Acids and bases'}, follow=True)

	# Test that users can send each other messages.
	def test_send_message(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		# Add yahoo account as a contact
		client.post('/contacts/', {'action': 'Add', 'new_contact': 'mamba@yahoo.com'})

		# Send POST request to send message
		client.post('/messages/', {'action': 'Send', 'receiver': 'mamba@yahoo.com', 'message': 'Hello'})

		# Check that a conversation object with both users was created, and this message was attached
		all_conversations_user1 = Conversation.objects.filter(participants__email='mamba@gmail.com')
		conversation = all_conversations_user1.filter(participants__email='mamba@yahoo.com')[0]
		message = conversation.messages.get(content='Hello')
		self.assertEqual(message.sender.email, 'mamba@gmail.com', 'Sender was not properly set.')
		self.assertEqual(message.receiver.email, 'mamba@yahoo.com', 'Receiver was not properly set.')

		# Check that the message is now displayed on the messages page
		response = client.post('/contacts/', {'action': 'Message', 'contact': 'mamba@yahoo.com'})
		self.assertContains(response, 'Hello')

		# Login as the other user and check that the message is displayed
		client.login(username='mamba@yahoo.com', password='password')
		response = client.post('/contacts/', {'action': 'Message', 'contact': 'mamba@gmail.com'})
		self.assertContains(response, 'Hello')

		# Send a message back
		response = client.post('/messages/', {'action': 'Send', 'receiver': 'mamba@gmail.com', 'message': 'Hi'})

		# Check that both messages are now rendered
		self.assertContains(response, 'Hello')
		self.assertContains(response, 'Hi')

		# Login as original user and check that both messages are displayed
		client.login(username='mamba@gmail.com', password='CS3240!!')
		response = client.post('/contacts/', {'action': 'Message', 'contact': 'mamba@yahoo.com'})
		self.assertContains(response, 'Hello')
		self.assertContains(response, 'Hi')
