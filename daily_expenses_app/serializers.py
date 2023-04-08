from rest_framework import serializers

from daily_expenses_app import models


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializes a user profile object"""
    class Meta:
        model = models.UserProfile
        fields = (
            'id', 'region',
            'email', 'name',
            'password', 'last_email_sent_date',
            'daily_expenses_limit', 'image')
        extra_kwargs = {'password': {
            'write_only': True, 'style': {
                'input_type': 'password', 'placeholder': 'Password'}
        }, 'last_email_sent_date': {'read_only': True}}

    def create(self, validated_data):
        """Create and return a new user"""
        user = models.UserProfile.objects.create_user(
            region=validated_data['region'],
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password']
        )
#           last_email_sent_date=validated_data['last_email_sent_date']
        return user

    def update(self, instance, validated_data):
        """Handle updating user account"""
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)

        return super().update(instance, validated_data)


class UserDailyExpensesSerializer(serializers.ModelSerializer):
    """Serializes user's expenses from the model"""
    class Meta:
        model = models.UserDailyExpenses
        fields = ('id', 'user',
                  'expense_name', 'category',
                  'price', 'created_at', 'image')
        extra_kwargs = {'user': {'read_only': True}, 'id': {'read_only': True}}


class CategorySerializer(serializers.ModelSerializer):
    """Serializes the categories from the Category Model"""

    class Meta:
        model = models.Category
        fields = ('id', 'user', 'category_name', 'description')
        extra_kwargs = {'user': {'read_only': True}}


class StatisticsSerializer(serializers.Serializer):
    last_1_day = serializers.FloatField()
    last_7_days = serializers.FloatField()
    last_30_days = serializers.FloatField()
    most_used_categories = serializers.CharField()
    expenses_by_category = serializers.JSONField()


class ExpensesImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to expenses"""

    class Meta:
        model = models.UserDailyExpenses
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': "True"}}
