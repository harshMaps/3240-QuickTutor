from django.urls import path
from . import views
# needed for profile images
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('feed/', views.feed, name='feed'),
    path('myRequest/', views.myRequest, name='myRequest'),
    path('profile/', views.profile, name='profile'),
    path('contacts/', views.contacts, name='contacts'),
    path('messages/', views.messages, name='messages'),
    path('review/', views.review, name='review'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)