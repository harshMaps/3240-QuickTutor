from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings

'''
* REFERENCES
* Title: How to use email as username for Django authentication
* Author: Federico Jaramillo
* Date: May 10, 2017
* URL: https://www.fomfus.com/articles/how-to-use-email-as-username-for-django-authentication-removing-the-username

* Title: Model Field Reference (Django Documentation)
* URL: https://docs.djangoproject.com/en/3.0/ref/models/fields/
'''
class UserManager(BaseUserManager):
    # Need a new model manager since we removed the username field

    use_in_migrations = True

    # all-auth creates our users
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # for creating regular users
    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    # needs fields to contain everything associated with a profile page
    email = models.EmailField(('email address'), unique=True)
    username = models.CharField(default="None", max_length=15)
    description = models.CharField(default='New User',max_length=100)

    # messaging stuff
    contacts = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    
    # profile picture field
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
        # images uploaded to that directory
        # need to 'pip install Pillow' to make this work

    #fields for requests
    has_active_request = models.BooleanField(default=False)

    # fields for reviews
    reviewable_user = models.CharField(max_length=100,default="None")
    avg_rating = models.DecimalField(max_digits=2, decimal_places=1, default=0.0) # stores the value of their rating out of 5 (like stars)
    rating_count = models.IntegerField(default=0) # stores the total number of ratings they have received so far
    """
    A user can only have one reviewable user of each type at a time.
    This is because tutees can only have one active request at a time
    and tutors can only help one user at a time.
    Therefore, once they move onto making a new request/helping a new tutee
    the window of opportunity to review this user has passed.
    """
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()

    def __str__(self):
        return self.email


class Request(models.Model):
    # need a field that maps the request to the user that wrote it (one-to-one relationship)
    title = models.CharField(max_length=200)  # the title of the request
    location = models.CharField(max_length=200)  # the location of the tutee (as specified by the tutee)
    pub_date = models.DateTimeField('date published',max_length=100)  # when it was published
    description = models.CharField(max_length=1000)  # a description written by the tutee
    user = models.CharField(max_length=100) # email goes here - the unique ID
    tutors = models.ManyToManyField(settings.AUTH_USER_MODEL) # tutors that have offered help will be added onto this
    def __str__(self):
        return self.title


class Message(models.Model):
    # Sender - many messages relate to one user
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sender')

    # Receiver - many messages relate to one user
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='receiver')

    # Message content
    content = models.CharField(max_length=1000)

    # Timestamp
    timestamp = models.DateTimeField('timestamp')


class Conversation(models.Model):
    # Maps the conversation to both users
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL)

    # Tracks the list of messages in this conversation
    messages = models.ManyToManyField(Message)


class Review(models.Model):
    # need a field that maps the request to user writing it, and the user it is about
    description = models.CharField(max_length=500) # written review
    rating = models.IntegerField() # save the value of rating from 1 to 5
    reviewee = models.CharField(max_length=100) # user being reviewed
    reviewer = models.CharField(max_length=100) # user making review
    def __str__(self):
        return self.description