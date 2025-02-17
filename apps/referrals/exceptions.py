from rest_framework.exceptions import APIException
from rest_framework import status


class InvalidReferralCodeException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid or expired referral code"
    default_code = 'invalid_referral_code'


class SelfReferralException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Cannot use your own referral code"
    default_code = 'self_referral'


class AlreadyReferredException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "User is already referred"
    default_code = 'already_referred'