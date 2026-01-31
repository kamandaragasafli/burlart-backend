import logging
import fal_client
from django.conf import settings
from .models import VideoGeneration, ImageGeneration, Subscription, CreditPurchase, Payment, CreditHold
from django.db import models

logger = logging.getLogger(__name__)

# ============================================================================
# LOCKED PRICING CONFIGURATION - DO NOT MODIFY
# ============================================================================
# These prices are FIXED and LOCKED. They cannot be changed from admin panel
# or any API endpoint. Only the owner can modify these by changing the code.
# 
# Video tool configuration with credits and model IDs (5 seconds video)
# ============================================================================
VIDEO_TOOL_CONFIG = {
    'pika': {
        'credits': 52,
        'model': 'fal-ai/pika/v2.2/text-to-video',
        'name': 'Pika Labs',
        'has_sound': False
    },
    'seedance': {
        'credits': 39,
        'model': 'fal-ai/bytedance/seedance/v1/pro/fast/text-to-video',
        'name': 'Seedance',
        'has_sound': True
    },
    'wan': {
        'credits': 24,
        'model': 'wan/v2.6/text-to-video',
        'name': 'Wan',
        'has_sound': False
    },
    'luma': {
        'credits': 32,
        'model': 'fal-ai/luma-photon/text-to-video',
        'name': 'Luma AI',
        'has_sound': True
    },
    'kling': {
        'credits': 55,
        'model': 'fal-ai/kling-video/v2.5-turbo/pro/text-to-video',
        'name': 'Kling AI',
        'has_sound': True
    },
    'veo': {
        'credits': 238,
        'model': 'fal-ai/veo3',
        'name': 'Veo',
        'has_sound': True
    },
    'sora': {
        'credits': 79,
        'model': 'fal-ai/sora-2/text-to-video',
        'name': 'Sora',
        'has_sound': False
    },
}

# ============================================================================
# LOCKED PRICING - Image tool configuration with credits and model IDs
# ============================================================================
IMAGE_TOOL_CONFIG = {
    'gpt-image': {
        'credits': 16,
        'model': 'fal-ai/gpt-image-1.5',
        'name': 'GPT Image',
    },
    'nano-banana': {
        'credits': 47,
        'model': 'fal-ai/nano-banana-pro',
        'name': 'Nano Banana',
    },
    'seedream': {
        'credits': 6,
        'model': 'fal-ai/bytedance/seedream/v4.5/text-to-image',
        'name': 'Seedream',
    },
    'flux': {
        'credits': 6,
        'model': 'fal-ai/flux-2-pro',
        'name': 'Flux',
    },
    'z-image': {
        'credits': 2,
        'model': 'fal-ai/z-image/turbo/lora',
        'name': 'Z-Image',
    },
    'qwen': {
        'credits': 6,
        'model': 'fal-ai/qwen-image-2512',
        'name': 'Qwen',
    },
    'gpt-image-edit': {
        'credits': 16,
        'model': 'fal-ai/gpt-image-1.5/edit',
        'name': 'GPT Image Edit',
    },
    'nano-banana-edit': {
        'credits': 47,
        'model': 'fal-ai/nano-banana/edit',
        'name': 'Nano Banana Edit',
    },
    'seedream-edit': {
        'credits': 7,
        'model': 'fal-ai/bytedance/seedream/v4.5/edit',
        'name': 'Seedream Edit',
    },
    'flux-edit': {
        'credits': 6,
        'model': 'fal-ai/flux-2-pro/edit',
        'name': 'Flux Edit',
    },
    'qwen-max-edit': {
        'credits': 6,
        'model': 'fal-ai/qwen-image-max/edit',
        'name': 'Qwen Max Edit',
    },
}

