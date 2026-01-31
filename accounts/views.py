import logging
import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    UserRegisterSerializer, 
    UserSerializer, 
    VideoGenerationSerializer,
    VideoGenerationCreateSerializer,
    ImageGenerationSerializer,
    ImageGenerationCreateSerializer,
)
from .services import VideoGenerationService, ImageGenerationService, SubscriptionService, TopUpService
from .models import VideoGeneration, ImageGeneration, Subscription, CreditPurchase
from .subscription_service import SubscriptionService
from .subscription_constants import SUBSCRIPTION_PLANS

logger = logging.getLogger(__name__)

User = get_user_model()


class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class UserLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid email or password'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.check_password(password):
            return Response(
                {'error': 'Invalid email or password'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class GoogleLoginView(APIView):
    """
    Login or register a user using a Google ID token.
    Frontend should send: { "id_token": "<google_id_token>" }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get('id_token')

        if not id_token:
            return Response(
                {'error': 'id_token is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Verify token with Google
            resp = requests.get(
                'https://oauth2.googleapis.com/tokeninfo',
                params={'id_token': id_token},
                timeout=5,
            )
            if resp.status_code != 200:
                logger.warning('Google token verification failed: %s', resp.text)
                return Response(
                    {'error': 'Invalid Google token'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            data = resp.json()
            audience = data.get('aud')
            email = data.get('email')
            email_verified = str(data.get('email_verified', '')).lower() == 'true'

            if settings.GOOGLE_CLIENT_ID and audience != settings.GOOGLE_CLIENT_ID:
                logger.warning(
                    'Google token client_id mismatch: expected %s, got %s',
                    settings.GOOGLE_CLIENT_ID,
                    audience,
                )
                return Response(
                    {'error': 'Invalid Google client id'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not email or not email_verified:
                return Response(
                    {'error': 'Google account email not verified'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'credits': 0,  # New users start with 0 credits
                    'language': 'en',
                    'theme': 'dark',
                },
            )
            if created:
                # Mark as passwordless (cannot login with password unless set later)
                user.set_unusable_password()
                user.save()

            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    },
                }
            )

        except Exception as exc:
            logger.exception('Google login failed: %s', exc)
            return Response(
                {'error': 'Google login failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        from .models import CreditHold
        from django.db.models import Sum
        
        user = self.get_object()
        serializer = self.get_serializer(user)
        data = serializer.data
        
        # Calculate held credits
        held_credits = CreditHold.objects.filter(
            user=user,
            status='hold'
        ).aggregate(total=Sum('credits_held'))['total'] or 0
        
        # Add held credits info
        data['held_credits'] = held_credits
        data['available_credits'] = user.credits - held_credits
        
        return Response(data)


class UserUpdateProfileView(generics.UpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UserDeleteAccountView(APIView):
    """Delete user account"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        try:
            user = request.user
            user_email = user.email
            
            # Delete user (this will cascade delete related objects)
            user.delete()
            
            logger.info(f"User account deleted: {user_email}")
            
            return Response({
                'message': 'Account deleted successfully'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Account deletion failed: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Account deletion failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VideoGenerationCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = VideoGenerationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        prompt = serializer.validated_data['prompt']
        tool = serializer.validated_data['tool']
        user_email = request.user.email
        
        logger.info(f"Video generation request - User: {user_email}, Tool: {tool}, Prompt: {prompt[:50]}...")
        
        try:
            options = serializer.validated_data.get('options', {})
            video_gen = VideoGenerationService.create_video_generation(
                user=request.user,
                prompt=prompt,
                tool=tool,
                options=options
            )
            
            logger.info(f"Video generation successful - User: {user_email}, Video ID: {video_gen.id}")
            
            return Response(
                VideoGenerationSerializer(video_gen).data,
                status=status.HTTP_201_CREATED
            )
        
        except ValueError as e:
            error_msg = str(e)
            logger.warning(f"Video generation validation error - User: {user_email}, Error: {error_msg}")
            
            # Check if it's an insufficient credits error
            if "Insufficient credits" in error_msg:
                # Get required credits for the tool
                tool_config = VideoGenerationService.get_tool_config(tool)
                required_credits = tool_config['credits'] if tool_config else 0
                
                return Response(
                    {
                        'error': error_msg,
                        'error_code': 'INSUFFICIENT_CREDITS',
                        'required_credits': required_credits,
                        'available_credits': request.user.credits,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            error_message = str(e)
            error_type = type(e).__name__
            logger.error(
                f"Video generation failed - User: {user_email}, Tool: {tool}, "
                f"Error Type: {error_type}, Error: {error_message}",
                exc_info=True
            )
            return Response(
                {
                    'error': 'Video generation failed',
                    'detail': error_message,
                    'error_type': error_type
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VideoGenerationListView(generics.ListAPIView):
    serializer_class = VideoGenerationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return VideoGeneration.objects.filter(user=self.request.user)


class VideoGenerationDetailView(generics.RetrieveAPIView):
    serializer_class = VideoGenerationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return VideoGeneration.objects.filter(user=self.request.user)


class ImageGenerationCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ImageGenerationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        prompt = serializer.validated_data['prompt']
        tool = serializer.validated_data['tool']
        user_email = request.user.email
        
        logger.info(f"Image generation request - User: {user_email}, Tool: {tool}, Prompt: {prompt[:50]}...")
        
        try:
            options = serializer.validated_data.get('options', {})
            image_gen = ImageGenerationService.create_image_generation(
                user=request.user,
                prompt=prompt,
                tool=tool,
                options=options
            )
            
            logger.info(f"Image generation successful - User: {user_email}, Image ID: {image_gen.id}")
            
            return Response(
                ImageGenerationSerializer(image_gen).data,
                status=status.HTTP_201_CREATED
            )
        
        except ValueError as e:
            error_msg = str(e)
            logger.warning(f"Image generation validation error - User: {user_email}, Error: {error_msg}")
            
            # Check if it's an insufficient credits error
            if "Insufficient credits" in error_msg:
                # Get required credits for the tool
                tool_config = ImageGenerationService.get_tool_config(tool)
                required_credits = tool_config['credits'] if tool_config else 0
                
                return Response(
                    {
                        'error': error_msg,
                        'error_code': 'INSUFFICIENT_CREDITS',
                        'required_credits': required_credits,
                        'available_credits': request.user.credits,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            error_message = str(e)
            error_type = type(e).__name__
            logger.error(
                f"Image generation failed - User: {user_email}, Tool: {tool}, "
                f"Error Type: {error_type}, Error: {error_message}",
                exc_info=True
            )
            return Response(
                {
                    'error': 'Image generation failed',
                    'detail': error_message,
                    'error_type': error_type
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ImageGenerationListView(generics.ListAPIView):
    serializer_class = ImageGenerationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ImageGeneration.objects.filter(user=self.request.user)


class ImageGenerationDetailView(generics.RetrieveAPIView):
    serializer_class = ImageGenerationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ImageGeneration.objects.filter(user=self.request.user)


class VideoToolsListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        from .services import TOOL_CONFIG
        
        tools = [
            {
                'id': key,
                'name': config['name'],
                'credits': config['credits'],
                'model': config['model'],
                'locked': True,  # Indicates price is locked and cannot be changed
            }
            for key, config in TOOL_CONFIG.items()
        ]
        
        return Response(tools)


class LockedPricingView(APIView):
    """
    Read-only endpoint to view locked pricing.
    Prices are FIXED and cannot be modified through this endpoint.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        from .constants import VIDEO_MODEL_CREDITS, IMAGE_MODEL_CREDITS
        from .services import VIDEO_TOOL_CONFIG, IMAGE_TOOL_CONFIG
        
        # Build response with locked prices
        video_pricing = []
        for tool_id, credits in VIDEO_MODEL_CREDITS.items():
            if tool_id in VIDEO_TOOL_CONFIG:
                video_pricing.append({
                    'id': tool_id,
                    'name': VIDEO_TOOL_CONFIG[tool_id]['name'],
                    'credits': credits,
                    'model': VIDEO_TOOL_CONFIG[tool_id]['model'],
                    'locked': True,
                    'category': 'video',
                })
        
        image_pricing = []
        for tool_id, credits in IMAGE_MODEL_CREDITS.items():
            if tool_id in IMAGE_TOOL_CONFIG:
                image_pricing.append({
                    'id': tool_id,
                    'name': IMAGE_TOOL_CONFIG[tool_id]['name'],
                    'credits': credits,
                    'model': IMAGE_TOOL_CONFIG[tool_id]['model'],
                    'locked': True,
                    'category': 'image',
                })
        
        return Response({
            'message': 'These prices are LOCKED and cannot be modified',
            'video_models': video_pricing,
            'image_models': image_pricing,
            'note': 'Prices can only be changed by code modification with owner approval',
        })


class SubscriptionPlansView(APIView):
    """Get available subscription plans"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        plans = []
        from .subscription_constants import SUBSCRIPTION_PLANS
        for plan_id, plan_config in SUBSCRIPTION_PLANS.items():
            plans.append({
                'id': plan_id,
                'name': plan_config['name'],
                'price': plan_config['price'],
                'currency': plan_config['currency'],
                'credits': plan_config['credits'],
                'period_days': plan_config['period_days'],
                'features': plan_config.get('features', []),
            })
        
        return Response(plans)


class SubscriptionCreateView(APIView):
    """Create a new subscription and payment"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        plan = request.data.get('plan') or request.data.get('plan_type')  # Support both
        auto_renew = request.data.get('auto_renew', True)
        payment_id = request.data.get('payment_id')  # From payment processor (if payment already completed)
        
        if not plan:
            return Response(
                {'error': 'plan_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from .subscription_constants import SUBSCRIPTION_PLANS
        if plan not in SUBSCRIPTION_PLANS:
            return Response(
                {'error': f'Invalid plan: {plan}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        plan_config = SUBSCRIPTION_PLANS[plan]
        
        try:
            # If payment_id is provided, payment is already completed (from webhook)
            if payment_id:
                subscription = SubscriptionService.create_subscription(
                    user=request.user,
                    plan_type=plan,
                    auto_renew=auto_renew,
                    payment_id=payment_id
                )
                
                subscription_info = SubscriptionService.get_subscription_info(request.user)
                
                return Response({
                    'message': 'Subscription created successfully',
                    'subscription': subscription_info,
                }, status=status.HTTP_201_CREATED)
            
            # Otherwise, create subscription (pending) and payment, then return payment URL
            from .payment_service import PaymentService
            
            # Create subscription in pending status (will be activated after payment via webhook)
            subscription = SubscriptionService.create_subscription(
                user=request.user,
                plan_type=plan,
                auto_renew=auto_renew,
                payment_id=None,  # Will be set after payment
            )
            # Subscription is already in pending status (not activated)
            
            # Create payment record linked to subscription
            payment, fees = PaymentService.create_payment(
                user=request.user,
                payment_type='subscription',
                amount=plan_config['price'],
                currency=plan_config.get('currency', '₼'),
                subscription=subscription,
            )
            
            # Process payment through E-point
            payment_obj, epoint_result = PaymentService.process_payment(payment.id)
            
            if not epoint_result.get('success'):
                return Response(
                    {'error': epoint_result.get('message', 'Payment creation failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # If this is a mock payment (TEST_MODE), auto-complete it
            from .payment_service import EPointService
            if EPointService.TEST_MODE or 'mock=true' in epoint_result.get('payment_url', ''):
                # Auto-complete mock payment
                try:
                    PaymentService.complete_payment(payment.id, epoint_result.get('transaction_id'))
                    subscription.refresh_from_db()
                    request.user.refresh_from_db()
                except Exception as e:
                    logger.warning(f"Mock payment auto-completion failed: {e}")
            
            # Return payment URL for redirect
            return Response({
                'subscription_id': subscription.id,
                'payment_id': payment.id,
                'payment_url': epoint_result.get('payment_url'),
                'transaction_id': epoint_result.get('transaction_id'),
                'message': 'Payment created. Redirect to payment_url to complete payment.',
            }, status=status.HTTP_200_OK)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Subscription creation failed: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Subscription creation failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubscriptionInfoView(APIView):
    """Get current user's subscription information"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        subscription_info = SubscriptionService.get_subscription_info(request.user)
        return Response(subscription_info)


class SubscriptionCancelView(APIView):
    """Cancel user's subscription"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            subscription = SubscriptionService.cancel_subscription(
                user=request.user
            )
            
            return Response({
                'message': 'Subscription cancelled successfully',
                'subscription_id': subscription.id,
            })
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Subscription cancellation failed: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Subscription cancellation failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TopUpPackagesView(APIView):
    """Get available top-up credit packages"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        packages = TopUpService.get_topup_packages()
        return Response(packages)


class TopUpCreateView(APIView):
    """Create a top-up credit purchase and payment"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        package = request.data.get('package')
        payment_id = request.data.get('payment_id')  # From payment processor (if payment already completed)
        
        if not package:
            return Response(
                {'error': 'package is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # If payment_id is provided, payment is already completed (from webhook)
            if payment_id:
                purchase, payment = TopUpService.create_topup(
                    user=request.user,
                    package=package,
                    payment_id=payment_id
                )
                
                # Complete the payment
                from .payment_service import PaymentService
                try:
                    PaymentService.complete_payment(payment.id, payment_id)
                    purchase.refresh_from_db()
                    request.user.refresh_from_db()
                except Exception as e:
                    logger.warning(f"Payment completion failed: {e}")
                
                return Response({
                    'message': 'Top-up purchase created successfully',
                    'purchase_id': purchase.id,
                    'payment_id': payment.id,
                    'status': purchase.status,
                    'credits': purchase.total_credits,
                    'user_credits': request.user.credits,
                    'payment_status': payment.status,
                }, status=status.HTTP_201_CREATED)
            
            # Otherwise, create purchase and payment, then return payment URL
            from .topup_constants import TOPUP_PACKAGES
            from .payment_service import PaymentService
            from .models import CreditPurchase
            
            package_config = TOPUP_PACKAGES.get(package)
            if not package_config:
                return Response(
                    {'error': f'Invalid package: {package}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create purchase record (pending, without payment_id yet)
            purchase = CreditPurchase.objects.create(
                user=request.user,
                package=package,
                status='pending',
                credits_purchased=package_config['credits'],
                bonus_credits=0,
                total_credits=package_config['credits'],
                price=package_config['price'],
                currency=package_config.get('currency', '₼'),
                payment_id=None,  # Will be set after payment is created
            )
            
            # Create payment record
            payment, fees = PaymentService.create_payment(
                user=request.user,
                payment_type='topup',
                amount=package_config['price'],
                currency=package_config.get('currency', '₼'),
                credit_purchase=purchase,
            )
            
            # Link payment to purchase
            purchase.payment_id = payment.id
            purchase.save()
            
            # Process payment through E-point
            payment_obj, epoint_result = PaymentService.process_payment(payment.id)
            
            if not epoint_result.get('success'):
                return Response(
                    {'error': epoint_result.get('message', 'Payment creation failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # If this is a mock payment (TEST_MODE), auto-complete it
            from .payment_service import EPointService
            if EPointService.TEST_MODE or 'mock=true' in epoint_result.get('payment_url', ''):
                # Auto-complete mock payment
                try:
                    PaymentService.complete_payment(payment.id, epoint_result.get('transaction_id'))
                    purchase.refresh_from_db()
                    request.user.refresh_from_db()
                except Exception as e:
                    logger.warning(f"Mock payment auto-completion failed: {e}")
            
            # Return payment URL for redirect
            return Response({
                'purchase_id': purchase.id,
                'payment_id': payment.id,
                'payment_url': epoint_result.get('payment_url'),
                'transaction_id': epoint_result.get('transaction_id'),
                'message': 'Payment created. Redirect to payment_url to complete payment.',
            }, status=status.HTTP_200_OK)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Top-up creation failed: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Top-up creation failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TopUpCompleteView(APIView):
    """Complete a pending top-up purchase (called after payment confirmation)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        purchase_id = request.data.get('purchase_id')
        payment_id = request.data.get('payment_id')
        
        if not purchase_id:
            return Response(
                {'error': 'purchase_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            purchase = TopUpService.complete_topup(purchase_id, payment_id)
            
            return Response({
                'message': 'Top-up purchase completed successfully',
                'purchase_id': purchase.id,
                'credits_added': purchase.total_credits,
                'user_credits': purchase.user.credits,
            })
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Top-up completion failed: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Top-up completion failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TopUpHistoryView(generics.ListAPIView):
    """Get user's top-up purchase history"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TopUpService.get_user_purchases(self.request.user)
    
    def list(self, request, *args, **kwargs):
        purchases = self.get_queryset()
        data = [
            {
                'id': p.id,
                'package': p.package,
                'status': p.status,
                'credits_purchased': p.credits_purchased,
                'bonus_credits': p.bonus_credits,
                'total_credits': p.total_credits,
                'price': float(p.price),
                'currency': p.currency,
                'created_at': p.created_at,
                'completed_at': p.completed_at,
            }
            for p in purchases
        ]
        return Response(data)


# E-point Payment Callback Views
class PaymentSuccessView(APIView):
    """Handle successful payment redirect from E-point"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """User is redirected here after successful payment"""
        from django.shortcuts import redirect
        
        transaction_id = request.GET.get('transaction_id')
        logger.info(f"Payment success callback - Transaction ID: {transaction_id}")
        
        # Redirect to frontend success page
        # Frontend will poll or check payment status
        from django.conf import settings
        frontend_url = f"{settings.FRONTEND_URL}/checkout/success?transaction_id={transaction_id}"
        return redirect(frontend_url)


class PaymentErrorView(APIView):
    """Handle failed payment redirect from E-point"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """User is redirected here after failed payment"""
        from django.shortcuts import redirect
        
        transaction_id = request.GET.get('transaction_id')
        error = request.GET.get('error', 'Unknown error')
        logger.warning(f"Payment error callback - Transaction ID: {transaction_id}, Error: {error}")
        
        # Redirect to frontend error page
        from django.conf import settings
        frontend_url = f"{settings.FRONTEND_URL}/checkout/cancel?transaction_id={transaction_id}&error={error}"
        return redirect(frontend_url)


class PaymentWebhookView(APIView):
    """Handle E-point webhook notifications (result callback)"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """E-point sends POST request here when payment status changes
        
        E-point sends 'data' (base64 encoded) and 'signature' parameters via POST
        as per documentation page 7 (Callback funksiyasının icra edilməsi)
        """
        from .payment_service import PaymentService, EPointService
        from .models import Payment
        
        try:
            # Get webhook parameters (data and signature from E-point)
            data_encoded = request.data.get('data') or request.POST.get('data')
            signature_received = request.data.get('signature') or request.POST.get('signature')
            
            if not data_encoded or not signature_received:
                logger.error(f"Payment webhook missing required parameters - data: {bool(data_encoded)}, signature: {bool(signature_received)}")
                return Response(
                    {'error': 'Missing required parameters: data and signature'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"Payment webhook received - Data length: {len(data_encoded)}, Signature: {signature_received[:20]}...")
            
            # Process webhook (verify signature and decode data)
            result = EPointService.process_webhook(data_encoded, signature_received)
            
            if not result.get('success'):
                logger.error(f"Webhook processing failed: {result.get('message')}")
                return Response(
                    {'error': result.get('message')},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get decoded webhook data
            webhook_data = result.get('data', {})
            transaction_id = webhook_data.get('transaction')  # E-point uses 'transaction' not 'transaction_id'
            payment_status = webhook_data.get('status')
            order_id = webhook_data.get('order_id')
            
            logger.info(f"Webhook decoded - Order: {order_id}, Transaction: {transaction_id}, Status: {payment_status}")
            
            # Find payment by order_id (our Payment ID) or E-point transaction ID
            payment = None
            try:
                # Try to find by order_id first (which is our Payment ID)
                if order_id:
                    payment = Payment.objects.get(id=order_id)
                # Fallback to E-point transaction ID
                elif transaction_id:
                    payment = Payment.objects.get(epoint_transaction_id=transaction_id)
                else:
                    raise Payment.DoesNotExist
                    
            except Payment.DoesNotExist:
                logger.error(f"Payment not found - Order ID: {order_id}, Transaction: {transaction_id}")
                return Response(
                    {'error': 'Payment not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Update payment with E-point transaction ID if not set
            if transaction_id and not payment.epoint_transaction_id:
                payment.epoint_transaction_id = transaction_id
                payment.save()
            
            # Complete payment if status is 'success'
            if payment_status == 'success':
                PaymentService.complete_payment(payment.id, transaction_id)
                logger.info(f"Payment completed via webhook - Payment ID: {payment.id}")
            elif payment_status in ['failed', 'error']:
                payment.status = 'failed'
                payment.notes = f"Payment {payment_status} via E-point - {webhook_data.get('message', '')}"
                payment.save()
                logger.warning(f"Payment failed via webhook - Payment ID: {payment.id}")
            else:
                # Other statuses: new, returned, server_error
                logger.info(f"Payment status update via webhook - Payment ID: {payment.id}, Status: {payment_status}")
            
            return Response({
                'success': True,
                'message': 'Webhook processed',
            })
            
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Webhook processing failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )