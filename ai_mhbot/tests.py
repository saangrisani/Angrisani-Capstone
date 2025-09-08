from django.test import TestCase

# Create your tests here.
import django.urls import reverse
from django.contrib.auth.models import User

class AuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("sean", "sean@csuchico.edu", "abc123")
        