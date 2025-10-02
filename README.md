# AWS Cost SaaS - Complete Turnkey Solution

A complete, production-ready SaaS platform for AWS cost analysis and optimization. This turnkey solution includes everything you need to launch your own AWS cost optimization service.

## 🚀 Features

- **AI-Powered Cost Analysis**: Advanced algorithms to identify cost optimization opportunities
- **Multi-Format Support**: Upload JSON, CSV, or Excel billing files
- **Real-time Recommendations**: Get actionable insights to reduce AWS costs by up to 40%
- **Subscription Management**: Complete Stripe integration with multiple pricing tiers
- **User Authentication**: Secure JWT-based authentication system
- **Modern UI**: Beautiful, responsive frontend with Tailwind CSS
- **Production Ready**: Docker, Nginx, and deployment configurations included

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis (optional, for caching)
- Stripe account
- AWS account (for Cost Explorer API)

## 🛠️ Quick Setup (Turnkey Installation)

### 1. Clone and Setup

```bash
git clone <your-repo>
cd aws-cost-saas-turnkey
```

### 2. Environment Configuration

**This is the ONLY step you need to customize!**

```bash
# Copy the environment template
cp env.template .env

# Edit .env with your actual values
nano .env
```

**Required Environment Variables:**

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/aws_cost_saas

# JWT Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production

# Stripe Payment Integration
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# AWS Credentials (for Cost Explorer API)
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your_aws_account_id

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Database

```bash
# Create PostgreSQL database
createdb aws_cost_saas

# The application will automatically create tables on first run
```

### 5. Run the Application

```bash
# Start the backend
cd backend
python main.py

# The frontend is served from the backend at http://localhost:8000
```

**That's it! Your SaaS is ready to go! 🎉**

## 🐳 Docker Deployment (Recommended for Production)

### 1. Using Docker Compose

```bash
# Start all services
docker-compose -f deployment/docker-compose.yml up -d

# View logs
docker-compose -f deployment/docker-compose.yml logs -f
```

### 2. Individual Docker Build

```bash
# Build backend image
docker build -f deployment/Dockerfile -t aws-cost-saas-backend .

# Run with environment file
docker run -d --env-file .env -p 8000:8000 aws-cost-saas-backend
```

## ☁️ Cloud Deployment

### Render.com (Easiest)

1. Connect your GitHub repository to Render
2. The `deployment/render.yaml` file will automatically configure your services
3. Add your environment variables in the Render dashboard
4. Deploy!

### Heroku

1. Install Heroku CLI
2. Create a new Heroku app
3. Add PostgreSQL addon
4. Set environment variables
5. Deploy using the `deployment/Procfile`

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set JWT_SECRET_KEY=your-secret-key
heroku config:set STRIPE_SECRET_KEY=your-stripe-key
git push heroku main
```

### AWS/GCP/Azure

Use the Docker configuration with your preferred container service:
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances

## 🔧 Configuration Guide

### Stripe Setup

1. Create a Stripe account at https://stripe.com
2. Get your API keys from the Stripe dashboard
3. Create products and prices for your subscription plans:
   - Starter: $29/month
   - Professional: $99/month
   - Enterprise: $299/month
4. Set up webhooks pointing to `/api/subscription/webhook`
5. Add webhook secret to your `.env` file

### AWS Cost Explorer API

1. Create IAM user with Cost Explorer permissions
2. Attach policy: `CostExplorerReadOnlyAccess`
3. Generate access keys
4. Add to your `.env` file

### Email Configuration

For Gmail:
1. Enable 2-factor authentication
2. Generate an app password
3. Use your Gmail address and app password in `.env`

## 📁 Project Structure

```
aws-cost-saas-turnkey/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── billing_parser.py    # Enhanced cost analysis engine
│   └── models.py            # Pydantic models
├── frontend/
│   ├── index.html           # Main frontend application
│   └── app.js              # JavaScript with robust error handling
├── auth/
│   ├── jwt_handler.py       # JWT authentication
│   └── database.py          # Database management
├── stripe/
│   └── payment_handler.py   # Stripe integration
├── deployment/
│   ├── docker-compose.yml   # Docker orchestration
│   ├── Dockerfile          # Backend container
│   ├── nginx.conf          # Reverse proxy config
│   ├── render.yaml         # Render.com deployment
│   └── Procfile            # Heroku deployment
├── requirements.txt         # Python dependencies
├── env.template            # Environment variables template
└── README.md              # This file
```

## 🔐 Security Features

- JWT-based authentication with refresh tokens
- Password hashing with bcrypt
- CORS protection
- Rate limiting
- Input validation with Pydantic
- SQL injection protection
- XSS protection headers
- Secure file upload handling

## 📊 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /api/user/profile` - Get user profile

### Cost Analysis
- `POST /api/analyze` - Analyze AWS costs
- `POST /api/upload-billing` - Upload billing file
- `GET /api/user/analyses` - Get user's analyses

### Subscriptions
- `GET /api/subscription/plans` - Get available plans
- `POST /api/subscription/create-payment-intent` - Create payment
- `POST /api/subscription/webhook` - Stripe webhooks

### Health & Monitoring
- `GET /health` - Health check
- `GET /api/admin/stats` - Admin statistics

## 🎨 Frontend Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern UI**: Built with Tailwind CSS
- **Error Handling**: Robust error handling with user-friendly messages
- **Real-time Updates**: Live cost analysis results
- **File Upload**: Drag-and-drop billing file upload
- **Payment Integration**: Seamless Stripe checkout
- **Authentication**: Secure login/register flow

## 🚀 Performance Optimizations

- Database connection pooling
- Redis caching (optional)
- Gzip compression
- Static file caching
- CDN-ready static assets
- Optimized Docker images
- Health checks and monitoring

## 🔍 Monitoring & Logging

- Structured logging with timestamps
- Health check endpoints
- Error tracking ready (Sentry integration)
- Performance metrics
- Database query monitoring

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=backend

# Run specific test file
pytest tests/test_auth.py
```

## 📈 Scaling Considerations

- **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
- **Caching**: Redis for session storage and caching
- **CDN**: CloudFront/CloudFlare for static assets
- **Load Balancing**: Multiple backend instances behind load balancer
- **Monitoring**: APM tools like New Relic or DataDog

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check DATABASE_URL format
   - Ensure PostgreSQL is running
   - Verify database exists

2. **Stripe Payment Fails**
   - Verify API keys are correct
   - Check webhook endpoint configuration
   - Ensure HTTPS in production

3. **File Upload Issues**
   - Check file size limits
   - Verify file format support
   - Check upload directory permissions

4. **Authentication Problems**
   - Verify JWT_SECRET_KEY is set
   - Check token expiration settings
   - Ensure proper CORS configuration

### Getting Help

- Check the logs: `docker-compose logs -f backend`
- Verify environment variables: `env | grep -E "(DATABASE|STRIPE|JWT)"`
- Test API endpoints: `curl http://localhost:8000/health`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the API documentation

---

**Ready to launch your AWS Cost SaaS? Just edit the `.env` file and you're good to go! 🚀**