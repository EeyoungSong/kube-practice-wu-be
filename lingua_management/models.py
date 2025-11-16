from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    language = models.CharField(max_length=50, choices=[('english', 'English'), ('spanish', 'Spanish'), ('chinese', 'Chinese')])

    def __str__(self):
        return self.name

class Wordbook(models.Model):
    INPUT_CHOICES = [
        ('image', 'Image'),
        ('text', 'Text'),
        ('youtube', 'YouTube Link'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    language = models.CharField(max_length=50) 
    input_type = models.CharField(max_length=10, choices=INPUT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} by {self.user.username}"

class Sentence(models.Model):
    user = models.ForeignKey(User, related_name='sentences', on_delete=models.CASCADE)
    wordbook = models.ForeignKey(Wordbook, related_name='sentences', on_delete=models.CASCADE)
    text = models.TextField()
    meaning = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_reviewed_at = models.DateTimeField(default=timezone.now)
    review_count = models.IntegerField(default=0)
    is_last_review_successful  = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class Word(models.Model):
    user = models.ForeignKey(User, related_name='words', on_delete=models.CASCADE)
    text = models.CharField(max_length=255, db_index=True)
    others = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_reviewed_at = models.DateTimeField(default=timezone.now)
    review_count = models.IntegerField(default=0)
    is_last_review_successful  = models.BooleanField(default=False)
    success_count = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'text'], name='unique_word_text')
        ]

    def __str__(self):
        return self.text

class SentenceWord(models.Model):
    word = models.ForeignKey(Word, related_name='sentence_links', on_delete=models.CASCADE)
    sentence = models.ForeignKey(Sentence, related_name='word_links', on_delete=models.CASCADE)
    meaning = models.CharField(max_length=255, blank=True)
    pos = models.CharField(max_length=255, blank=True)
    memo = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['word', 'sentence'], name='unique_sentence_word')
        ]

    def __str__(self):
        return f"'{self.word.text}' from '{self.sentence.text[:20]}...'"
