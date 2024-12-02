from rest_framework import serializers
from api.models import User, Place, Review
from django.contrib.auth import authenticate
import re


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']



class UserRegistrationSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(
        style={'input_type': 'password'}, write_only=True, error_messages={"required": "Provide a password.", "blank": "Provide a password."})

    class Meta:
        model = User
        fields = ['email', 'username',
                  'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True},
            "username": {"error_messages": {"required": "Enter your full name.", 'blank': "Enter your full name."}},
            "password": {"error_messages": {"required": "Provide a password.", 'blank': "Provide a password."}},
            "confirm_password": {"error_messages": {"required": "Provide a confirm password.", 'blank': "Provide a confirm password."}},
            "email": {"error_messages": {"required": "Enter your email address.", 'blank': "Enter your email address."}}
        }

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        fullname = attrs.get('username')

        special_char = re.compile('[@_!$%^&*()<>?/\|}{~:]#')

        if special_char.search(fullname) != None:
            raise serializers.ValidationError(
                'Full name should not contain any special characters.')

        if bool(re.search(r'\d', fullname)):
            raise serializers.ValidationError(
                'Full name should not contain numbers.')

        if len(fullname) < 3 or len(fullname) > 26:
            raise serializers.ValidationError(
                "Full name must have 3-26 characters.")

        if len(password) < 8 or len(password) > 20:
            raise serializers.ValidationError(
                'Password must have 8-20 characters.')

        if password != confirm_password:
            raise serializers.ValidationError(
                "Password and confirm password did not match.")

        return attrs

    def create(self, validated_data):
        del validated_data['confirm_password']
        validated_data = {**validated_data,
                          'email': (validated_data['email']).lower()}
        return User.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, error_messages={'required': 'Enter your email address.', 'blank': 'Enter your email address.'})

    class Meta:
        model = User
        fields = ['email', 'password']
        extra_kwargs = {'password': {'error_messages': {
            'blank': 'Provide a password.', 'required': 'Provide a password.'}}}

    def validate(self, attrs):
        email = attrs.get('email').lower()
        password = attrs.get('password')
        user = authenticate(email=email, password=password)
        if user is None:
            raise serializers.ValidationError("Email or password is invalid.")
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password']



class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = '__all_'



class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all_'


