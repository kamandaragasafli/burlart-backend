from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, VideoGeneration, ImageGeneration, Subscription, CreditPurchase, Payment
from django.db.models import Sum, Count, Q
from django.utils.html import format_html


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'credits', 'language', 'theme', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'language', 'theme']
    search_fields = ['email']
    ordering = ['email']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'credits', 'language', 'theme')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'credits', 'language', 'theme'),
        }),
    )


@admin.register(VideoGeneration)
class VideoGenerationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'tool', 'status', 'credits_used', 'created_at']
    list_filter = ['status', 'tool', 'created_at']
    search_fields = ['user__email', 'prompt', 'fal_request_id']
    readonly_fields = ['created_at', 'updated_at', 'credits_used']  # Credits are locked
    
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
        
        extra_context['financial_summary'] = {
            'total_revenue': float(total_revenue),
            'total_commission': float(total_commission),
            'total_tax': float(total_tax),
            'total_net': float(total_net),
            'payment_counts': payment_counts,
        }
        
        return super().changelist_view(request, extra_context)