# ============================================================================
# LOCKED PRICING - Image-to-Video tool configuration with credits and model IDs
# ============================================================================
IMAGE_TO_VIDEO_TOOL_CONFIG = {
    'sora-i2v': {
        'credits': 79,
        'model': 'fal-ai/sora-2/image-to-video',
        'name': 'Sora (Image-to-Video)',
        'has_sound': False,
        'requires_image': True
    },
    'veo-i2v': {
        'credits': 238,
        'model': 'fal-ai/veo3/image-to-video',
        'name': 'Veo (Image-to-Video)',
        'has_sound': True,
        'requires_image': True
    },
    'kling-i2v': {
        'credits': 55,
        'model': 'fal-ai/kling-video/v2.5-turbo/pro/image-to-video',
        'name': 'Kling AI (Image-to-Video)',
        'has_sound': True,
        'requires_image': True
    },
    'luma-i2v': {
        'credits': 32,
        'model': 'fal-ai/luma-photon/image-to-video',
        'name': 'Luma Photon (Image-to-Video)',
        'has_sound': True,
        'requires_image': True
    },
    'seedance-i2v': {
        'credits': 98,
        'model': 'fal-ai/bytedance/seedance/v1/pro/fast/image-to-video',
        'name': 'Seedance (Image-to-Video)',
        'has_sound': True,
        'requires_image': True
    },
    'pika-i2v': {
        'credits': 71,
        'model': 'fal-ai/pika/v2.2/image-to-video',
        'name': 'Pika Labs (Image-to-Video)',
        'has_sound': False,
        'requires_image': True
    },
    'gpt-image-i2v': {
        'credits': 16,
        'model': 'fal-ai/gpt-image-1.5/image-to-video',
        'name': 'GPT Image (Image-to-Video)',
        'has_sound': False,
        'requires_image': True
    },
    'nano-banana-i2v': {
        'credits': 47,
        'model': 'fal-ai/nano-banana-pro/image-to-video',
        'name': 'Nano Banana (Image-to-Video)',
        'has_sound': False,
        'requires_image': True
    },
    'seedream-i2v': {
        'credits': 6,
        'model': 'fal-ai/seedream/v4.5/image-to-video',
        'name': 'Seedream (Image-to-Video)',
        'has_sound': False,
        'requires_image': True
    },
    'flux-i2v': {
        'credits': 6,
        'model': 'fal-ai/flux-2-pro/image-to-video',
        'name': 'Flux (Image-to-Video)',
        'has_sound': False,
        'requires_image': True
    },
    'z-image-i2v': {
        'credits': 2,
        'model': 'fal-ai/z-image/turbo/lora/image-to-video',
        'name': 'Z-Image (Image-to-Video)',
        'has_sound': False,
        'requires_image': True
    },
    'qwen-i2v': {
        'credits': 6,
        'model': 'fal-ai/qwen-image-2512/image-to-video',
        'name': 'Qwen (Image-to-Video)',
        'has_sound': False,
        'requires_image': True
    },
}

# Combined tool config for backward compatibility
TOOL_CONFIG = {**VIDEO_TOOL_CONFIG, **IMAGE_TOOL_CONFIG, **IMAGE_TO_VIDEO_TOOL_CONFIG}

# Validate locked prices after all configs are defined
def _validate_locked_prices():
    """Internal function to validate locked prices"""
    from .constants import validate_locked_prices
    try:
        validate_locked_prices(VIDEO_TOOL_CONFIG, IMAGE_TOOL_CONFIG, IMAGE_TO_VIDEO_TOOL_CONFIG)
        logger.info("Locked pricing validation passed")
    except ValueError as e:
        logger.error(f"LOCKED PRICING VALIDATION FAILED: {e}")
        raise

# Run validation
_validate_locked_prices()


