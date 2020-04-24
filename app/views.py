from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import timezone
from django.contrib.auth import get_user, logout
from django.db.models import Q
from .models import *
from .forms import *
from django.core.mail import send_mail
from django.conf import settings
import datetime
'''
* REFERENCES
* Title: Sending email (Django Documentation)
* URL: https://docs.djangoproject.com/en/3.0/topics/email/
'''
# Rendering views
def index(request):
    # If logged in, send them to feed page
    if request.user.is_authenticated:
        return HttpResponseRedirect('/feed')
    # Else, send to login page
    else:
        return render(request, 'app/index.html')


# The old redirect page -- was giving some form submission errors. Deemed unnecessary
# def redirect(request):
#     if request.user.is_authenticated:
#         return render(request, 'app/redirect.html')
#     else:
#         return HttpResponseRedirect('/')


def feed(request):
    # Check if logged in
    if request.user.is_authenticated:
        # handle post request
        if request.method == 'POST':
            # If it's an 'offer help' request...
            if request.POST.get('action') == 'Offer Help':
                # Get the tutor who is offering help
                tutor = get_user(request)

                # Get the tutee who owns the request
                tutee = request.POST.get('tutee')

                # Add the tutor to the list of tutors attached to that request
                request_to_edit = Request.objects.get(user=tutee)
                request_to_edit.tutors.add(tutor)
                request_to_edit.save()

                # Refresh feed
                return HttpResponseRedirect('/feed')

            # If it's a 'revoke offer' request...
            elif request.POST.get('action') == 'Revoke Offer':
                # Get the tutor who is revoking their offer
                tutor = get_user(request)

                # Get the tutee who owns the request
                tutee = request.POST.get('tutee')

                # Remove the tutor from the list of tutors attached to that request
                request_to_edit = Request.objects.get(user=tutee)
                request_to_edit.tutors.remove(tutor)
                request_to_edit.save()

                # Refresh feed
                return HttpResponseRedirect('/feed')

            # If it's a 'view profile' request
            elif request.POST.get('action') == 'View Profile':
                # Get the email of the tutee who owns the request (this is the profile we want to display)
                tutee = request.POST.get('tutee')

                # Get the User instance
                tutee_user = User.objects.get(email=tutee)

                # Get reviews associated with this tutee
                reviews = Review.objects.filter(reviewee=tutee)

                # Pass to context
                context = {
                    'tutorORtutee': tutee_user,
                    'reviews': reviews
                }

                return render(request, 'app/profile.html', context)

            # If it's a 'logout' request...
            elif request.POST.get('action') == 'Logout':
                logout(request)
                return HttpResponseRedirect('/')

        # handle get request
        else:
            # Get list of requests, ordered by publication date/time
            if 'filter' in request.GET:
                query = request.GET.get('filter')
                requests_list = Request.objects.order_by('-pub_date')[:].filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query))
            else:  
                requests_list = Request.objects.order_by('-pub_date')[:]

            # Compute time since each request was published, and store in list in identical order
            times = []
            for item in requests_list:
                time_since_post = calculate_timestamp(item)
                times.append(time_since_post)

            # Pass requests_and_times in context
            context = {
                'requests_list': requests_list,
                'times': times,
            }

            return render(request, 'app/feed.html', context)

    # Else, not logged in; show log in page
    else:
        return HttpResponseRedirect('/')
# -- END OF FEED VIEW --

