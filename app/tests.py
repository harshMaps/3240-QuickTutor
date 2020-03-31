from django.test import TestCase, Client
from .models import *
import datetime
from django.utils import timezone
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

	# Check that user's boolean is set when they create a request
	def test_has_active_request(self):
		# Create client and login
		client = Client()
		client.login(username='mamba@gmail.com', password='CS3240!!')

		user = User.objects.get(email='mamba@gmail.com')
		self.assertTrue(user.has_active_request, 'has_active_request boolean was not set.')

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

	# STILL NEED TO TEST 'VIEW PROFILE' FEATURE FROM MYREQUEST PAGE, AS WELL AS THE ACCEPTING PROCESS


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