class VideoGenerationService:
    @staticmethod
    def get_tool_config(tool_name):
        """Get tool configuration by tool name - supports both text-to-video and image-to-video"""
        # Check text-to-video first
        config = VIDEO_TOOL_CONFIG.get(tool_name)
        if config:
            return config
        # Check image-to-video
        return IMAGE_TO_VIDEO_TOOL_CONFIG.get(tool_name)
    
    @staticmethod
    def create_video_generation(user, prompt, tool, options=None):
        """Create a video generation request"""
        if options is None:
            options = {}
        
        logger.info(f"Starting video generation - User: {user.email}, Tool: {tool}, Options: {options}")
        
        tool_config = VideoGenerationService.get_tool_config(tool)
        
        if not tool_config:
            logger.error(f"Invalid tool requested: {tool}")
            raise ValueError(f"Invalid tool: {tool}")
        
        logger.info(f"Tool config - Model: {tool_config['model']}, Credits: {tool_config['credits']}")
        
        # Check if user has enough credits (including held credits)
        required_credits = tool_config['credits']
        available_credits = user.credits
        
        # Calculate held credits (not yet confirmed or released)
        held_credits = CreditHold.objects.filter(
            user=user,
            status='hold'
        ).aggregate(total=models.Sum('credits_held'))['total'] or 0
        
        # Available credits = current balance - held credits
        actually_available = available_credits - held_credits
        
        if actually_available < required_credits:
            logger.warning(
                f"Insufficient credits - User: {user.email}, "
                f"Required: {required_credits}, "
                f"Available: {available_credits}, "
                f"Held: {held_credits}, "
                f"Actually Available: {actually_available}"
            )
            raise ValueError(f"Insufficient credits. Required: {required_credits}, Available: {actually_available}")
        
        # Create video generation record first
        video_gen = VideoGeneration.objects.create(
            user=user,
            prompt=prompt,
            tool=tool,
            model_id=tool_config['model'],
            credits_used=required_credits,
            status='pending'
        )
        logger.info(f"Video generation record created - ID: {video_gen.id}")
        
        # HOLD credits (deduct from available balance, but mark as held)
        user.credits -= required_credits
        user.save()
        
        # Create credit hold record
        credit_hold = CreditHold.objects.create(
            user=user,
            transaction_type='video',
            video_generation=video_gen,
            credits_held=required_credits,
            status='hold'
        )
        logger.info(f"Credits held - User: {user.email}, Amount: {required_credits}, Hold ID: {credit_hold.id}, Remaining: {user.credits}")
        
        try:
            logger.info(f"Submitting to fal.ai - Model: {tool_config['model']}, Prompt length: {len(prompt)}")
            
            # Check if FAL_KEY is set
            if not hasattr(settings, 'FAL_KEY') or not settings.FAL_KEY:
                raise ValueError("FAL_KEY is not configured in settings")
            
            # Prepare arguments for fal.ai
            arguments = {
                "prompt": prompt
            }
            
            # Add reference image if provided (for image-to-video models)
            if options.get('referenceImage'):
                arguments['image_url'] = options['referenceImage']
                logger.info(f"Adding reference image for image-to-video: {options['referenceImage'][:100]}...")
            
            # Add negative prompt if provided
            if options.get('negativePrompt'):
                arguments['negative_prompt'] = options['negativePrompt']
            
            # Add seed if provided
            if options.get('seed'):
                arguments['seed'] = int(options['seed'])
            
            # Handle sound/audio
            sound_enabled = options.get('soundEnabled', tool_config.get('has_sound', False))
            if sound_enabled:
                model_name = tool_config['model']
                if 'seedance' in model_name.lower() or 'bytedance' in model_name.lower():
                    arguments['enable_audio'] = True
                elif 'kling' in model_name.lower():
                    arguments['audio'] = True
                elif 'luma' in model_name.lower():
                    arguments['enable_audio'] = True
                elif 'veo' in model_name.lower() or 'veo3' in model_name.lower():
                    arguments['enable_audio'] = True
                else:
                    arguments['enable_audio'] = True
                logger.info(f"Audio enabled for tool: {tool}")
            
            # Add resolution
            if options.get('resolution'):
                if options['resolution'] == '1080p':
                    arguments['resolution'] = '1080p'
                else:
                    arguments['resolution'] = '720p'
            
            # Add duration/length
            if options.get('duration'):
                arguments['duration'] = options['duration']
            
            # Add version if applicable (for Veo)
            if tool == 'veo':
                if options.get('version') == 'fast':
                    # Veo 3.1 Fast
                    arguments['version'] = '3.1-fast'
                else:
                    arguments['version'] = '3.1'
                
                if options.get('characterReference'):
                    arguments['character_reference'] = True
            
            logger.info(f"Fal.ai arguments: {arguments}")
            
            # Submit to fal.ai
            handler = fal_client.submit(
                tool_config['model'],
                arguments=arguments
            )
            
            logger.info(f"Request submitted to fal.ai - Request ID: {handler.request_id}")
            
            # Store the request ID
            video_gen.fal_request_id = handler.request_id
            video_gen.status = 'processing'
            video_gen.save()
            
            # Get the result (this will wait for completion)
            logger.info(f"Waiting for result - Request ID: {handler.request_id}")
            result = handler.get()
            logger.info(f"Result received - Request ID: {handler.request_id}, Result keys: {list(result.keys()) if result else 'None'}")
            
            # Update with result
            if result and 'video' in result:
                video_gen.video_url = result['video']['url']
                video_gen.status = 'completed'
                logger.info(f"Video generation completed - ID: {video_gen.id}, URL: {video_gen.video_url}")
                
                # CONFIRM credit hold (credits are permanently deducted)
                try:
                    credit_hold = CreditHold.objects.get(video_generation=video_gen, status='hold')
                    credit_hold.confirm()
                    logger.info(f"Credit hold confirmed - Hold ID: {credit_hold.id}")
                except CreditHold.DoesNotExist:
                    logger.warning(f"No credit hold found for video generation {video_gen.id}")
            else:
                video_gen.status = 'failed'
                video_gen.error_message = f"No video URL in response. Result keys: {list(result.keys()) if result else 'None'}"
                logger.error(f"No video in result - ID: {video_gen.id}, Result: {result}")
                
                # RELEASE credit hold (return credits to user)
                try:
                    credit_hold = CreditHold.objects.get(video_generation=video_gen, status='hold')
                    credit_hold.release()
                    logger.info(f"Credit hold released - Hold ID: {credit_hold.id}, Credits returned")
                except CreditHold.DoesNotExist:
                    logger.warning(f"No credit hold found for video generation {video_gen.id}")
            
            video_gen.save()
            
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            logger.error(
                f"Video generation exception - User: {user.email}, Tool: {tool}, "
                f"Video ID: {video_gen.id}, Error Type: {error_type}, Error: {error_message}",
                exc_info=True
            )
            
            # RELEASE credit hold (return credits to user)
            try:
                credit_hold = CreditHold.objects.get(video_generation=video_gen, status='hold')
                credit_hold.release()
                logger.info(f"Credit hold released due to error - Hold ID: {credit_hold.id}, Credits returned")
            except CreditHold.DoesNotExist:
                logger.warning(f"No credit hold found for video generation {video_gen.id}")
            
            video_gen.status = 'failed'
            video_gen.error_message = f"{error_type}: {error_message}"
            video_gen.save()
            
            raise
        
        return video_gen
    
    @staticmethod
    def get_user_videos(user):
        """Get all videos for a user"""
        return VideoGeneration.objects.filter(user=user)


