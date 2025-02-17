# File: apps/referrals/urls.py
from django.urls import path
from .views import (
    ReferralCodeCreateView,
    ReferralCodeDeleteView,
    ReferralCodeByEmailView,
    ReferralRegistrationView,
    ReferralListView,
     ReferralStatsView
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
    path('stats/', ReferralStatsView.as_view(), name='referral-stats'),
]

