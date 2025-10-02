# Stripe Payment Setup - Accept Real Money

## Step 1: Create Stripe Account

1. Go to https://stripe.com
2. Click "Start now" (free)
3. Sign up with email
4. Verify email

## Step 2: Get API Keys

1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy your keys:
   - **Publishable key**: `pk_test_...`
   - **Secret key**: `sk_test_...`

## Step 3: Create Products & Prices

1. Go to https://dashboard.stripe.com/test/products
2. Click "Add product"

**Starter Plan:**
- Name: `AWS Cost Analyzer - Starter`
- Price: `$29.00`
- Billing: `Recurring - Monthly`
- Click "Save product"
- Copy the **Price ID**: `price_xxxxx`

**Professional Plan:**
- Name: `AWS Cost Analyzer - Professional`
- Price: `$99.00`
- Billing: `Recurring - Monthly`
- Click "Save product"
- Copy the **Price ID**: `price_xxxxx`

## Step 4: Add Keys to Render

1. Go to your Render dashboard
2. Click your `aws-cost-analyzer` service
3. Go to "Environment" tab
4. Update these variables:

```
STRIPE_SECRET_KEY = sk_test_YOUR_ACTUAL_KEY_HERE
STRIPE_STARTER_PRICE_ID = price_YOUR_STARTER_PRICE_ID
STRIPE_PROFESSIONAL_PRICE_ID = price_YOUR_PRO_PRICE_ID
```

5. Click "Save Changes"
6. Service will auto-redeploy

## Step 5: Test Payment

1. Go to your live site
2. Sign up for account
3. Click "Upgrade Plan"
4. Use test card: `4242 4242 4242 4242`
5. Expiry: Any future date
6. CVC: Any 3 digits
7. Complete payment

## Step 6: Go Live (Real Money)

When ready for production:

1. Complete Stripe verification
2. Switch to **Live mode** in Stripe dashboard
3. Get **Live API keys**
4. Update Render environment variables with live keys
5. Create live products/prices
6. Update price IDs

## Test Cards

- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- 3D Secure: `4000 0025 0000 3155`

## Webhook Setup (Optional)

For subscription updates:

1. Go to https://dashboard.stripe.com/test/webhooks
2. Add endpoint: `https://aws-cost-analyzer.onrender.com/api/subscription/webhook`
3. Select events: `customer.subscription.*`
4. Copy webhook secret
5. Add to Render: `STRIPE_WEBHOOK_SECRET`

## You're Ready!

Your SaaS can now accept real payments. Stripe handles:
- Credit card processing
- Recurring billing
- Failed payments
- Refunds
- Tax calculation

**Stripe takes 2.9% + $0.30 per transaction**

Example: $29 plan = You get $28.16, Stripe gets $0.84