class ImageGenerationService:
    @staticmethod
    def get_tool_config(tool_name):
        """Get tool configuration by tool name"""
        return IMAGE_TOOL_CONFIG.get(tool_name)
    
    @staticmethod
    def create_image_generation(user, prompt, tool, options=None):
        """Create an image generation request"""
        if options is None:
            options = {}
        
        logger.info(f"Starting image generation - User: {user.email}, Tool: {tool}, Options: {options}")
        
        tool_config = ImageGenerationService.get_tool_config(tool)
        
        if not tool_config:
            logger.error(f"Invalid tool requested: {tool}")
            raise ValueError(f"Invalid tool: {tool}")
        
        logger.info(f"Tool config - Model: {tool_config['model']}, Credits: {tool_config['credits']}")
        
        # Check if user has enough credits (including held credits)
        required_credits = tool_config['credits']
        available_credits = user.credits
        
        # Calculate held credits (not yet confirmed or released)
        held_credits = CreditHold.objects.filter(
            user=user,
            status='hold'
        ).aggregate(total=models.Sum('credits_held'))['total'] or 0
        
        # Available credits = current balance - held credits
        actually_available = available_credits - held_credits
        
        if actually_available < required_credits:
            logger.warning(
                f"Insufficient credits - User: {user.email}, "
                f"Required: {required_credits}, "
                f"Available: {available_credits}, "
                f"Held: {held_credits}, "
                f"Actually Available: {actually_available}"
            )
            raise ValueError(f"Insufficient credits. Required: {required_credits}, Available: {actually_available}")
        
        # Create image generation record first
        image_gen = ImageGeneration.objects.create(
            user=user,
            prompt=prompt,
            tool=tool,
            model_id=tool_config['model'],
            credits_used=required_credits,
            status='pending'
        )
        logger.info(f"Image generation record created - ID: {image_gen.id}")
        
        # HOLD credits (deduct from available balance, but mark as held)
        user.credits -= required_credits
        user.save()
        
        # Create credit hold record
        credit_hold = CreditHold.objects.create(
            user=user,
            transaction_type='image',
            image_generation=image_gen,
            credits_held=required_credits,
            status='hold'
        )
        logger.info(f"Credits held - User: {user.email}, Amount: {required_credits}, Hold ID: {credit_hold.id}, Remaining: {user.credits}")
        
        try:
            logger.info(f"Submitting to fal.ai - Model: {tool_config['model']}, Prompt length: {len(prompt)}")
            
            # Check if FAL_KEY is set
            if not hasattr(settings, 'FAL_KEY') or not settings.FAL_KEY:
                raise ValueError("FAL_KEY is not configured in settings")
            
            # Prepare arguments for fal.ai
            arguments = {
                "prompt": prompt
            }
            
            # Add negative prompt if provided
            if options.get('negativePrompt'):
                arguments['negative_prompt'] = options['negativePrompt']
            
            # Add seed if provided
            if options.get('seed'):
                arguments['seed'] = int(options['seed'])
            
            logger.info(f"Fal.ai arguments: {arguments}")
            
            # Submit to fal.ai
            handler = fal_client.submit(
                tool_config['model'],
                arguments=arguments
            )
            
            logger.info(f"Request submitted to fal.ai - Request ID: {handler.request_id}")
            
            # Store the request ID
            image_gen.fal_request_id = handler.request_id
            image_gen.status = 'processing'
            image_gen.save()
            
            # Get the result (this will wait for completion)
            logger.info(f"Waiting for result - Request ID: {handler.request_id}")
            result = handler.get()
            logger.info(f"Result received - Request ID: {handler.request_id}, Result keys: {list(result.keys()) if result else 'None'}")
            
            # Update with result
            if result and 'images' in result:
                # Some models return 'images' array
                if isinstance(result['images'], list) and len(result['images']) > 0:
                    image_gen.image_url = result['images'][0].get('url') if isinstance(result['images'][0], dict) else result['images'][0]
                else:
                    image_gen.image_url = result['images']
                image_gen.status = 'completed'
                logger.info(f"Image generation completed - ID: {image_gen.id}, URL: {image_gen.image_url}")
                
                # CONFIRM credit hold (credits are permanently deducted)
                try:
                    credit_hold = CreditHold.objects.get(image_generation=image_gen, status='hold')
                    credit_hold.confirm()
                    logger.info(f"Credit hold confirmed - Hold ID: {credit_hold.id}")
                except CreditHold.DoesNotExist:
                    logger.warning(f"No credit hold found for image generation {image_gen.id}")
            elif result and 'image' in result:
                # Some models return 'image' object
                if isinstance(result['image'], dict):
                    image_gen.image_url = result['image'].get('url')
                else:
                    image_gen.image_url = result['image']
                image_gen.status = 'completed'
                logger.info(f"Image generation completed - ID: {image_gen.id}, URL: {image_gen.image_url}")
                
                # CONFIRM credit hold (credits are permanently deducted)
                try:
                    credit_hold = CreditHold.objects.get(image_generation=image_gen, status='hold')
                    credit_hold.confirm()
                    logger.info(f"Credit hold confirmed - Hold ID: {credit_hold.id}")
                except CreditHold.DoesNotExist:
                    logger.warning(f"No credit hold found for image generation {image_gen.id}")
            else:
                image_gen.status = 'failed'
                image_gen.error_message = f"No image URL in response. Result keys: {list(result.keys()) if result else 'None'}"
                logger.error(f"No image in result - ID: {image_gen.id}, Result: {result}")
                
                # RELEASE credit hold (return credits to user)
                try:
                    credit_hold = CreditHold.objects.get(image_generation=image_gen, status='hold')
                    credit_hold.release()
                    logger.info(f"Credit hold released - Hold ID: {credit_hold.id}, Credits returned")
                except CreditHold.DoesNotExist:
                    logger.warning(f"No credit hold found for image generation {image_gen.id}")
            
            image_gen.save()
            
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            logger.error(
                f"Image generation exception - User: {user.email}, Tool: {tool}, "
                f"Image ID: {image_gen.id}, Error Type: {error_type}, Error: {error_message}",
                exc_info=True
            )
            
            # RELEASE credit hold (return credits to user)
            try:
                credit_hold = CreditHold.objects.get(image_generation=image_gen, status='hold')
                credit_hold.release()
                logger.info(f"Credit hold released due to error - Hold ID: {credit_hold.id}, Credits returned")
            except CreditHold.DoesNotExist:
                logger.warning(f"No credit hold found for image generation {image_gen.id}")
            
            image_gen.status = 'failed'
            image_gen.error_message = f"{error_type}: {error_message}"
            image_gen.save()
            
            raise
        
        return image_gen
    
    @staticmethod
    def get_user_images(user):
        """Get all images for a user"""
        return ImageGeneration.objects.filter(user=user)


