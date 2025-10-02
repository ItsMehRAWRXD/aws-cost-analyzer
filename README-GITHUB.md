# AWS Cost Analyzer SaaS

Production-ready SaaS for AWS cost optimization with Stripe payments.

## Features
- User authentication
- Cost analysis with AI recommendations
- Stripe subscription ($29 & $99 plans)
- Beautiful dashboard with charts
- Real-time optimization suggestions

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Stripe keys
```

3. Run locally:
```bash
python app.py
```

## Deploy to Render.com

1. Fork this repo
2. Connect to Render.com
3. Add environment variables
4. Deploy automatically

## Environment Variables

- `SECRET_KEY` - Flask secret key
- `STRIPE_SECRET_KEY` - Stripe API key
- `STRIPE_STARTER_PRICE_ID` - Starter plan price ID
- `STRIPE_PROFESSIONAL_PRICE_ID` - Pro plan price ID

## Tech Stack

- Flask
- SQLite
- Stripe
- Chart.js
- Tailwind CSS

## License

MIT
