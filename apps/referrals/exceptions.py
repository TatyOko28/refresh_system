# File: apps/referrals/exceptions.py
from rest_framework.exceptions import APIException
from rest_framework import status

class InvalidReferralCodeException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid or expired referral code"

class SelfReferralException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Cannot use your own referral code"

class AlreadyReferredException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "User is already referred"









