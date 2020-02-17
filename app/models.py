from django.db import models
#from django.contrib.auth import models as other_models <--- django has a built in User model that we may want to use

# Create your models here.
# we will need these models at least


class User(models.Model):
    # needs tutor and tutee specific fields
    tutor_mode = models.BooleanField()  # true if in tutor_mode
    # also needs fields to contain everything associated with a profile page


class Request(models.Model):
    # need a field that maps the request to the user that wrote it (one-to-one relationship)
    title = models.CharField(max_length=100)  # the title of the request
    location = models.CharField(max_length=50)  # the location of the tutee (as specified by the tutee)
    pub_date = models.DateTimeField('date published')  # when it was published
    description = models.CharField(max_length=1000)  # a description written by the tutee
    random = models.CharField(max_length=10) # dummy field testing migrations
    # need a field to track the list of tutors that have offered their help
    # maybe need a field for proposed price?
    def __str__(self):
        return self.title


class Conversation(models.Model):
    # need a field that maps the conversation to both users
    # need a field that tracks the list of sent messages
    pass
