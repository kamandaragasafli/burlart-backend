from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    credits = models.IntegerField(default=0)
    language = models.CharField(max_length=5, default='en')
    theme = models.CharField(max_length=10, default='dark')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()
    
    def __str__(self):
        return self.email
    
    @property
    def active_subscription(self):
        """Get active subscription if exists"""
        try:
            sub = self.subscription
            if sub and sub.is_active():
                return sub
        except:
            pass
        return None
    
    @property
    def monthly_credits(self):
        """Get monthly credits from active subscription"""
        subscription = self.active_subscription
        if subscription:
            from .subscription_constants import SUBSCRIPTION_PLANS
            return SUBSCRIPTION_PLANS.get(subscription.plan, {}).get('credits', 0)
        return 0


class VideoGeneration(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    TOOL_CHOICES = [
        ('pika', 'Pika Labs'),
        ('seedance', 'Seedance'),
        ('wan', 'Wan'),
        ('luma', 'Luma AI'),
        ('kling', 'Kling AI'),
        ('veo', 'Veo'),
        ('sora', 'Sora'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
    prompt = models.TextField()
    tool = models.CharField(max_length=20, choices=TOOL_CHOICES)
    model_id = models.CharField(max_length=200)
    credits_used = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    video_url = models.URLField(blank=True, null=True)
    fal_request_id = models.CharField(max_length=200, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.tool} - {self.status}"


class ImageGeneration(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    TOOL_CHOICES = [
        ('gpt-image', 'GPT Image'),
        ('nano-banana', 'Nano Banana'),
        ('seedream', 'Seedream'),
        ('flux', 'Flux'),
        ('z-image', 'Z-Image'),
        ('qwen', 'Qwen'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='images')
    prompt = models.TextField()
    tool = models.CharField(max_length=20, choices=TOOL_CHOICES)
    model_id = models.CharField(max_length=200)
    credits_used = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    image_url = models.URLField(blank=True, null=True)
    fal_request_id = models.CharField(max_length=200, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.tool} - {self.status}"


class Subscription(models.Model):
    """
    Subscription model for monthly packages
    Supports auto-renewal and credit rollover management
    """
    PLAN_CHOICES = [
        ('demo', 'Demo'),
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('agency', 'Agency'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('pending', 'Pending'),
        ('past_due', 'Past Due'),  # Payment failed, grace period
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    auto_renew = models.BooleanField(default=True)
    
    # Dates
    start_date = models.DateTimeField(auto_now_add=True)
    period_start = models.DateTimeField(null=True, blank=True)  # Current billing period start
    period_end = models.DateTimeField(null=True, blank=True)  # Current billing period end (next_renewal_date)
    next_renewal_date = models.DateTimeField(null=True, blank=True)  # Alias for period_end (for backward compatibility)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    last_renewed_at = models.DateTimeField(null=True, blank=True)
    
    # Payment info
    payment_id = models.CharField(max_length=200, blank=True, null=True)
    payment_provider = models.CharField(max_length=50, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.plan} - {self.status}"
    
    def is_active(self):
        """Check if subscription is currently active"""
        period_end = self.period_end or self.next_renewal_date
        return (
            self.status == 'active' and 
            period_end and
            period_end > timezone.now()
        )
    
    def activate(self):
        """Activate subscription and set billing period"""
        from datetime import timedelta
        
        self.status = 'active'
        now = timezone.now()
        self.period_start = now
        self.period_end = now + timedelta(days=30)
        self.next_renewal_date = self.period_end  # Keep for backward compatibility
        self.save()
    
    def renew(self):
        """
        Renew subscription and add monthly credits.
        Credit rollover: NO ROLLOVER - credits reset to monthly amount.
        This method is called by auto-renewal process.
        """
        from .subscription_constants import SUBSCRIPTION_PLANS
        from datetime import timedelta
        
        if not self.auto_renew:
            self.status = 'expired'
            self.save()
            return False
        
        # Get plan credits
        plan_config = SUBSCRIPTION_PLANS.get(self.plan)
        if not plan_config:
            return False
        
        # NO ROLLOVER - Reset credits to monthly amount (old unused credits are lost)
        monthly_credits = plan_config['credits']
        self.user.credits = monthly_credits  # Reset, not add
        self.user.save()
        
        # Update billing period (next month)
        now = timezone.now()
        self.period_start = now
        self.period_end = now + timedelta(days=30)
        self.next_renewal_date = self.period_end  # Keep for backward compatibility
        self.last_renewed_at = now
        self.status = 'active'
        self.save()
        
        return True
    
    def attempt_renewal_payment(self):
        """
        Attempt to renew subscription with payment.
        Returns (success: bool, payment: Payment or None)
        """
        from .subscription_constants import SUBSCRIPTION_PLANS
        from .payment_service import PaymentService, EPointService
        
        plan_config = SUBSCRIPTION_PLANS.get(self.plan)
        if not plan_config:
            return False, None
        
        amount = plan_config['price']
        
        # Create payment record
        payment, fees = PaymentService.create_payment(
            user=self.user,
            payment_type='subscription',
            amount=amount,
            currency='₼',
            subscription=self,
        )
        
        # Process payment through E-point
        try:
            payment_obj, epoint_result = PaymentService.process_payment(payment.id)
            
            # In production, this would redirect to E-point
            # For now (mock mode), auto-complete
            if EPointService.TEST_MODE:
                # Auto-complete in test mode
                PaymentService.complete_payment(payment.id, epoint_result.get('transaction_id'))
                payment.refresh_from_db()
                
                if payment.status == 'completed':
                    # Renew subscription
                    self.renew()
                    return True, payment
                else:
                    # Payment failed
                    self.status = 'past_due'
                    self.save()
                    return False, payment
            else:
                # Production: Return payment URL for redirect
                return None, payment  # None means redirect needed
                
        except Exception as e:
            logger.error(f"Payment processing error: {e}", exc_info=True)
            payment.status = 'failed'
            payment.notes = str(e)
            payment.save()
            
            self.status = 'past_due'
            self.save()
            return False, payment
    
    def cancel(self):
        """Cancel subscription (no auto-renew)"""
        self.auto_renew = False
        self.cancelled_at = timezone.now()
        self.status = 'cancelled'
        self.save()


class Payment(models.Model):
    """
    Payment model for tracking all payments (subscriptions and top-ups).
    Includes E-point integration, commission, and tax calculations.
    """
    PAYMENT_TYPE_CHOICES = [
        ('subscription', 'Subscription'),
        ('topup', 'Top-up'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_PROVIDER_CHOICES = [
        ('epoint', 'E-point'),
    ]
    
    # User and payment type
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Related objects
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    credit_purchase = models.ForeignKey('CreditPurchase', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    
    # Amounts
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Original amount (₼)
    currency = models.CharField(max_length=10, default='₼')
    
    # E-point amounts (after commission)
    epoint_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Amount E-point receives
    commission = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # 3% commission
    commission_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.03)  # 3% = 0.03
    
    # Tax (from E-point amount)
    tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # 4% tax
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.04)  # 4% = 0.04
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Final amount after tax
    
    # E-point integration
    payment_provider = models.CharField(max_length=20, choices=PAYMENT_PROVIDER_CHOICES, default='epoint')
    epoint_transaction_id = models.CharField(max_length=200, blank=True, null=True)
    epoint_response = models.JSONField(blank=True, null=True)  # Store E-point response
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_type', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.payment_type} - {self.amount} {self.currency} - {self.status}"
    
    def calculate_fees(self):
        """
        Calculate commission and tax.
        Commission: 3% of original amount
        Tax: 4% of E-point amount (amount after commission)
        """
        from decimal import Decimal
        
        # Commission: 3% of original amount
        self.commission = Decimal(str(self.amount)) * Decimal(str(self.commission_rate))
        
        # E-point amount: original - commission
        self.epoint_amount = Decimal(str(self.amount)) - self.commission
        
        # Tax: 4% of E-point amount
        self.tax = self.epoint_amount * Decimal(str(self.tax_rate))
        
        # Net amount: E-point amount - tax
        self.net_amount = self.epoint_amount - self.tax
        
        self.save()
        return {
            'original_amount': float(self.amount),
            'commission': float(self.commission),
            'epoint_amount': float(self.epoint_amount),
            'tax': float(self.tax),
            'net_amount': float(self.net_amount),
        }


class CreditHold(models.Model):
    """
    Credit Hold system for managing pending transactions.
    Credits are held (not deducted) until job completes or fails.
    """
    STATUS_CHOICES = [
        ('hold', 'Hold'),  # Credit is held
        ('confirmed', 'Confirmed'),  # Job succeeded, credit deducted
        ('released', 'Released'),  # Job failed/cancelled, credit returned
    ]
    
    TRANSACTION_TYPE_CHOICES = [
        ('video', 'Video Generation'),
        ('image', 'Image Generation'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_holds')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    
    # Related generation
    video_generation = models.ForeignKey(VideoGeneration, on_delete=models.CASCADE, null=True, blank=True, related_name='credit_hold')
    image_generation = models.ForeignKey(ImageGeneration, on_delete=models.CASCADE, null=True, blank=True, related_name='credit_hold')
    
    # Credit info
    credits_held = models.IntegerField()  # Amount of credits held
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='hold')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.credits_held} credits - {self.status}"
    
    def confirm(self):
        """
        Confirm the hold - deduct credits permanently.
        Called when job succeeds.
        """
        from django.utils import timezone
        
        if self.status != 'hold':
            return False
        
        # Deduct credits (they were already held, now confirm the deduction)
        # Note: Credits were already deducted from available balance when hold was created
        # This just marks the hold as confirmed
        
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        self.save()
        
        return True
    
    def release(self):
        """
        Release the hold - return credits to user.
        Called when job fails or is cancelled.
        """
        from django.utils import timezone
        
        if self.status != 'hold':
            return False
        
        # Return credits to user
        self.user.credits += self.credits_held
        self.user.save()
        
        self.status = 'released'
        self.released_at = timezone.now()
        self.save()
        
        return True


class CreditPurchase(models.Model):
    """
    Top-up credit purchase model.
    Users can buy additional credits when they run out.
    Credits are added to existing balance (unlike subscription which resets).
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PACKAGE_CHOICES = [
        ('small', 'Top-up S - ₼10 - 450 kredit'),
        ('medium', 'Top-up M - ₼25 - 1,150 kredit'),
        ('large', 'Top-up L - ₼50 - 2,200 kredit'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_purchases')
    package = models.CharField(max_length=20, choices=PACKAGE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Credits (no bonus for new packages)
    credits_purchased = models.IntegerField()
    bonus_credits = models.IntegerField(default=0)  # Bonus credits (currently 0 for all packages)
    total_credits = models.IntegerField()  # Same as credits_purchased (no bonus)
    
    # Payment
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='₼')
    payment_id = models.CharField(max_length=200, blank=True, null=True)
    payment_provider = models.CharField(max_length=50, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.package} - {self.status} - {self.total_credits} credits"
    
    def complete(self):
        """Complete the purchase and add credits to user"""
        from django.utils import timezone
        
        if self.status != 'pending':
            return False
        
        # Add credits to user balance (ADD, not reset like subscription)
        self.user.credits += self.total_credits
        self.user.save()
        
        # Update purchase status
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        return True