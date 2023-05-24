from rest_framework import serializers
from core.models import Contract

from core.serializers import SuggestedContractSerializer


class OwnerContractSuggestionSerializer(serializers.ModelSerializer):
    suggestions = SuggestedContractSerializer(many=True, read_only=True)

    class Meta:
        model = Contract
        fields = [
            "id",
            "start_date",
            "end_date",
            "rent_amount",
            "deposit_amount",
            "terms_and_conditions",
            "file",
            "signature_request_id",
            "suggestions",
        ]