def myRequest(request):
    # Check if logged in
    if request.user.is_authenticated:
        # If getting a post request...
        if request.method == 'POST':
            # If it's a 'new request' request...
            if request.POST.get('action') == 'Submit':
                # Make sure they don't have an active request
                user = get_user(request)
                if user.has_active_request:
                    return HttpResponseRedirect('/myRequest')

                # If they don't have an active request, go ahead and create the request with their entered data
                title = request.POST['title']
                location = request.POST['location']
                description = request.POST['description']
                new_request = Request()
                new_request.title = title
                new_request.location = location
                new_request.description = description
                new_request.pub_date = timezone.now()
                new_request.user = request.user.email
                new_request.save()

                # Set their boolean flag
                user.has_active_request = True
                user.save()

                # Use redirect to refresh the page
                return HttpResponseRedirect('/myRequest')

            # If it's a 'delete request' request...
            elif request.POST.get('action') == 'Delete':
                # Find the request using the user's email
                user = get_user(request)
                email = user.email
                instance = Request.objects.filter(user=email)
                instance.delete()

                # Set their boolean flag
                user.has_active_request = False
                user.save()

                # Use redirect to refresh the page
                return HttpResponseRedirect('/myRequest')

            # If it's an 'edit request' request...
            elif request.POST.get('action') == 'Edit':
                # Find the request using the user's email
                user = get_user(request)
                request_to_edit = Request.objects.get(user=user.email)

                # Get the request's data and pass in context to pre-fill the editor with the data
                title = request_to_edit.title
                location = request_to_edit.location
                description = request_to_edit.description
                context = {
                    'title': title,
                    'location': location,
                    'description': description
                }
                return render(request, 'app/requestEditor.html', context)

            # If they've decided to update the request... (saving the edited changes)
            elif request.POST.get('action') == 'Update':
                # Find the request using the user's email
                user = get_user(request)
                request_to_edit = Request.objects.get(user=user.email)

                # Update the info and save
                request_to_edit.title = request.POST['title']
                request_to_edit.location = request.POST['location']
                request_to_edit.description = request.POST['description']
                request_to_edit.save()

                # Redirect to refresh myRequest page and display the updated request
                return HttpResponseRedirect('/myRequest/')

            # If they're trying to view a tutor's profile...
            elif request.POST.get('action') == 'View Profile':
                # Get the tutor associated with the 'View profile' button they pressed
                tutor = request.POST.get('tutor')

                # Get the User instance
                tutor_user = User.objects.get(email=tutor)

                # Get the reviews for this tutor
                reviews = Review.objects.filter(reviewee=tutor)

                # Pass to context
                context = {
                    'tutorORtutee': tutor_user,
                    'reviews': reviews
                }

                return render(request, 'app/profile.html', context)

            # If they're trying to accept a request...
            elif request.POST.get('action') == 'Accept and Delete':
                # Get User and Request objects
                user = get_user(request)
                request_to_edit = Request.objects.get(user=user.email)
                request_title = request_to_edit.title
                request_description = request_to_edit.description
                request_location = request_to_edit.location

                # Get tutor to accept
                tutor = request.POST.get('tutor')

                # Make sure that the tutor hasn't revoked their offer in the time that the tutee was viewing
                # the page!
                tutor_found = False
                for tutor_in_list in request_to_edit.tutors.all():
                    if tutor == tutor_in_list.email:
                        tutor_found = True
                # If the tutor has revoked their offer, pass special flag 'tutor_not_found' and an alert should be
                # displayed.
                if not tutor_found:
                    time_since_request = calculate_timestamp(request_to_edit)
                    context = {
                        'request': request_to_edit,
                        'time_since_request': time_since_request,
                        'tutor_not_found': True
                    }
                    return render(request, 'app/myRequest.html', context)

                # If the tutor's offer still holds, go ahead and delete the request, and set boolean flag
                request_to_edit.delete()
                user.has_active_request = False

                # Deal with reviews
                user.reviewable_user = tutor # save the tutor email as reviewable
                # tutor variable should have been storing their email according to line 218
                user.save()

                # Get the tutor's User object
                tutor_user = User.objects.get(email=tutor)

                # Deal with reviews
                tutor_user.reviewable_user = user.email # save the user email as reviewable to the tutor
                tutor_user.save()

                # If the tutor is not in the user's contacts, add the tutor
                if tutor_user not in user.contacts.all():
                    user.contacts.add(tutor_user)
                    user.save()
                    # Create a new Conversation object with them (need to save before adding participants)
                    conversation = Conversation()
                    conversation.save()
                    conversation.participants.add(user)
                    conversation.participants.add(tutor_user)
                    conversation.save()

                # If the user is not in the tutor's contacts, add the user
                if user not in tutor_user.contacts.all():
                    tutor_user.contacts.add(user)
                    tutor_user.save()

                # Send email to tutor to notify that request was accepted
                subject = 'QuickTutor Alert - Your Offer Has Been Accepted'
                message = user.email + ' has accepted your help for the following request: \n\n' \
                        'Title: ' + request_title + '\n' \
                        'Location: ' + request_location + '\n' \
                        'Description: ' + request_description + '\n\n' \
                        'Visit http://quicktutor-mamba.herokuapp.com/contacts/ to contact them and get started!'
                sender = 'quicktutormamba@gmail.com'
                recipient = [tutor]

                send_mail(subject, message, sender, recipient, fail_silently=True)

                # Call helper method to get the correct Conversation object
                conversation = getConversation(user.email, tutor)

                # Get the last 50 messages, ordered from oldest to most recent
                messages = conversation.messages.all().order_by('timestamp')[:50]

                context = {
                    'user': user,
                    'other_user': tutor_user,
                    'messages': messages,
                }

                # Send to messages page with this tutor!
                return render(request, 'app/messages.html', context)

            # If it's a 'logout' request...
            elif request.POST.get('action') == 'Logout':
                logout(request)
                return HttpResponseRedirect('/')

        # Else, a GET request. just loading the page
        else:
            user = get_user(request)

            # If the user has a request, get it and pass it to the view for display
            if user.has_active_request:
                my_request = Request.objects.get(user=user.email)

                # Compute time since request was created and pass as string to context
                time_since_request = calculate_timestamp(my_request)

                context = {
                    'request': my_request,
                    'time_since_request': time_since_request,
                }

                return render(request, 'app/myRequest.html', context)

            # Else they don't have an active request, no context needed, show request creation form)
            else:
                return render(request, 'app/myRequest.html')

    # Else not authenticated
    else:
        return HttpResponseRedirect('/')
