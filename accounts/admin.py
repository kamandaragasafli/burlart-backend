from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, VideoGeneration, ImageGeneration, Subscription, CreditPurchase, Payment
from django.db.models import Sum, Count, Q
from django.utils.html import format_html
from django.conf import settings
import fal_client
import logging
import requests
import os

logger = logging.getLogger(__name__)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'date_joined', 'subscription_plan_display', 'credits', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'date_joined']
    search_fields = ['email']
    ordering = ['-date_joined']  # Yeniləri birinci
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'credits')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'credits'),
        }),
    )
    
    def subscription_plan_display(self, obj):
        """Display subscription plan name"""
        try:
            subscription = obj.subscription
            if subscription and subscription.is_active():
                from .subscription_constants import SUBSCRIPTION_PLANS
                plan_config = SUBSCRIPTION_PLANS.get(subscription.plan, {})
                plan_name = plan_config.get('name', subscription.plan.upper())
                return format_html(
                    '<span style="color: #51cf66; font-weight: bold;">{}</span>',
                    plan_name
                )
            elif subscription:
                # Subscription exists but not active
                from .subscription_constants import SUBSCRIPTION_PLANS
                plan_config = SUBSCRIPTION_PLANS.get(subscription.plan, {})
                plan_name = plan_config.get('name', subscription.plan.upper())
                return format_html(
                    '<span style="color: #ffa500;">{} ({})</span>',
                    plan_name,
                    subscription.status
                )
        except:
            pass
        return format_html('<span style="color: #868e96;">Yoxdur</span>')
    subscription_plan_display.short_description = 'Paket'


