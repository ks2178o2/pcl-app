# 🏁 PitCrew Labs Sales Co-Pilot Platform

## 📋 Overview

**PitCrew Labs** is an enterprise-grade, AI-powered sales co-pilot platform designed to enhance sales performance through intelligent knowledge management, real-time assistance, and multi-tenant collaboration.

## 🚀 Key Features

### 🧠 AI-Powered Sales Intelligence
- **20+ Sales Co-Pilot Features**: Comprehensive suite of AI-powered sales assistance tools
- **Real-Time Call Coaching**: Live assistance during sales calls
- **Customer Intelligence**: 360° customer view with historical insights
- **Predictive Analytics**: Sales forecasting and pipeline analysis
- **Performance Benchmarking**: Team and individual performance tracking

### 🏢 Multi-Tenant Architecture
- **Complete Tenant Isolation**: Secure data separation between sales organizations
- **Hierarchical Organizations**: Parent-child organization relationships with feature inheritance
- **Role-Based Access Control**: 5-tier RBAC system (system_admin, org_admin, sales_manager, salesperson, customer)
- **Cross-Tenant Collaboration**: Share successful sales strategies between organizations

### 📊 Advanced Knowledge Management
- **Global Knowledge Base**: App-wide sales best practices and methodologies
- **Context Sharing**: Cross-tenant knowledge sharing with approval workflows
- **Multiple Upload Types**: File upload, web scraping, and bulk API uploads
- **Smart Content Processing**: Automatic content extraction and categorization
- **Duplicate Detection**: Prevent duplicate content across the platform

### 🔒 Enterprise Security
- **Comprehensive Audit Logging**: Complete audit trail for compliance
- **Security Monitoring**: Real-time violation detection and alerting
- **Data Encryption**: End-to-end encryption for all sensitive data
- **Compliance Ready**: Built-in compliance reporting and monitoring

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **6 Core Services**: Enhanced context management, tenant isolation, feature inheritance, audit logging, and more
- **4 API Modules**: RESTful APIs for all platform functionality
- **15+ Database Tables**: Comprehensive data model with views and functions
- **95%+ Test Coverage**: Production-ready with comprehensive testing

### Frontend (React/TypeScript)
- **10+ UI Components**: Intuitive interface for all user roles
- **3 Custom Hooks**: Comprehensive state management
- **Responsive Design**: Mobile-responsive design for all devices
- **Accessibility**: Full WCAG compliance with keyboard navigation

### Database (Supabase/PostgreSQL)
- **Row-Level Security**: Automatic tenant isolation
- **Optimized Queries**: Performance-optimized database operations
- **Real-Time Updates**: Live synchronization across all components
- **Backup & Recovery**: Comprehensive data protection

## 🛠️ Technology Stack

### Backend
- **Python 3.9+**: Core programming language
- **FastAPI**: Modern, fast web framework
- **Supabase**: Backend-as-a-Service with PostgreSQL
- **Pytest**: Comprehensive testing framework
- **Pydantic**: Data validation and serialization

### Frontend
- **React 18**: Modern UI library
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives
- **TanStack Query**: Data fetching and caching

### DevOps & Testing
- **Vitest**: Fast unit testing framework
- **GitHub Actions**: CI/CD automation
- **Docker**: Containerization support
- **Coverage Reporting**: Comprehensive test coverage tracking

## 📦 Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 13+
- Git

### Backend Setup
```bash
# Navigate to backend directory
cd apps/app-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
python setup_supabase.py

# Start the development server
uvicorn main:app --reload --port 8000
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd apps/realtime-gateway

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# Start the development server
npm run dev
```

### Database Setup
```bash
# Run the database setup script
python check_and_create_tables.py

# Apply schema migrations
psql -d your_database -f enhanced_rag_context_schema.sql
psql -d your_database -f tenant_isolation_schema.sql
```

## 🧪 Testing

### Backend Testing
```bash
# Run all backend tests
cd apps/app-api
python -m pytest

# Run with coverage
python -m pytest --cov=. --cov-report=html

# Run specific test suites
python run_rag_tests.py
python test_runner_95_coverage.py
```

### Frontend Testing
```bash
# Run all frontend tests
cd apps/realtime-gateway
npm test

# Run with coverage
npm run test:coverage

# Run integration tests
npm run test:integration
```

### End-to-End Testing
```bash
# Run comprehensive test suite
./run_ci_tests.sh

# Run RAG-specific tests
./run_rag_tests.sh
```

## 🚀 Deployment

### Production Deployment
```bash
# Build frontend
cd apps/realtime-gateway
npm run build

# Deploy backend
cd apps/app-api
pip install -r requirements.txt
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker Deployment
```bash
# Build and run with Docker
docker-compose up -d

# Scale services
docker-compose up -d --scale backend=3
```

### Environment Configuration
- **Development**: Local development with hot reload
- **Staging**: Pre-production testing environment
- **Production**: Live production environment with monitoring

## 📊 Monitoring & Analytics

### Built-in Monitoring
- **Performance Metrics**: Response times and throughput tracking
- **Error Tracking**: Comprehensive error logging and alerting
- **Usage Analytics**: Feature usage and performance analytics
- **Security Monitoring**: Real-time security violation detection

### Compliance & Auditing
- **Audit Logging**: Complete audit trail for all operations
- **Compliance Reporting**: Automated compliance report generation
- **Data Retention**: Configurable data retention policies
- **Access Logging**: Complete user access and activity logging

## 🔧 Configuration

### Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/pitcrew_labs
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Security Configuration
JWT_SECRET=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key

# Feature Flags
ENABLE_RAG_FEATURES=true
ENABLE_CROSS_TENANT_SHARING=true
ENABLE_AUDIT_LOGGING=true
```

### Feature Configuration
- **RAG Features**: Enable/disable specific AI features
- **Tenant Isolation**: Configure isolation policies
- **Quota Management**: Set organization quotas and limits
- **Security Policies**: Configure security and access policies

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards
- **Python**: Follow PEP 8 guidelines
- **TypeScript**: Use strict type checking
- **Testing**: Maintain 95%+ test coverage
- **Documentation**: Update documentation for all changes

## 📚 Documentation

### API Documentation
- **Backend API**: Available at `/docs` when running the backend
- **Frontend Components**: Comprehensive component documentation
- **Database Schema**: Complete database schema documentation

### User Guides
- **Admin Guide**: Complete administration guide
- **User Guide**: End-user documentation
- **Developer Guide**: Technical implementation guide
- **Deployment Guide**: Production deployment instructions

## 🆘 Support

### Getting Help
- **Documentation**: Check the comprehensive documentation
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join community discussions
- **Email**: Contact support at support@pitcrew-labs.com

### Community
- **GitHub**: [PitCrew Labs Repository](https://github.com/your-org/pcl-app)
- **Discord**: Join our community Discord server
- **Twitter**: Follow us @PitCrewLabs

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Supabase**: For the excellent backend-as-a-service platform
- **FastAPI**: For the modern Python web framework
- **React**: For the powerful UI library
- **Tailwind CSS**: For the utility-first CSS framework
- **All Contributors**: Thank you to all contributors who help make PitCrew Labs better

---

**PitCrew Labs** - Empowering sales teams with AI-driven intelligence and collaboration. 🏁🚀