# -- END OF MYREQUEST VIEW --


def profile(request):
    # Check if logged in
    if request.user.is_authenticated:
        # handle post request
        if request.method == 'POST':
            # If it's a 'logout' request...
            if request.POST.get('action') == 'Logout':
                logout(request)
                return HttpResponseRedirect('/')

            # If it's an 'Update Profile' request
            elif request.POST.get('action') == 'Update Profile':
                # Get current user
                user = get_user(request)

                # Get form data
                description = request.POST.get('description')
                image = request.FILES.get('img') # will be None if not found

                # Convert to string to check file type
                invalid_image = True
                if image is not None:
                    string_image = image.name.lower()
                    if string_image.endswith('.png') or string_image.endswith('.jpg') or string_image.endswith('.jpeg')\
                                                                                    or string_image.endswith('.gif'):
                        invalid_image = False

                # If no image selected, or invalid image file type, get current image setting
                if invalid_image:
                    image = user.image

                # Update user object
                user.description = description
                user.image = image
                user.save()

                # Redirect to profile page to refresh
                return HttpResponseRedirect('/profile')

        # handle get request
        else:
            # Get reviews for this user
            user = get_user(request)
            reviews = Review.objects.filter(reviewee=user.email)

            # Pass to context
            context = {
                'user': user,
                'reviews': reviews
                }
            return render(request, 'app/profile.html', context)
    # if user is not logged in
    else:
        return HttpResponseRedirect('/')


def contacts(request):
    # Check if logged in
    if request.user.is_authenticated:
        # handle post request
        if request.method == 'POST':
            # If it's a 'message' request...
            if request.POST.get('action') == 'Message' or request.POST.get('action') == 'Check for new messages':
                # Get the conversation object associated with this person.
                user = get_user(request)
                user_email = user.email
                other_user_email = request.POST.get('contact')

                # Call helper method to get the correct Conversation object
                conversation = getConversation(user_email, other_user_email)

                # Get the last 100 messages, ordered from oldest to most recent
                messages = conversation.messages.all().order_by('timestamp')[:100]

                # Get the other user
                other_user = User.objects.filter(email=other_user_email)[0]

                context = {
                    'user': user,
                    'other_user': other_user,
                    'messages': messages,
                }

                return render(request, 'app/messages.html', context)

            # If it's an 'Add' (contact) request...
            if request.POST.get('action') == 'Add':
                # Get user
                user = get_user(request)

                # Get contact to add
                contact_to_add_email = request.POST.get('new_contact')
                contact_exists = User.objects.filter(email=contact_to_add_email).exists()

                # If a user with this email does not exist, or if you're trying to add yourself,
                # just redirect to contacts page
                if (not contact_exists or contact_to_add_email == user.email):
                    return HttpResponseRedirect('/contacts')

                # Otherwise, check to see if this user is already a contact
                else:
                    contact_to_add = User.objects.get(email=contact_to_add_email)
                    # If user is already a contact, just redirect to contacts page
                    if contact_to_add in user.contacts.all():
                        return HttpResponseRedirect('/contacts/')
                    # If user is not already a contact...
                    else:
                        # Add as contact
                        user.contacts.add(contact_to_add)
                        user.save()

                        # Add this user as contact for other user
                        if (user not in contact_to_add.contacts.all()):
                            contact_to_add.contacts.add(user)
                            contact_to_add.save()

                        # Create a new Conversation with them (need to save before adding participants)
                        conversation = Conversation()
                        conversation.save()
                        conversation.participants.add(user)
                        conversation.participants.add(contact_to_add)
                        conversation.save()

                        return HttpResponseRedirect('/contacts/')

            # If it's a 'logout' request...
            if request.POST.get('action') == 'Logout':
                logout(request)
                return HttpResponseRedirect('/')

        # handle get request
        else:
            # Get current user to fetch list of contacts
            user = get_user(request)

            # Fetch list of contacts (query set of user objects)
            contacts_users = user.contacts.all()

            # Convert into list of users and names
            users = []
            names = []
            for contact in contacts_users:
                users.append(contact)
                name = contact.get_full_name()
                names.append(name)

            # Set context
            context = {
                'users': users,
                'names': names,
                'self': user,
            }

            return render(request, 'app/contacts.html', context)
    # If not logged in, send to login page
    else:
        return HttpResponseRedirect('/')


