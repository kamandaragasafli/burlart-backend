from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegisterView,
    UserLoginView,
    GoogleLoginView,
    UserProfileView,
    UserUpdateProfileView,
    UserDeleteAccountView,
    VideoGenerationCreateView,
    VideoGenerationListView,
    VideoGenerationDetailView,
    ImageGenerationCreateView,
    ImageGenerationListView,
    ImageGenerationDetailView,
    VideoToolsListView,
    LockedPricingView,
    SubscriptionPlansView,
    SubscriptionCreateView,
    SubscriptionInfoView,
    SubscriptionCancelView,
    TopUpPackagesView,
    TopUpCreateView,
    TopUpCompleteView,
    TopUpHistoryView,
    PaymentSuccessView,
    PaymentErrorView,
    PaymentWebhookView,
)

urlpatterns = [
    # Auth endpoints
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User endpoints
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/update/', UserUpdateProfileView.as_view(), name='profile-update'),
    path('profile/delete/', UserDeleteAccountView.as_view(), name='profile-delete'),
    
    # Video generation endpoints
    path('videos/generate/', VideoGenerationCreateView.as_view(), name='video-generate'),
    path('videos/', VideoGenerationListView.as_view(), name='video-list'),
    path('videos/<int:pk>/', VideoGenerationDetailView.as_view(), name='video-detail'),
    
    # Image generation endpoints
    path('images/generate/', ImageGenerationCreateView.as_view(), name='image-generate'),
    path('images/', ImageGenerationListView.as_view(), name='image-list'),
    path('images/<int:pk>/', ImageGenerationDetailView.as_view(), name='image-detail'),
    
    # Tools endpoint
    path('tools/', VideoToolsListView.as_view(), name='tools-list'),
    
    # Locked pricing endpoint (read-only)
    path('pricing/locked/', LockedPricingView.as_view(), name='locked-pricing'),
    
    # Subscription endpoints
    path('subscriptions/plans/', SubscriptionPlansView.as_view(), name='subscription-plans'),
    path('subscriptions/create/', SubscriptionCreateView.as_view(), name='subscription-create'),
    path('subscriptions/info/', SubscriptionInfoView.as_view(), name='subscription-info'),
    path('subscriptions/cancel/', SubscriptionCancelView.as_view(), name='subscription-cancel'),
    
    # Top-up endpoints
    path('topup/packages/', TopUpPackagesView.as_view(), name='topup-packages'),
    path('topup/create/', TopUpCreateView.as_view(), name='topup-create'),
    path('topup/complete/', TopUpCompleteView.as_view(), name='topup-complete'),
    path('topup/history/', TopUpHistoryView.as_view(), name='topup-history'),
    
    # E-point Payment Callbacks
    path('payment/success/', PaymentSuccessView.as_view(), name='payment-success'),
    path('payment/error/', PaymentErrorView.as_view(), name='payment-error'),
    path('payment/webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
]