class SubscriptionService:
    @staticmethod
    def create_subscription(user, plan, auto_renew=True, payment_id=None):
        """Create a new subscription for user"""
        from django.utils import timezone
        from datetime import timedelta
        from .subscription_constants import SUBSCRIPTION_PLANS
        
        logger.info(f"Creating subscription - User: {user.email}, Plan: {plan}")
        
        # Check if user already has an active subscription
        try:
            existing_sub = user.subscription
            if existing_sub and existing_sub.is_active():
                logger.warning(f"User {user.email} already has active subscription")
                raise ValueError("User already has an active subscription")
        except Subscription.DoesNotExist:
            pass
        
        # Validate plan
        plan_config = SUBSCRIPTION_PLANS.get(plan)
        if not plan_config:
            raise ValueError(f"Invalid plan: {plan}")
        
        # Create subscription
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            status='active',
            auto_renew=auto_renew,
            next_renewal_date=timezone.now() + timedelta(days=30),
            payment_id=payment_id,
        )
        
        # Grant initial credits (NO ROLLOVER - reset to monthly amount)
        monthly_credits = plan_config['credits']
        user.credits = monthly_credits
        user.save()
        
        logger.info(f"Subscription created - ID: {subscription.id}, Credits granted: {monthly_credits}")
        
        return subscription
    
    @staticmethod
    def get_subscription_info(user):
        """Get subscription information for user"""
        from .subscription_constants import SUBSCRIPTION_PLANS
        
        try:
            subscription = user.subscription
            plan_config = SUBSCRIPTION_PLANS.get(subscription.plan, {})
            
            return {
                'has_subscription': True,
                'plan': subscription.plan,
                'plan_name': plan_config.get('name', subscription.plan),
                'status': subscription.status,
                'auto_renew': subscription.auto_renew,
                'start_date': subscription.start_date,
                'next_renewal_date': subscription.next_renewal_date,
                'is_active': subscription.is_active(),
                'monthly_credits': plan_config.get('credits', 0),
            }
        except Subscription.DoesNotExist:
            return {
                'has_subscription': False,
                'plan': None,
                'status': None,
                'auto_renew': False,
                'is_active': False,
            }
    
    @staticmethod
    def cancel_subscription(user, subscription_id=None):
        """Cancel user's subscription, reset credits, and cancel top-ups"""
        from .models import CreditPurchase, CreditHold
        
        try:
            subscription = user.subscription
            subscription.cancel()
            
            # Reset user credits to 0
            user.credits = 0
            user.save()
            logger.info(f"User credits reset to 0 - User: {user.email}")
            
            # Cancel all pending top-up purchases
            pending_topups = CreditPurchase.objects.filter(
                user=user,
                status__in=['pending', 'processing']
            )
            cancelled_count = pending_topups.update(status='cancelled')
            logger.info(f"Cancelled {cancelled_count} pending top-up purchases - User: {user.email}")
            
            # Release all held credits
            held_credits = CreditHold.objects.filter(
                user=user,
                status='hold'
            )
            held_count = held_credits.update(status='released')
            logger.info(f"Released {held_count} held credits - User: {user.email}")
            
            logger.info(f"Subscription cancelled - User: {user.email}, Subscription ID: {subscription.id}")
            return subscription
        except Subscription.DoesNotExist:
            raise ValueError("No active subscription found")
    
    @staticmethod
    def renew_expired_subscriptions():
        """
        Renew all expired subscriptions that have auto_renew enabled.
        Attempts payment through E-point for each subscription.
        """
        from django.utils import timezone
        
        logger.info("Starting subscription renewal process")
        
        # Find all subscriptions that need renewal (period_end reached)
        now = timezone.now()
        expired_subscriptions = Subscription.objects.filter(
            status='active',
            auto_renew=True
        ).filter(
            models.Q(period_end__lte=now) | models.Q(next_renewal_date__lte=now)
        )
        
        renewed_count = 0
        failed_count = 0
        pending_payments = []
        
        for subscription in expired_subscriptions:
            try:
                # Attempt payment
                success, payment, redirect_url = subscription.attempt_renewal_payment()
                
                if success:
                    renewed_count += 1
                    logger.info(f"Subscription renewed - User: {subscription.user.email}, Plan: {subscription.plan}")
                elif redirect_url:
                    # Payment redirect needed
                    pending_payments.append({
                        'subscription_id': subscription.id,
                        'user': subscription.user.email,
                        'payment_id': payment.id,
                        'redirect_url': redirect_url,
                    })
                    logger.info(f"Payment redirect needed - User: {subscription.user.email}, Payment ID: {payment.id}")
                else:
                    # Payment failed
                    failed_count += 1
                    logger.warning(f"Subscription renewal payment failed - User: {subscription.user.email}, Payment ID: {payment.id if payment else 'N/A'}")
            except Exception as e:
                failed_count += 1
                logger.error(f"Error renewing subscription - User: {subscription.user.email}, Error: {str(e)}", exc_info=True)
        
        logger.info(f"Subscription renewal completed - Renewed: {renewed_count}, Failed: {failed_count}, Pending: {len(pending_payments)}")
        
        return {
            'renewed': renewed_count,
            'failed': failed_count,
            'pending_payments': pending_payments,
        }