def messages(request):
    # Check if user is logged in
    if request.user.is_authenticated:
        # If post request...
        if request.method == 'POST':
            # If it is a 'Send' (message) request
            if request.POST.get('action') == 'Send':
                # Get user
                user = get_user(request)

                # Get receiver
                receiver_email = request.POST.get('receiver')
                receiver = User.objects.get(email=receiver_email)

                # Get message content
                msg_content = request.POST.get('message')

                # Create a new Message
                message = Message()
                message.timestamp = timezone.now()
                message.sender = user
                message.receiver = receiver
                message.content = msg_content
                message.save()

                # Call helper method to get the correct Conversation object
                conversation = getConversation(user.email, receiver_email)

                # Add message to the conversation
                conversation.messages.add(message)

                # Get the last 100 messages, ordered from oldest to most recent
                messages = conversation.messages.all().order_by('timestamp')[:100]

                context = {
                    'user': user,
                    'other_user': receiver,
                    'messages': messages,
                }

                return render(request, 'app/messages.html', context)

        # handle get request
        else:
            return render(request, 'app/messages.html')
    # If not logged in, send to login page
    else:
        return HttpResponseRedirect('/')


# Helper method for calculating how long ago a request was posted. Takes in a Request object as parameter.
def calculate_timestamp(request):
    # Get datetime from request object
    pub_date = str(request.pub_date)

    # Isolate components of pub date
    year = int(pub_date[0:4])
    month = int(pub_date[5:7])
    day = int(pub_date[8:10])
    hour = int(pub_date[11:13])
    minute = int(pub_date[14:16])
    second = int(pub_date[17:19])

    # Create datetime object
    pub_date = datetime.datetime(year, month, day, hour, minute, second)

    # Isolate components of current time
    current_time = str(timezone.now())
    year = int(current_time[0:4])
    month = int(current_time[5:7])
    day = int(current_time[8:10])
    hour = int(current_time[11:13])
    minute = int(current_time[14:16])
    second = int(current_time[17:19])

    # Create datetime object
    current_time = datetime.datetime(year, month, day, hour, minute, second)

    # Compute difference and convert to minutes
    delta = current_time - pub_date

    # If more than a day ago, just return number of days
    if delta.days == 1:
        return "1 day ago"
    elif delta.days > 1:
        return str(delta.days) + " days ago"

    # Otherwise, it's less than a day, so return number of hours or minutes
    minutes = int(delta.seconds / 60)

    # If less than one minute, return "Just now"
    if minutes <= 1:
        return "Just now"
    # If less than an hour, return number of minutes
    elif minutes <= 59:
        return str(minutes) + " minutes ago"
    # Otherwise, return number of hours
    elif minutes <= 119:
        return "1 hour ago"
    elif minutes <= 1439:
        return str(int(minutes/60)) + " hours ago"


# Helper method that takes two email addresses and finds the Conversation object between these two
def getConversation(user1, user2):
    # Get the conversations involving user1
    all_conversations_user1 = Conversation.objects.filter(participants__email=user1)

    # Filter these conversations by the other user to get the single conversation between these two users
    conversation = all_conversations_user1.filter(participants__email=user2)[0]

    return conversation


def review(request):
    # Check if logged in
    if request.user.is_authenticated:
        # If getting a post request...
        if request.method == 'POST':
            # If it's a 'Submit' review request...
            if request.POST.get('action') == 'Submit':
                # Get current user
                user = get_user(request)

                # create a new review object
                rating = request.POST['rating']
                description = request.POST['description']
                new_review = Review()
                new_review.rating = rating
                new_review.description = description
                new_review.reviewer = user.email
                reviewee_user = User.objects.get(email=user.reviewable_user) # need for later
                new_review.reviewee = user.reviewable_user
                new_review.save()

                # Update the reviewer user: reset reviewable_user field
                user.reviewable_user = "None"
                user.save()

                # Update the reviewee user: ratings field
                current_average = float(reviewee_user.avg_rating)
                current_count = int(reviewee_user.rating_count)
                new_count = current_count + 1
                new_average = ((new_count - 1)*current_average + int(rating))/new_count
                reviewee_user.rating_count = new_count
                reviewee_user.avg_rating = round(new_average, 1)
                reviewee_user.save()

                # Use redirect to go back to contacts page
                return HttpResponseRedirect('/contacts/')
            # If it's a 'logout' request...
            elif request.POST.get('action') == 'Logout':
                logout(request)
                return HttpResponseRedirect('/')
       # Else, a GET request. just loading the page
        else:
            return render(request, 'app/review.html')
    # Else not authenticated
    else:
        return HttpResponseRedirect('/')