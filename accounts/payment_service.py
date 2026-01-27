"""
Payment Service for E-point integration
Currently in TEST/MOCK mode - not active yet
"""
import logging
from decimal import Decimal
from django.utils import timezone
from .models import Payment, Subscription, CreditPurchase

logger = logging.getLogger(__name__)


class EPointService:
    """
    E-point payment provider service (MOCK/TEST MODE)
    In production, this would integrate with actual E-point API
    """
    
    # Configuration (would be in settings in production)
    TEST_MODE = True  # Currently in test mode
    API_URL = "https://api.epoint.az"  # Placeholder - not active yet
    API_KEY = None  # Would be in environment variables
    
    @staticmethod
    def create_payment(amount, currency='₼', description='', user=None):
        """
        Create payment request with E-point (MOCK)
        In production, this would make actual API call to E-point
        """
        if EPointService.TEST_MODE:
            # Mock response
            logger.info(f"EPOINT MOCK: Creating payment - Amount: {amount} {currency}, User: {user.email if user else 'N/A'}")
            
            # Simulate E-point transaction ID
            mock_transaction_id = f"EPOINT_MOCK_{int(timezone.now().timestamp())}"
            
            return {
                'success': True,
                'transaction_id': mock_transaction_id,
                'payment_url': f"https://epoint.az/pay/{mock_transaction_id}",  # Mock payment URL
                'status': 'pending',
                'message': 'Payment created (MOCK MODE)',
            }
        else:
            # Production code would make actual API call here
            # response = requests.post(EPointService.API_URL + '/create', ...)
            raise NotImplementedError("E-point integration not active yet")
    
    @staticmethod
    def check_payment_status(transaction_id):
        """
        Check payment status with E-point (MOCK)
        """
        if EPointService.TEST_MODE:
            logger.info(f"EPOINT MOCK: Checking payment status - Transaction ID: {transaction_id}")
            
            # Mock: Always return completed for test
            return {
                'success': True,
                'status': 'completed',
                'transaction_id': transaction_id,
                'message': 'Payment completed (MOCK MODE)',
            }
        else:
            # Production code would make actual API call here
            raise NotImplementedError("E-point integration not active yet")
    
    @staticmethod
    def process_webhook(data):
        """
        Process webhook from E-point (MOCK)
        In production, this would verify webhook signature and process payment
        """
        if EPointService.TEST_MODE:
            logger.info(f"EPOINT MOCK: Processing webhook - Data: {data}")
            return {
                'success': True,
                'message': 'Webhook processed (MOCK MODE)',
            }
        else:
            # Production code would verify webhook and process payment
            raise NotImplementedError("E-point integration not active yet")


class PaymentService:
    """
    Main payment service that handles payment creation, processing, and fee calculations
    """
    
    @staticmethod
    def create_payment(user, payment_type, amount, currency='₼', subscription=None, credit_purchase=None):
        """
        Create a payment record and calculate fees
        """
        logger.info(f"Creating payment - User: {user.email}, Type: {payment_type}, Amount: {amount}")
        
        # Create payment record
        payment = Payment.objects.create(
            user=user,
            payment_type=payment_type,
            amount=Decimal(str(amount)),
            currency=currency,
            subscription=subscription,
            credit_purchase=credit_purchase,
            status='pending',
        )
        
        # Calculate fees (commission and tax)
        fees = payment.calculate_fees()
        
        logger.info(f"Payment created - ID: {payment.id}, Fees: {fees}")
        
        return payment, fees
    
    @staticmethod
    def process_payment(payment_id, epoint_transaction_id=None):
        """
        Process payment through E-point (currently MOCK)
        """
        try:
            payment = Payment.objects.get(id=payment_id, status='pending')
        except Payment.DoesNotExist:
            raise ValueError(f"Payment not found or already processed: {payment_id}")
        
        # Create E-point payment request
        epoint_result = EPointService.create_payment(
            amount=float(payment.amount),
            currency=payment.currency,
            description=f"{payment.payment_type} payment",
            user=payment.user,
        )
        
        if not epoint_result.get('success'):
            payment.status = 'failed'
            payment.notes = f"E-point error: {epoint_result.get('message', 'Unknown error')}"
            payment.save()
            raise ValueError(f"E-point payment failed: {epoint_result.get('message')}")
        
        # Update payment with E-point transaction ID
        payment.epoint_transaction_id = epoint_result.get('transaction_id') or epoint_transaction_id
        payment.epoint_response = epoint_result
        payment.status = 'processing'
        payment.processed_at = timezone.now()
        payment.save()
        
        logger.info(f"Payment processing - ID: {payment.id}, E-point Transaction: {payment.epoint_transaction_id}")
        
        return payment, epoint_result
    
    @staticmethod
    def complete_payment(payment_id, epoint_transaction_id=None):
        """
        Complete payment after E-point confirmation (currently MOCK - auto-completes)
        """
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            raise ValueError(f"Payment not found: {payment_id}")
        
        if payment.status == 'completed':
            return payment  # Already completed
        
        # Check E-point status (MOCK - always succeeds)
        if EPointService.TEST_MODE:
            # In test mode, auto-complete
            epoint_status = EPointService.check_payment_status(
                payment.epoint_transaction_id or epoint_transaction_id
            )
        else:
            # Production: Check actual status
            epoint_status = EPointService.check_payment_status(
                payment.epoint_transaction_id or epoint_transaction_id
            )
        
        if epoint_status.get('status') == 'completed':
            # Complete the payment
            payment.status = 'completed'
            payment.completed_at = timezone.now()
            if epoint_transaction_id:
                payment.epoint_transaction_id = epoint_transaction_id
            payment.save()
            
            # Complete related subscription or credit purchase
            if payment.payment_type == 'subscription' and payment.subscription:
                if payment.subscription.status == 'pending':
                    payment.subscription.activate()
            elif payment.payment_type == 'topup' and payment.credit_purchase:
                if payment.credit_purchase.status == 'pending':
                    payment.credit_purchase.complete()
            
            logger.info(f"Payment completed - ID: {payment.id}")
            return payment
        else:
            payment.status = 'failed'
            payment.notes = f"E-point status: {epoint_status.get('status')}"
            payment.save()
            raise ValueError(f"Payment not completed by E-point: {epoint_status.get('status')}")