@admin.register(VideoGeneration)
class VideoGenerationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'tool', 'status', 'credits_used', 'created_at']
    list_filter = ['status', 'tool', 'created_at']
    search_fields = ['user__email', 'prompt', 'fal_request_id']
    readonly_fields = ['created_at', 'updated_at', 'credits_used']  # Credits are locked
    ordering = ['-created_at']  # Yeniləri birinci
    
    fieldsets = (
        ('User & Tool', {'fields': ('user', 'tool', 'model_id')}),
        ('Content', {'fields': ('prompt', 'video_url')}),
        ('Status', {'fields': ('status', 'credits_used', 'fal_request_id', 'error_message')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def has_change_permission(self, request, obj=None):
        # Prevent changing credits_used as it's locked
        return super().has_change_permission(request, obj)


@admin.register(ImageGeneration)
class ImageGenerationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'tool', 'status', 'credits_used', 'created_at']
    list_filter = ['status', 'tool', 'created_at']
    search_fields = ['user__email', 'prompt', 'fal_request_id']
    readonly_fields = ['created_at', 'updated_at', 'credits_used']  # Credits are locked
    ordering = ['-created_at']  # Yeniləri birinci
    
    fieldsets = (
        ('User & Tool', {'fields': ('user', 'tool', 'model_id')}),
        ('Content', {'fields': ('prompt', 'image_url')}),
        ('Status', {'fields': ('status', 'credits_used', 'fal_request_id', 'error_message')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def has_change_permission(self, request, obj=None):
        # Prevent changing credits_used as it's locked
        return super().has_change_permission(request, obj)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'plan', 'status', 'auto_renew', 'next_renewal_date', 'created_at']
    list_filter = ['status', 'plan', 'auto_renew', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']  # Yeniləri birinci
    
    fieldsets = (
        ('User & Plan', {'fields': ('user', 'plan', 'status')}),
        ('Renewal', {'fields': ('auto_renew', 'next_renewal_date', 'cancelled_at', 'last_renewed_at')}),
        ('Payment', {'fields': ('payment_id', 'payment_provider')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(CreditPurchase)
class CreditPurchaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'package', 'status', 'total_credits', 'price', 'created_at']
    list_filter = ['status', 'package', 'created_at']
    search_fields = ['user__email', 'payment_id']
    readonly_fields = ['created_at', 'completed_at', 'total_credits']
    ordering = ['-created_at']  # Yeniləri birinci
    
    fieldsets = (
        ('User & Package', {'fields': ('user', 'package', 'status')}),
        ('Credits', {'fields': ('credits_purchased', 'total_credits')}),
        ('Payment', {'fields': ('price', 'currency', 'payment_id', 'payment_provider')}),
        ('Timestamps', {'fields': ('created_at', 'completed_at')}),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'payment_type', 'status', 'amount_display', 'fees_display', 'net_amount_display', 'created_at']
    list_filter = ['status', 'payment_type', 'payment_provider', 'created_at']
    search_fields = ['user__email', 'epoint_transaction_id', 'notes']
    readonly_fields = ['created_at', 'processed_at', 'completed_at', 'commission', 'tax', 'net_amount', 'epoint_amount']
    ordering = ['-created_at']  # Yeniləri birinci
    
    fieldsets = (
        ('User & Type', {'fields': ('user', 'payment_type', 'status')}),
        ('Related Objects', {'fields': ('subscription', 'credit_purchase')}),
        ('Amounts', {'fields': ('amount', 'currency')}),
        ('Fees & Calculations', {
            'fields': ('commission', 'commission_rate', 'epoint_amount', 'tax', 'tax_rate', 'net_amount'),
            'description': 'Commission: 3% of original amount. Tax: 4% of E-point amount.',
        }),
        ('E-point Integration', {'fields': ('payment_provider', 'epoint_transaction_id', 'epoint_response')}),
        ('Timestamps', {'fields': ('created_at', 'processed_at', 'completed_at')}),
        ('Notes', {'fields': ('notes',)}),
    )
    
    def amount_display(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_display.short_description = 'Amount'
    
    def fees_display(self, obj):
        if obj.commission and obj.tax:
            return format_html(
                '<span style="color: #ff6b6b;">Commission: {} {}</span><br>'
                '<span style="color: #ffa500;">Tax: {} {}</span>',
                obj.commission, obj.currency,
                obj.tax, obj.currency
            )
        return '-'
    fees_display.short_description = 'Fees'
    
    def net_amount_display(self, obj):
        if obj.net_amount:
            return format_html(
                '<strong style="color: #51cf66;">{} {}</strong>',
                obj.net_amount, obj.currency
            )
        return '-'
    net_amount_display.short_description = 'Net Amount'
    
    def changelist_view(self, request, extra_context=None):
        # Add financial summary to changelist
        extra_context = extra_context or {}
        
        # Total revenue (all completed payments)
        total_revenue = Payment.objects.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Total commission
        total_commission = Payment.objects.filter(status='completed').aggregate(
            total=Sum('commission')
        )['total'] or 0
        
        # Total tax
        total_tax = Payment.objects.filter(status='completed').aggregate(
            total=Sum('tax')
        )['total'] or 0
        
        # Total net amount
        total_net = Payment.objects.filter(status='completed').aggregate(
            total=Sum('net_amount')
        )['total'] or 0
        
        # Payment counts
        payment_counts = Payment.objects.filter(status='completed').aggregate(
            total=Count('id'),
            subscriptions=Count('id', filter=Q(payment_type='subscription')),
            topups=Count('id', filter=Q(payment_type='topup')),
        )
        
        # Get FAL AI account balance using REST API
        fal_balance = None
        fal_error = None
        try:
            if hasattr(settings, 'FAL_KEY') and settings.FAL_KEY:
                import requests
                headers = {
                    'Authorization': f'Key {settings.FAL_KEY}',
                    'Content-Type': 'application/json'
                }
                
                # Try multiple FAL AI API endpoints for account balance
                endpoints = [
                    'https://fal.ai/api/v1/account',
                    'https://fal.ai/api/v1/user',
                    'https://fal.ai/api/v1/balance',
                    'https://fal.ai/api/v1/credits',
                ]
                
                for endpoint in endpoints:
                    try:
                        logger.debug(f"Trying FAL AI endpoint: {endpoint}")
                        response = requests.get(endpoint, headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            account_data = response.json()
                            logger.debug(f"FAL AI response from {endpoint}: {account_data}")
                            
                            # Try different possible keys for balance
                            fal_balance = (
                                account_data.get('balance') or 
                                account_data.get('credits') or 
                                account_data.get('credit_balance') or
                                account_data.get('account_balance') or
                                account_data.get('available_credits') or
                                account_data.get('remaining_credits') or
                                account_data.get('credits_balance')
                            )
                            
                            # If still None, try nested structures
                            if fal_balance is None and isinstance(account_data, dict):
                                if 'account' in account_data:
                                    account_info = account_data['account']
                                    fal_balance = (
                                        account_info.get('balance') or 
                                        account_info.get('credits') or
                                        account_info.get('credit_balance')
                                    )
                                if fal_balance is None and 'user' in account_data:
                                    user_info = account_data['user']
                                    fal_balance = (
                                        user_info.get('balance') or 
                                        user_info.get('credits') or
                                        user_info.get('credit_balance')
                                    )
                            
                            if fal_balance is not None:
                                logger.info(f"FAL AI balance retrieved: {fal_balance} from {endpoint}")
                                break
                        elif response.status_code == 401:
                            logger.warning(f"FAL AI authentication failed for {endpoint}")
                            fal_error = "FAL AI authentication failed - check API key"
                            break
                        else:
                            logger.debug(f"FAL AI endpoint {endpoint} returned status {response.status_code}")
                    except requests.exceptions.RequestException as e:
                        logger.debug(f"FAL AI endpoint {endpoint} failed: {str(e)}")
                        continue
                
                if fal_balance is None and not fal_error:
                    fal_error = "Could not retrieve balance from FAL AI API - all endpoints failed"
            else:
                fal_error = "FAL_KEY not configured in settings"
        except Exception as e:
            logger.error(f"Error accessing FAL AI API: {str(e)}", exc_info=True)
            fal_error = str(e)
        
        extra_context['financial_summary'] = {
            'total_revenue': float(total_revenue),
            'total_commission': float(total_commission),
            'total_tax': float(total_tax),
            'total_net': float(total_net),
            'payment_counts': payment_counts,
            'fal_balance': fal_balance,
            'fal_error': fal_error,
        }
        
        return super().changelist_view(request, extra_context)


