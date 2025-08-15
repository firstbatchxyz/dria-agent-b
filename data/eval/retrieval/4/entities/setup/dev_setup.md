# Development Setup Guide
## Prerequisites

**Required Software:**
- Node.js 18.x or higher
- MongoDB 6.0+
- Docker Desktop
- Git

**Development Tools:**
- VS Code (recommended)
- Postman for API testing
- MongoDB Compass for database management

## Installation Steps

### 1. Repository Setup
```bash
git clone https://github.com/kankun-team/kankun-app.git
cd kankun-app
npm install
```

### 2. Environment Configuration
```bash
cp .env.example .env.local
# Configure the following variables:
# - DATABASE_URL
# - JWT_SECRET
# - GOOGLE_MAPS_API_KEY
```

### 3. Database Setup
```bash
docker-compose up -d mongodb
npm run db:migrate
npm run db:seed
```

### 4. Start Development Servers
```bash
# Terminal 1 - Backend
npm run dev:backend

# Terminal 2 - Frontend  
npm run dev:frontend
```

## Development Workflow

**Branch Strategy:** Feature branches from `develop`, PRs to `develop`, releases from `main`

**Code Standards:** ESLint + Prettier configuration, pre-commit hooks enabled

**Testing:** Jest for unit tests, Cypress for E2E testing

## Troubleshooting

**Common Issues:** [[setup/troubleshooting.md]]

**Team Support:** #dev-help Slack channel