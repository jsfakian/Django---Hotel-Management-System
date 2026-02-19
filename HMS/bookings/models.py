from django.db import models

class Hotel(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    star_rating = models.IntegerField()
    base_price = models.FloatField()

    def __str__(self):
        return self.name

class Booking(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    occupancy_rate = models.FloatField()  # % of rooms booked
    competitor_price = models.FloatField()
    demand_index = models.FloatField()  # Calculated based on external sources (e.g., Google Trends)

    def __str__(self):
        return f"Booking for {self.hotel.name} on {self.check_in_date}"
