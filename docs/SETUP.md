# Complete Setup Guide

## 🚀 Prerequisites

### Required Software

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **PostgreSQL 15+** - [Download](https://www.postgresql.org/download/)
- **Git** - [Download](https://git-scm.com/downloads)

### Package Manager Setup (Recommended)

We use **uv** as our Python package manager for faster dependency resolution:

```bash
# Install uv (cross-platform)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv

# Verify installation
uv --version
```

## 🛠️ Local Development Setup

### 1. Repository Setup

```bash
git clone https://github.com/Fidelisaboke/nature-quest.git
cd nature-quest
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

```

### 3. Automated Setup (Recommended)

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run complete setup
./scripts/setup-db.sh

# Handles eberything
./scripts/run-local.sh
```

### 4. Manual Setup (Alternative)

```bash
# Create virtual environment with uv
uv venv nature-quest --python 3.11

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies with uv (faster)
uv pip install -r requirements.txt

# Set up database
./scripts/setup-db.sh

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### 5. Start Development Server

```bash
# Quick start (handles everything)
./scripts/run-local.sh

# Or manually
source venv/bin/activate
python manage.py runserver
```

### 6. Verify Installation

**Health Check:** [http://localhost:8000/api/v1/health/](http://localhost:8000/api/v1/health/)

Expected Response:

```json
{
  "status": "ok",
  "timestamp": "2025-01-06T12:00:00Z",
  "django": "5.2.6",
  "python": "3.11.x"
}
```

**Admin Panel:** [http://localhost:8000/admin/](http://localhost:8000/admin/)

## 🐳 Docker Development

### Quick Docker Setup

```bash
git clone https://github.com/your-username/nature-quest.git
cd nature-quest

# Environment setup
cp .env.example .env
# Edit .env with your settings

# Start all services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### Docker Operations

```bash
# View logs
docker-compose logs web
docker-compose logs db

# Access containers
docker-compose exec web bash
docker-compose exec db psql -U nature_quest_user -d nature_quest

# Django commands in container
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell

# Stop services
docker-compose down
```

## 🚨 Troubleshooting

### Common Issues

**1. PostgreSQL Connection Error**

```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**

- Verify PostgreSQL is running: `brew services start postgresql` (macOS)
- Check `.env` database credentials
- Run database setup: `./scripts/setup-db.sh`

**2. Virtual Environment Issues**

```
ModuleNotFoundError: No module named 'django'
```

**Solutions:**

```bash
source venv/bin/activate
uv pip install -r requirements.txt
```

**3. Migration Issues**

```
django.db.migrations.exceptions.InconsistentMigrationHistory
```

**Solutions:**

```bash
python manage.py migrate --fake-initial
# or
python manage.py migrate your_app zero
python manage.py migrate
```

**4. Docker Port Conflicts**

```
Error: port is already allocated
```

**Solutions:**

```bash
docker-compose down
sudo lsof -i :8000
sudo kill -9 <PID>
```

**5. UV Installation Issues**

```bash
# Alternative installation methods
pip install uv
# or
conda install -c conda-forge uv
```

### Performance Optimization

**Development Mode:**

```bash
# Use uv for faster installs
uv pip install -r requirements.txt

# Enable Django debug toolbar
uv pip install django-debug-toolbar
```

## 📋 Checklist for New Developers

- [ ] Python 3.11+ installed
- [ ] PostgreSQL 15+ installed
- [ ] UV package manager installed
- [ ] Repository cloned
- [ ] `.env` file configured
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Database setup completed
- [ ] Migrations applied
- [ ] Health endpoint accessible
- [ ] Admin panel accessible

## 🔗 Useful Resources

- **Django Documentation**: [docs.djangoproject.com](https://docs.djangoproject.com/)
- **PostgreSQL Guide**: [postgresql.org/docs](https://www.postgresql.org/docs/)
- **UV Package Manager**: [github.com/astral-sh/uv](https://github.com/astral-sh/uv)
- **Docker Compose**: [docs.docker.com/compose](https://docs.docker.com/compose/)

---

**Need more help?** Check our [GitHub Discussions](https://github.com/your-username/nature-quest/discussions) or create an [issue](https://github.com/your-username/nature-quest/issues).
