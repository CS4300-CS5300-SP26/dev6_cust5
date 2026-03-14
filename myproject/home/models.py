from django.db import models


class Property(models.Model):
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    listing_type = models.CharField(max_length=10)
    property_type = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title