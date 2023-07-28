from django.db import models



class ContactMessage(models.Model):
    """
    Models for contact message 
    """
    name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50)
    subject = models.CharField(max_length=256)
    body = models.TextField(max_length=5000)

    def __str__(self):
        return self.subject