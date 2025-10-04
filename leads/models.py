from django.db import models

class Offer(models.Model):
    name = models.CharField(max_length=200)
    value_props = models.JSONField()
    ideal_use_cases = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

class Lead(models.Model):
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    industry = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    linkedin_bio = models.TextField(blank=True)
    intent = models.CharField(max_length=20, choices=[
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low')
    ], null=True)
    score = models.IntegerField(null=True)
    reasoning = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
