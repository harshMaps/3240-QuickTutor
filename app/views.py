from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import timezone
from django.contrib.auth import get_user, logout
from django.db.models import Q
from .models import *
from .forms import *
from django.contrib import messages
import datetime
import requests as rq


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

                # Get the User instance and pass to context to render their profile page
                tutee_user = User.objects.get(email=tutee)
                context = {
                    'tutorORtutee': tutee_user,
                }

                return render(request, 'app/profile.html', context)

            # If it's a 'logout' request...
            elif request.POST.get('action') == 'Logout':
                logout(request)
                return HttpResponseRedirect('/')

        # handle get request
        else:
            # Get list of requests, ordered by publication date/time
            if 'q' in request.GET:
                query = request.GET.get('q')
                requests_list = Request.objects.order_by('-pub_date')[:].filter(Q(title__icontains=query) | Q(description__icontains=query))
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

                # Get the User instance and pass in context to generate profile page
                tutor_user = User.objects.get(email=tutor)
                context = {
                    'tutorORtutee': tutor_user,
                }

                return render(request, 'app/profile.html', context)

            # If they're trying to accept a request...
            elif request.POST.get('action') == 'Accept and Delete':
                # Get User and Request objects
                user = get_user(request)
                request_to_edit = Request.objects.get(user=user.email)

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
                user.reviewable_user = tutor # save the tutor object as reviewable
                # tutor variable should have been storing their email according to line 218
                user.save()

                # Get the tutor's User object
                tutor_user = User.objects.get(email=tutor)

                # Deal with reviews
                tutor_user.reviewable_user = user.email # savee the user object as reviewable to the tutor
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

                # If the user is not in the tutor's contacts, add the user (pretty much guaranteed to happen)
                if user not in tutor_user.contacts.all():
                    tutor_user.contacts.add(user)
                    tutor_user.save()

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
            # Else updating their profile
            else: 
                u_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)

                if u_form.is_valid():
                    u_form.save()
                    # messages.success(request, f'Your account has been updated!')
                    return redirect('profile')
        # handle get request
        else:
            u_form = UserUpdateForm(instance=request.user)
        context = {
            'user': get_user(request),
            'u_form': u_form
            }
        return render(request, 'app/profile.html', context)
    else:
        return HttpResponseRedirect('/')


def contacts(request):
    # Check if logged in
    if request.user.is_authenticated:
        # handle post request
        if request.method == 'POST':
            # If it's a 'message' request...
            if request.POST.get('action') == 'Message':
                # Get the conversation object associated with this person.
                user = get_user(request)
                user_email = user.email
                other_user_email = request.POST.get('contact')

                # Call helper method to get the correct Conversation object
                conversation = getConversation(user_email, other_user_email)

                # Get the last 50 messages, ordered from oldest to most recent
                messages = conversation.messages.all().order_by('timestamp')[:50]

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
                    return HttpResponseRedirect('/contacts/')

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

            # Convert into list of emails and names
            emails = []
            names = []
            for contact in contacts_users:
                email = contact.email
                emails.append(email)
                name = contact.get_full_name()
                names.append(name)

            # Set context
            context = {
                'emails': emails,
                'names': names,
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

                # Get the last 50 messages, ordered from oldest to most recent
                messages = conversation.messages.all().order_by('timestamp')[:50]

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
    # need to create the form for them to submit reviews
    # edit the user models and remove the person they are reviewing
    # from their "reviewable_user" field
    
    # Check if logged in
    # if request.user.is_authenticated:
    #     # If getting a post request...
    #     if request.method == 'POST':
    #         # If it's a 'new request' request...
    #         if request.POST.get('action') == 'Submit':
    #             # Make sure they don't have an active request
    #             user = get_user(request)

    #             # If they don't have an active request, go ahead and create the request with their entered data
    #             rating = request.POST['rating']
    #             description = request.POST['description']
    #             new_review = Review()
    #             new_review.rating = rating
    #             new_review.description = description
    #             new_review.reviewer = user.email
    #             new_review.reviewee = user.reviewable_user
    #             new_request.save()

    #             # Reset their reviewable_user field
    #             user.reviewable_user = "None"
    #             user.save()

    #             # Use redirect to refresh the page
    #             return HttpResponseRedirect('/review')
    #         # If it's a 'logout' request...
    #         elif request.POST.get('action') == 'Logout':
    #             logout(request)
    #             return HttpResponseRedirect('/')
    #     # Else, a GET request. just loading the page
    #     else:
            return render(request, 'app/review.html')