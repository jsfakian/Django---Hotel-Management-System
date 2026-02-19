from rest_framework import serializers
from .models import Contract

class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = "__all__"

class ContractSignSerializer(serializers.Serializer):
    signature = serializers.CharField(max_length=255)
