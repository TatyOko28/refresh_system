# File: apps/referrals/urls.py
from django.urls import path
from .views import ReferralRegistrationView
from .views import (
    ReferralCodeCreateView,
    ReferralCodeDeleteView,
    ReferralCodeByEmailView,
    ReferralListView
)

urlpatterns = [
    path('codes/create/', ReferralCodeCreateView.as_view(), 
         name='referral-code-create'),
    path('codes/<str:code>/', ReferralCodeDeleteView.as_view(), 
         name='referral-code-delete'),
    path('codes/by-email/<str:email>/', ReferralCodeByEmailView.as_view(), 
         name='referral-code-by-email'),
    path('list/', ReferralListView.as_view(), name='referral-list'),
    path('register/', ReferralRegistrationView.as_view(), name='referral-register'),
    path('stats/', ReferralListView.as_view(), name='referral-stats'),

]

