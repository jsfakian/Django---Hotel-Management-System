from rest_framework.decorators import api_view
from rest_framework.response import Response
import joblib
import numpy as np
import pandas as pd
from .models import Hotel, Booking

# Load pre-trained model
try:
    model = joblib.load("dynamic_pricing_model.pkl")
except:
    print("no model")

@api_view(["GET"])
def get_dynamic_price(request, hotel_id):
    """API endpoint to get AI-driven price recommendation for a hotel room."""

    # Get Hotel Data
    try:
        hotel = Hotel.objects.get(id=hotel_id)
        latest_booking = Booking.objects.filter(hotel=hotel).latest("check_in_date")
    except Hotel.DoesNotExist:
        return Response({"error": "Hotel not found"}, status=404)
    except Booking.DoesNotExist:
        return Response({"error": "No booking data available"}, status=404)

    # Prepare Input Data
    input_data = pd.DataFrame({
        "occupancy_rate": [latest_booking.occupancy_rate],
        "competitor_price": [latest_booking.competitor_price],
        "demand_index": [latest_booking.demand_index],
        "day_of_week": [pd.to_datetime(latest_booking.check_in_date).dayofweek],
        "season": [get_season(latest_booking.check_in_date)]
    })

    # Predict Price
    predicted_price = model.predict(input_data)[0]

    return Response({
        "hotel_name": hotel.name,
        "base_price": hotel.base_price,
        "dynamic_price": round(predicted_price, 2),
        "competitor_price": latest_booking.competitor_price,
        "occupancy_rate": latest_booking.occupancy_rate,
    })
