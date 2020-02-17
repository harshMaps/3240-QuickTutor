from django.shortcuts import render
from django.http import HttpResponse
from .models import *


def index(request):
    return HttpResponse("let's get this money (this is the app index)")

def feed(request):
    requests_list = Request.objects.order_by('-pub_date')[:]
    # process each request in a for loop
    context = {
        'requests_list': requests_list,
    }
    return render(request, 'app/feed.html', context)