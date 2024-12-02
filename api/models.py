import datetime
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.core.exceptions import ValidationError

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, cofirm_password=None):
        """
        Creates and saves a User with the given email, username, and password.
        """
        if not email:
            raise ValueError('User must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None):
        """
        Creates and saves a superuser with the given email, username,, and password.
        """
        user = self.create_user(
            email,
            password=password,
            username=username,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    email = models.EmailField(
        max_length=255,
        unique=True,
    )
    username = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

  
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        return self.is_admin

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return self.is_admin



class Place(models.Model):
    
    PLACE_TYPES = [
        ('hotel', 'Hotel'),
        ('attraction', 'Attraction'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="places")

    name = models.CharField(max_length=255, verbose_name="Place Name")
    location = models.TextField(verbose_name="Location")
    place_type = models.CharField(max_length=50, choices=PLACE_TYPES, verbose_name="Type")  

    
    is_image_file = models.BooleanField(default=True, verbose_name="Is Image File? (Unchecked for URL)")
    image_url = models.URLField(blank=True, null=True, verbose_name="Image URL")
    image_file = models.ImageField(upload_to="place_images/", blank=True, null=True, verbose_name="Image File")

    
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    combined_amenities = models.TextField(blank=True, null=True)
    rating = models.FloatField(default=0.0, blank=True, null=True)
    number_of_reviews = models.PositiveIntegerField(default=0, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    ranking = models.CharField(max_length=55, blank=True, null=True)
    subcategories = models.TextField(blank=True, null=True)  

    published_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        
        if self.is_image_file and not self.image_file:
            raise ValidationError("Image file is required because 'Is Image File?' is checked.")
        if not self.is_image_file and not self.image_url:
            raise ValidationError("Image URL is required because 'Is Image File?' is unchecked.")

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Place"
        verbose_name_plural = "Places"

class Review(models.Model):
    SENTIMENT_TYPES = [
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
        ('no_sentiment', 'No Sentiment'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()  
    sentiment = models.CharField(max_length=50, choices=SENTIMENT_TYPES, verbose_name="Sentiment Type", default="")  

    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'place')

    def __str__(self):
        return f"Review by {self.user.username} for {self.place.name}"
