# 🚀 PitCrew Labs Deployment Guide

## 📋 Overview

This guide covers the complete deployment process for the PitCrew Labs Sales Co-Pilot Platform, including GitHub repository setup, CI/CD pipeline configuration, and team deployment automation.

## 🏗️ Repository Setup

### ✅ Completed Steps

1. **Git Repository Initialized**
   - ✅ Local Git repository created
   - ✅ Comprehensive `.gitignore` file added
   - ✅ Initial commit with all project files

2. **GitHub Repository Created**
   - ✅ Repository `pcl-app` created at: https://github.com/ks2178o2/pcl-app
   - ✅ Code successfully pushed to GitHub
   - ✅ Security issues resolved (API keys removed from history)

3. **Project Structure**
   - ✅ Complete backend (FastAPI/Python) with 6 services
   - ✅ Complete frontend (React/TypeScript) with 10+ components
   - ✅ Database schemas and migrations
   - ✅ Comprehensive test suite (95%+ coverage)
   - ✅ Docker configuration for containerization

## 🔧 CI/CD Pipeline Configuration

### GitHub Actions Workflow

The CI/CD pipeline includes:

- **Backend Testing**: Python tests with PostgreSQL integration
- **Frontend Testing**: React/TypeScript tests with Vitest
- **Integration Testing**: End-to-end workflow testing
- **Security Scanning**: Trivy vulnerability scanning
- **Build & Deploy**: Automated deployment to staging/production

### Workflow Triggers

- **Push to `main`**: Triggers full CI/CD pipeline + production deployment
- **Push to `develop`**: Triggers CI/CD pipeline + staging deployment
- **Pull Requests**: Triggers testing and security scanning

## 🚀 Deployment Options

### Option 1: Manual Deployment

```bash
# Clone the repository
git clone https://github.com/ks2178o2/pcl-app.git
cd pcl-app

# Set up environment
cp env.example .env
# Edit .env with your configuration

# Backend setup
cd apps/app-api
pip install -r requirements.txt
python setup_supabase.py

# Frontend setup
cd ../realtime-gateway
npm install
npm run build

# Start services
# Backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend (in another terminal)
npm run dev
```

### Option 2: Docker Deployment

```bash
# Clone the repository
git clone https://github.com/ks2178o2/pcl-app.git
cd pcl-app

# Set up environment
cp env.example .env
# Edit .env with your configuration

# Start with Docker Compose
docker-compose up -d

# Scale services
docker-compose up -d --scale backend=3
```

### Option 3: Cloud Deployment

#### Heroku
```bash
# Install Heroku CLI
# Create Heroku app
heroku create pitcrew-labs-app

# Set environment variables
heroku config:set SUPABASE_URL=your_supabase_url
heroku config:set SUPABASE_KEY=your_supabase_key
# ... other environment variables

# Deploy
git push heroku main
```

#### AWS/GCP/Azure
- Use the provided Docker configuration
- Deploy using container services (ECS, Cloud Run, Container Instances)
- Set up load balancers and auto-scaling

## 🔄 Team Deployment Automation

### Setting Up Team Repository

1. **Create Team Repository**
   ```bash
   # Create a new repository for your team
   gh repo create your-team/pcl-app-production --private
   ```

2. **Set Up Deployment Automation**
   ```bash
   # Add deployment webhook
   # Configure automatic sync from main repository
   ```

3. **Configure Environment Variables**
   - Set up production environment variables
   - Configure database connections
   - Set up monitoring and logging

### Automated Deployment Flow

```
Developer Push → GitHub Actions → Build & Test → Deploy to Staging → Deploy to Production
```

## 📊 Monitoring & Maintenance

### Health Checks

- **Backend Health**: `GET /health`
- **Frontend Health**: `GET /health`
- **Database Health**: Connection monitoring
- **API Health**: Response time monitoring

### Logging

- **Application Logs**: Structured logging with JSON format
- **Audit Logs**: Complete audit trail for compliance
- **Error Logs**: Error tracking and alerting
- **Performance Logs**: Performance metrics and optimization

### Monitoring Tools

- **Application Monitoring**: Sentry integration
- **Performance Monitoring**: Custom metrics
- **Security Monitoring**: Real-time security scanning
- **Uptime Monitoring**: Service availability tracking

## 🔒 Security Configuration

### Environment Variables

```bash
# Required Environment Variables
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
JWT_SECRET=your_jwt_secret_key
ENCRYPTION_KEY=your_encryption_key

# Optional Environment Variables
OPENAI_API_KEY=your_openai_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key
SENTRY_DSN=your_sentry_dsn
```

### Security Features

- **Multi-Tenant Isolation**: Complete data separation
- **Role-Based Access Control**: 5-tier RBAC system
- **Audit Logging**: Complete audit trail
- **Security Scanning**: Automated vulnerability scanning
- **Data Encryption**: End-to-end encryption

## 📈 Scaling Considerations

### Horizontal Scaling

- **Backend**: Multiple FastAPI instances behind load balancer
- **Frontend**: CDN distribution for static assets
- **Database**: Read replicas and connection pooling
- **Caching**: Redis for session and data caching

### Performance Optimization

- **Database Indexing**: Optimized queries and indexes
- **Caching Strategy**: Multi-level caching implementation
- **CDN Integration**: Static asset distribution
- **API Rate Limiting**: Request throttling and limits

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Check environment variables
   - Verify database accessibility
   - Check network connectivity

2. **Authentication Issues**
   - Verify JWT secret configuration
   - Check user permissions
   - Validate token expiration

3. **Performance Issues**
   - Monitor database query performance
   - Check memory usage
   - Analyze API response times

### Support Resources

- **Documentation**: Comprehensive guides and API docs
- **GitHub Issues**: Bug reports and feature requests
- **Community**: Discord server and discussions
- **Email Support**: support@pitcrew-labs.com

## 📚 Additional Resources

### Documentation Links

- [API Documentation](https://github.com/ks2178o2/pcl-app/blob/main/README.md)
- [Database Schema](https://github.com/ks2178o2/pcl-app/blob/main/enhanced_rag_context_schema.sql)
- [Testing Guide](https://github.com/ks2178o2/pcl-app/blob/main/RAG_FEATURE_MANAGEMENT_TESTING_GUIDE.md)
- [Architecture Decisions](https://github.com/ks2178o2/pcl-app/blob/main/RAG_ARCHITECTURE_DECISIONS.md)

### Quick Start Commands

```bash
# Development
npm run dev

# Testing
npm run test

# Building
npm run build

# Docker
docker-compose up -d

# Database setup
python check_and_create_tables.py
```

---

**PitCrew Labs** - Ready for production deployment! 🏁🚀
