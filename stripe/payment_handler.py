#!/usr/bin/env python3
"""
Stripe Payment Handler for AWS Cost SaaS
Complete payment processing and subscription management
"""

import stripe
import os
from typing import Dict, Any, Optional
from datetime import datetime
import json

class StripeHandler:
    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        self.price_ids = {
            "starter": os.getenv("STRIPE_PRICE_ID_STARTER"),
            "professional": os.getenv("STRIPE_PRICE_ID_PROFESSIONAL"),
            "enterprise": os.getenv("STRIPE_PRICE_ID_ENTERPRISE")
        }
    
    async def create_customer(self, email: str, name: str) -> str:
        """Create Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "source": "aws_cost_saas"
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            raise Exception(f"Customer creation failed: {str(e)}")
    
    async def create_subscription(self, user_id: int, plan_id: str) -> stripe.PaymentIntent:
        """Create subscription payment intent"""
        try:
            # Get price ID for the plan
            price_id = self.price_ids.get(plan_id)
            if not price_id:
                raise Exception(f"Invalid plan ID: {plan_id}")
            
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=self._get_plan_amount(plan_id),
                currency='usd',
                metadata={
                    'user_id': str(user_id),
                    'plan_id': plan_id
                },
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            
            return payment_intent
        except stripe.error.StripeError as e:
            raise Exception(f"Payment intent creation failed: {str(e)}")
    
    async def create_subscription_with_customer(self, user_id: int, plan_id: str, customer_id: str) -> stripe.Subscription:
        """Create actual subscription for existing customer"""
        try:
            price_id = self.price_ids.get(plan_id)
            if not price_id:
                raise Exception(f"Invalid plan ID: {plan_id}")
            
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{
                    'price': price_id,
                }],
                metadata={
                    'user_id': str(user_id),
                    'plan_id': plan_id
                },
                expand=['latest_invoice.payment_intent'],
            )
            
            return subscription
        except stripe.error.StripeError as e:
            raise Exception(f"Subscription creation failed: {str(e)}")
    
    async def cancel_subscription(self, subscription_id: str) -> stripe.Subscription:
        """Cancel subscription"""
        try:
            subscription = stripe.Subscription.delete(subscription_id)
            return subscription
        except stripe.error.StripeError as e:
            raise Exception(f"Subscription cancellation failed: {str(e)}")
    
    async def update_subscription(self, subscription_id: str, new_plan_id: str) -> stripe.Subscription:
        """Update subscription plan"""
        try:
            price_id = self.price_ids.get(new_plan_id)
            if not price_id:
                raise Exception(f"Invalid plan ID: {new_plan_id}")
            
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription['items']['data'][0].id,
                    'price': price_id,
                }],
                proration_behavior='create_prorations',
            )
            
            return subscription
        except stripe.error.StripeError as e:
            raise Exception(f"Subscription update failed: {str(e)}")
    
    def verify_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Verify Stripe webhook signature"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event
        except ValueError as e:
            raise Exception(f"Invalid payload: {str(e)}")
        except stripe.error.SignatureVerificationError as e:
            raise Exception(f"Invalid signature: {str(e)}")
    
    async def get_customer_subscriptions(self, customer_id: str) -> list:
        """Get customer's subscriptions"""
        try:
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status='all'
            )
            return subscriptions.data
        except stripe.error.StripeError as e:
            raise Exception(f"Subscription retrieval failed: {str(e)}")
    
    async def create_payment_method(self, customer_id: str, payment_method_id: str) -> stripe.PaymentMethod:
        """Attach payment method to customer"""
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )
            return payment_method
        except stripe.error.StripeError as e:
            raise Exception(f"Payment method attachment failed: {str(e)}")
    
    async def create_setup_intent(self, customer_id: str) -> stripe.SetupIntent:
        """Create setup intent for saving payment method"""
        try:
            setup_intent = stripe.SetupIntent.create(
                customer=customer_id,
                payment_method_types=['card'],
                usage='off_session',
            )
            return setup_intent
        except stripe.error.StripeError as e:
            raise Exception(f"Setup intent creation failed: {str(e)}")
    
    def _get_plan_amount(self, plan_id: str) -> int:
        """Get plan amount in cents"""
        plan_amounts = {
            "starter": 2900,      # $29.00
            "professional": 9900, # $99.00
            "enterprise": 29900   # $299.00
        }
        return plan_amounts.get(plan_id, 2900)
    
    async def handle_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            event_type = event['type']
            event_data = event['data']['object']
            
            if event_type == 'payment_intent.succeeded':
                return await self._handle_payment_succeeded(event_data)
            elif event_type == 'customer.subscription.created':
                return await self._handle_subscription_created(event_data)
            elif event_type == 'customer.subscription.updated':
                return await self._handle_subscription_updated(event_data)
            elif event_type == 'customer.subscription.deleted':
                return await self._handle_subscription_deleted(event_data)
            elif event_type == 'invoice.payment_failed':
                return await self._handle_payment_failed(event_data)
            else:
                return {"status": "ignored", "event_type": event_type}
                
        except Exception as e:
            raise Exception(f"Webhook handling failed: {str(e)}")
    
    async def _handle_payment_succeeded(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment"""
        user_id = payment_intent.get('metadata', {}).get('user_id')
        plan_id = payment_intent.get('metadata', {}).get('plan_id')
        
        return {
            "status": "success",
            "action": "payment_succeeded",
            "user_id": user_id,
            "plan_id": plan_id,
            "amount": payment_intent.get('amount')
        }
    
    async def _handle_subscription_created(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription creation"""
        user_id = subscription.get('metadata', {}).get('user_id')
        plan_id = subscription.get('metadata', {}).get('plan_id')
        
        return {
            "status": "success",
            "action": "subscription_created",
            "user_id": user_id,
            "plan_id": plan_id,
            "subscription_id": subscription.get('id')
        }
    
    async def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription update"""
        user_id = subscription.get('metadata', {}).get('user_id')
        plan_id = subscription.get('metadata', {}).get('plan_id')
        
        return {
            "status": "success",
            "action": "subscription_updated",
            "user_id": user_id,
            "plan_id": plan_id,
            "subscription_id": subscription.get('id')
        }
    
    async def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription deletion"""
        user_id = subscription.get('metadata', {}).get('user_id')
        
        return {
            "status": "success",
            "action": "subscription_deleted",
            "user_id": user_id,
            "subscription_id": subscription.get('id')
        }
    
    async def _handle_payment_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment"""
        customer_id = invoice.get('customer')
        
        return {
            "status": "success",
            "action": "payment_failed",
            "customer_id": customer_id,
            "invoice_id": invoice.get('id')
        }
