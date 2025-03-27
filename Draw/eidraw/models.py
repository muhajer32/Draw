from django.db import models

# Create your models here

class Settings(models.Model):
    gift_price_limit = models.DecimalField(max_digits=6, decimal_places=2, default=20.00)
    drawing_enabled = models.BooleanField(default=False)

    def __str__(self):
        return "Gift Exchange Settings"

class AgeGroup(models.Model):
    name = models.CharField(max_length=50)
    min_age = models.IntegerField()
    max_age = models.IntegerField()

    def __str__(self):
        return self.name

class Person(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    GenderChoices = models.TextChoices('Gender', 'MALE FEMALE')
    gender = models.CharField(
        max_length=6,
        choices=GenderChoices.choices,
        default=GenderChoices.MALE
    )
    extra_info = models.TextField(blank=True)
    age_group = models.ForeignKey(AgeGroup, on_delete=models.CASCADE)
    owner_id = models.CharField(max_length=50)  # WhatsApp/Telegram ID
    drawn_person = models.OneToOneField('self', null=True, blank=True, on_delete=models.SET_NULL)
    has_drawn = models.BooleanField(default=False)
    is_drawn = models.BooleanField(default=False)

    def __str__(self):
        return self.name