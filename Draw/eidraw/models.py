from django.db import models
import uuid

class Group(models.Model):
    name = models.CharField(max_length=100)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    organizer_email = models.EmailField() # e-mail of organizer
    date = models.DateField(null=True, blank=True)
    drawing_enabled = models.BooleanField(default=False)
    gift_price_limit = models.DecimalField(max_digits=6, decimal_places=2, default=20.00)

    def __str__(self):
        return self.name

class AgeGroup(models.Model):
    name = models.CharField(max_length=50)
    min_age = models.IntegerField()
    max_age = models.IntegerField()

    def __str__(self):
        return self.name

class Person(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user_id = models.CharField(max_length=100)  # WhatsApp ID of registrant
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    wishlist = models.TextField(blank=True, null=True)
    has_drawn = models.BooleanField(default=False)
    is_drawn = models.BooleanField(default=False)
    drawn_person = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('group', 'name')

class Exclusion(models.Model):
    person = models.ForeignKey(Person, related_name='exclusions', on_delete=models.CASCADE)
    exclude = models.ForeignKey(Person, related_name='excluded_by', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('person', 'exclude')