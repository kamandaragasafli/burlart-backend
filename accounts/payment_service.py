"""
Payment Service for E-point integration
"""
import logging
import requests
import json
import base64
import hashlib
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from .models import Payment, Subscription, CreditPurchase

logger = logging.getLogger(__name__)


class EPointService:
    """
    E-point payment provider service
    """
    
    # Configuration from Django settings
    TEST_MODE = getattr(settings, 'EPOINT_TEST_MODE', True)
    API_URL = getattr(settings, 'EPOINT_API_URL', 'https://epoint.az/api/1')
    PUBLIC_KEY = getattr(settings, 'EPOINT_PUBLIC_KEY', None)
    SECRET_KEY = getattr(settings, 'EPOINT_SECRET_KEY', None)
    
    @staticmethod
    def _generate_signature(data: str, private_key: str) -> str:
        """
        Generate E-point signature: base64_encode(sha1(private_key + data + private_key))
        """
        # Create SHA1 hash: private_key + data + private_key
        hash_string = private_key + data + private_key
        sha1_hash = hashlib.sha1(hash_string.encode('utf-8')).digest()
        # Base64 encode the hash
        signature = base64.b64encode(sha1_hash).decode('utf-8')
        return signature
    
    @staticmethod
    def create_payment(amount, currency='AZN', description='', user=None, order_id=None, payment_type=None):
        """
        Create payment request with E-point
        
        Args:
            amount: Payment amount
            currency: Currency code (₼, AZN, USD, EUR)
            description: Payment description
            user: User instance
            order_id: Order ID (required by E-point API)
            payment_type: Payment type ('subscription' or 'topup') for success page redirect
        """
        # Convert currency symbol to ISO code for E-point API
        currency_map = {
            '₼': 'AZN',
            'AZN': 'AZN',
            'USD': 'USD',
            'EUR': 'EUR',
        }
        currency_code = currency_map.get(currency, 'AZN')
        
        # Generate order_id if not provided
        if not order_id:
            order_id = f"ORDER_{int(timezone.now().timestamp())}"
        
        # Check if we should use mock mode
        # Only use mock mode if EPOINT_TEST_MODE=True (not auto-enabled by localhost)
        if EPointService.TEST_MODE:
            # Mock response for testing
            logger.info(f"EPOINT MOCK: Creating payment - Amount: {amount} {currency}, User: {user.email if user else 'N/A'}")
            
            # Simulate E-point transaction ID
            mock_transaction_id = f"EPOINT_MOCK_{int(timezone.now().timestamp())}"
            
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173').rstrip('/')
            # In TEST_MODE, redirect to frontend success page (auto-complete payment)
            # Add type parameter for proper success page handling
            type_param = f"&type={payment_type}" if payment_type else ""
            payment_url = f"{frontend_url}/checkout/success?transaction_id={mock_transaction_id}&mock=true{type_param}"
            
            return {
                'success': True,
                'transaction_id': mock_transaction_id,
                'payment_url': payment_url,  # Redirect to frontend success page in TEST_MODE
                'status': 'pending',
                'message': 'Payment created (MOCK MODE)',
            }
        
        # Production: Real E-point API call
        try:
            logger.info(f"EPOINT: Creating payment - Amount: {amount} {currency}, User: {user.email if user else 'N/A'}")
            
            # Check if API credentials are configured
            if not EPointService.PUBLIC_KEY or not EPointService.SECRET_KEY:
                logger.error("EPOINT: API credentials not configured - PUBLIC_KEY or SECRET_KEY missing in .env")
                return {
                    'success': False,
                    'message': 'E-point API credentials not configured. Please set EPOINT_PUBLIC_KEY and EPOINT_SECRET_KEY in .env file.',
                }
            
            # Prepare payment data for E-point (JSON format)
            # IMPORTANT: Key order matters for signature verification (as per E-point docs page 5)
            # According to E-point documentation example: {"public_key":"...","amount":"...","currency":"...","description":"...","order_id":"..."}
            # But required params are: public_key, amount, currency, language, order_id
            # Optional: description, success_redirect_url, error_redirect_url
            # Remove trailing slashes from URLs to avoid double slashes
            frontend_url = settings.FRONTEND_URL.rstrip('/')
            
            # Build JSON string with exact key order as per E-point documentation
            # Order based on doc example: public_key, amount, currency, language, description, order_id, success_redirect_url, error_redirect_url
            from collections import OrderedDict
            payment_data_json = OrderedDict([
                ('public_key', EPointService.PUBLIC_KEY),
                ('amount', str(float(amount))),
                ('currency', currency_code),
                ('language', 'az'),
            ])
            
            # Add description before order_id (as per doc example)
            if description:
                payment_data_json['description'] = description
            
            payment_data_json['order_id'] = str(order_id)
            payment_data_json['success_redirect_url'] = f"{frontend_url}/checkout/success"
            payment_data_json['error_redirect_url'] = f"{frontend_url}/checkout/cancel"
            
            # Convert to JSON string with exact key order (OrderedDict preserves order)
            # Use separators=(',', ':') to remove spaces, ensure_ascii=True for proper encoding
            json_string = json.dumps(payment_data_json, separators=(',', ':'), ensure_ascii=True, sort_keys=False)
            
            # Base64 encode the JSON string
            data_encoded = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
            
            # Generate signature: base64_encode(sha1(private_key + data + private_key))
            signature = EPointService._generate_signature(data_encoded, EPointService.SECRET_KEY)
            
            # Debug logging for signature verification
            logger.info(f"EPOINT: JSON string: {json_string}")
            logger.info(f"EPOINT: Data encoded: {data_encoded}")
            logger.info(f"EPOINT: SECRET_KEY length: {len(EPointService.SECRET_KEY) if EPointService.SECRET_KEY else 0}")
            logger.info(f"EPOINT: SECRET_KEY (full): {EPointService.SECRET_KEY}")
            logger.info(f"EPOINT: Signature: {signature}")
            
            # Verify signature generation manually for debugging
            hash_string = EPointService.SECRET_KEY + data_encoded + EPointService.SECRET_KEY
            logger.info(f"EPOINT: Hash string (first 50 chars): {hash_string[:50]}...")
            sha1_hash = hashlib.sha1(hash_string.encode('utf-8')).digest()
            manual_signature = base64.b64encode(sha1_hash).decode('utf-8')
            logger.info(f"EPOINT: Manual signature check: {manual_signature}")
            if signature != manual_signature:
                logger.error(f"EPOINT: Signature mismatch in generation! Expected: {manual_signature}, Got: {signature}")
            
            # Prepare POST request payload
            request_payload = {
                'data': data_encoded,
                'signature': signature
            }
            
            # Make API request to E-point
            logger.info(f"EPOINT: Sending request to {EPointService.API_URL}/request")
            response = requests.post(
                f"{EPointService.API_URL}/request",
                data=request_payload,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"EPOINT: Payment request successful - Response: {result}")
                
                # Check if E-point returned an error
                if result.get('status') == 'error':
                    error_message = result.get('message', 'Unknown error')
                    logger.error(f"EPOINT: API returned error - {error_message}")
                    
                    # If signature error, provide detailed logging
                    if 'signature' in error_message.lower() or 'Signature' in error_message:
                        logger.error(f"EPOINT: Signature mismatch - Check SECRET_KEY in .env file")
                        logger.error(f"EPOINT: Debug - JSON: {json_string[:200]}...")
                        logger.error(f"EPOINT: Debug - Data encoded: {data_encoded[:100]}...")
                    
                    return {
                        'success': False,
                        'message': f'E-point API error: {error_message}',
                    }
                
                # Get checkout URL from response (as per E-point documentation page 6)
                # E-point returns: status, transaction, redirect_url
                checkout_url = result.get('redirect_url') or result.get('checkout_url') or result.get('url')
                transaction_id = result.get('transaction') or result.get('transaction_id') or result.get('id')
                
                if checkout_url:
                    # Use the checkout_url from response
                    payment_url = checkout_url
                    
                    logger.info(f"EPOINT: Payment created successfully - Transaction: {transaction_id}")
                    return {
                        'success': True,
                        'transaction_id': transaction_id,
                        'payment_url': payment_url,
                        'status': 'pending',
                        'message': 'Payment created successfully',
                    }
                else:
                    logger.error(f"EPOINT: No checkout URL in response - {result}")
                    return {
                        'success': False,
                        'message': 'E-point API did not return checkout URL',
                    }
            else:
                logger.error(f"EPOINT: Payment creation failed - Status: {response.status_code}, Response: {response.text}")
                return {
                    'success': False,
                    'message': f'E-point API error: {response.status_code}',
                }
        except requests.exceptions.RequestException as e:
            # Network/connection errors
            logger.error(f"EPOINT: Connection error - {str(e)}")
            return {
                'success': False,
                'message': f'E-point API connection error: {str(e)}',
            }
        except Exception as e:
            logger.error(f"EPOINT: Exception during payment creation - {str(e)}")
            return {
                'success': False,
                'message': f'E-point API error: {str(e)}',
            }
    
    @staticmethod
    def check_payment_status(transaction_id):
        """
        Check payment status with E-point
        """
        # Check if this is a mock transaction ID
        is_mock = transaction_id and transaction_id.startswith('EPOINT_MOCK_')
        
        if EPointService.TEST_MODE or is_mock:
            logger.info(f"EPOINT MOCK: Checking payment status - Transaction ID: {transaction_id}")
            
            # Mock: Always return completed for test
            return {
                'success': True,
                'status': 'completed',
                'transaction_id': transaction_id,
                'message': 'Payment completed (MOCK MODE)',
            }
        
        # Production: Real E-point API call
        try:
            logger.info(f"EPOINT: Checking payment status - Transaction ID: {transaction_id}")
            
            # Prepare status check data
            status_data_json = {
                'public_key': EPointService.PUBLIC_KEY,
                'transaction_id': transaction_id,
            }
            
            # Convert to JSON string
            json_string = json.dumps(status_data_json, separators=(',', ':'))
            
            # Base64 encode the JSON string
            data_encoded = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
            
            # Generate signature
            signature = EPointService._generate_signature(data_encoded, EPointService.SECRET_KEY)
            
            # Prepare POST request payload
            request_payload = {
                'data': data_encoded,
                'signature': signature
            }
            
            response = requests.post(
                f"{EPointService.API_URL}/get-status",
                data=request_payload,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"EPOINT: Payment status retrieved - Status: {result.get('status')}")
                return {
                    'success': True,
                    'status': result.get('status'),  # e.g., 'completed', 'pending', 'failed'
                    'transaction_id': transaction_id,
                    'message': 'Status retrieved successfully',
                }
            else:
                logger.error(f"EPOINT: Status check failed - Status: {response.status_code}")
                return {
                    'success': False,
                    'status': 'unknown',
                    'message': f'E-point API error: {response.status_code}',
                }
        except Exception as e:
            logger.error(f"EPOINT: Exception during status check - {str(e)}")
            # If it's a mock transaction, return completed
            if is_mock:
                return {
                    'success': True,
                    'status': 'completed',
                    'transaction_id': transaction_id,
                    'message': 'Payment completed (MOCK MODE)',
                }
            return {
                'success': False,
                'status': 'unknown',
                'message': f'E-point API exception: {str(e)}',
            }
    
    @staticmethod
    def process_webhook(data_encoded, signature_received):
        """
        Process webhook from E-point
        This is called by E-point when payment status changes
        
        Args:
            data_encoded: Base64 encoded JSON data from E-point
            signature_received: Signature from E-point to verify authenticity
        """
        if EPointService.TEST_MODE:
            logger.info(f"EPOINT MOCK: Processing webhook - Data: {data_encoded[:50]}...")
            # In test mode, just decode and return
            try:
                decoded_json = base64.b64decode(data_encoded).decode('utf-8')
                webhook_data = json.loads(decoded_json)
                return {
                    'success': True,
                    'data': webhook_data,
                    'message': 'Webhook processed (MOCK MODE)',
                }
            except Exception as e:
                logger.error(f"EPOINT MOCK: Failed to decode webhook data - {str(e)}")
                return {
                    'success': False,
                    'message': f'Failed to decode webhook data: {str(e)}',
                }
        
        # Production: Verify and process E-point webhook
        try:
            # Step 1: Verify signature (as per E-point documentation page 7)
            # Generate signature: base64_encode(sha1(private_key + data + private_key))
            expected_signature = EPointService._generate_signature(data_encoded, EPointService.SECRET_KEY)
            
            if expected_signature != signature_received:
                logger.error(f"EPOINT: Webhook signature verification failed")
                logger.error(f"EPOINT: Expected: {expected_signature[:50]}...")
                logger.error(f"EPOINT: Received: {signature_received[:50]}...")
                return {
                    'success': False,
                    'message': 'Signature verification failed - webhook may be tampered',
                }
            
            logger.info(f"EPOINT: Webhook signature verified successfully")
            
            # Step 2: Decode data (base64_decode)
            decoded_json = base64.b64decode(data_encoded).decode('utf-8')
            webhook_data = json.loads(decoded_json)
            
            logger.info(f"EPOINT: Webhook data decoded - Transaction: {webhook_data.get('transaction')}, Status: {webhook_data.get('status')}")
            
            # Step 3: Validate required fields (as per E-point documentation page 7)
            required_fields = ['order_id', 'status', 'transaction']
            if not all(field in webhook_data for field in required_fields):
                logger.error(f"EPOINT: Invalid webhook data - Missing required fields")
                logger.error(f"EPOINT: Received fields: {list(webhook_data.keys())}")
                return {
                    'success': False,
                    'message': 'Invalid webhook data - missing required fields',
                }
            
            logger.info(f"EPOINT: Webhook processed successfully - Order: {webhook_data.get('order_id')}, Status: {webhook_data.get('status')}")
            
            return {
                'success': True,
                'data': webhook_data,
                'message': 'Webhook processed successfully',
            }
        except Exception as e:
            logger.error(f"EPOINT: Exception during webhook processing - {str(e)}")
            return {
                'success': False,
                'message': f'Webhook processing exception: {str(e)}',
            }


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
            order_id=payment.id,  # Use payment ID as order_id
            payment_type=payment.payment_type,  # Pass payment type for success page
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

