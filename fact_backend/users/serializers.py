from rest_framework import serializers


class UsersStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    app = serializers.CharField()

