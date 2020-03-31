from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth import get_user
from django.contrib.auth import logout
from .models import *
from .forms import *
from django.contrib import messages
import datetime


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
                user.save()

                # It should automatically add the tutor as a contact and direct you to a message with them!
                return HttpResponseRedirect('/contacts/')

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
    if request.user.is_authenticated:
        # handle post request
        if request.method == 'POST':
            # If it's a 'logout' request...
            if request.POST.get('action') == 'Logout':
                logout(request)
                return HttpResponseRedirect('/')
        # handle get request
        else:
            return render(request, 'app/contacts.html')
    else:
        return HttpResponseRedirect('/')


def messages(request):
    if request.user.is_authenticated:
        return render(request, 'app/messages.html')
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