class TopUpService:
    @staticmethod
    def create_topup(user, package, payment_id=None):
        """Create a top-up credit purchase with payment record"""
        from .topup_constants import TOPUP_PACKAGES
        from .payment_service import PaymentService
        
        logger.info(f"Creating top-up - User: {user.email}, Package: {package}")
        
        # Validate package
        package_config = TOPUP_PACKAGES.get(package)
        if not package_config:
            raise ValueError(f"Invalid package: {package}")
        
        # Calculate total credits
        credits_purchased = package_config['credits']
        total_credits = credits_purchased  # No bonus for new packages
        
        # Create purchase record
        purchase = CreditPurchase.objects.create(
            user=user,
            package=package,
            status='pending',
            credits_purchased=credits_purchased,
            bonus_credits=0,  # No bonus for new packages
            total_credits=total_credits,
            price=package_config['price'],
            currency=package_config['currency'],
            payment_id=payment_id,
        )
        
        # Create payment record with fee calculation
        payment, fees = PaymentService.create_payment(
            user=user,
            payment_type='topup',
            amount=package_config['price'],
            currency=package_config['currency'],
            credit_purchase=purchase,
        )
        
        logger.info(f"Top-up created - ID: {purchase.id}, Credits: {total_credits}, Payment ID: {payment.id}, Fees: {fees}")
        
        return purchase, payment
    
    @staticmethod
    def complete_topup(purchase_id, payment_id=None):
        """Complete a top-up purchase and add credits to user"""
        from .payment_service import PaymentService
        
        try:
            purchase = CreditPurchase.objects.get(id=purchase_id, status='pending')
        except CreditPurchase.DoesNotExist:
            raise ValueError(f"Purchase not found or already processed: {purchase_id}")
        
        # Get related payment
        payment = Payment.objects.filter(credit_purchase=purchase).first()
        
        if payment:
            # Complete payment (which will complete the purchase)
            PaymentService.complete_payment(payment.id, payment_id)
        else:
            # Fallback: Complete purchase directly (for backward compatibility)
            if payment_id:
                purchase.payment_id = payment_id
            
            if purchase.complete():
                logger.info(f"Top-up completed - ID: {purchase.id}, User: {purchase.user.email}, Credits added: {purchase.total_credits}")
                return purchase
            else:
                raise ValueError("Purchase could not be completed")
        
        purchase.refresh_from_db()
        return purchase
    
    @staticmethod
    def get_topup_packages():
        """Get all available top-up packages"""
        from .topup_constants import TOPUP_PACKAGES
        
        packages = []
        for package_id, config in TOPUP_PACKAGES.items():
            packages.append({
                'id': package_id,
                'name': config['name'],
                'price': config['price'],
                'currency': config['currency'],
                'credits': config['credits'],
                'bonus_credits': 0,  # No bonus for new packages
                'total_credits': config['credits'],  # No bonus for new packages
                'popular': config.get('popular', False),
                'locked': True,  # Prices are locked
            })
        
        return packages
    
    @staticmethod
    def get_user_purchases(user):
        """Get all credit purchases for a user"""
        return CreditPurchase.objects.filter(user=user).order_by('-created_at')

