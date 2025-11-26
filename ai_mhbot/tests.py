from django.test import TestCase

# Create your tests here.
from django.contrib.auth.models import User

class AuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("sean", "sean@csuchico.edu", "abc123")
        

from django.urls import reverse
from django.utils import timezone
from .models import MoodEntry, ChatMessage


class ExerciseTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("tester", "t@test.local", "pw")
        self.client.login(username="tester", password="pw")

    def test_exercise_completion_logs_chat_and_mood(self):
        url = reverse('exercise_complete')
        resp = self.client.post(url, {'exercise': 'breathing'})
        # Should redirect back to chat
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.endswith('/chat/') or resp.url == reverse('chat'))

        # ChatMessage with meta.exercise_completed should exist
        cm_exists = ChatMessage.objects.filter(user=self.user, meta__exercise_completed='breathing').exists()
        self.assertTrue(cm_exists, 'ChatMessage not recorded with exercise meta')

        # MoodEntry for today should exist and note should contain the exercise label
        today = timezone.localdate()
        me = MoodEntry.objects.filter(user=self.user, day=today).first()
        self.assertIsNotNone(me, 'MoodEntry for today not created')
        self.assertIn('Exercise completed: breathing', me.note)
