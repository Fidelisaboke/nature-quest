# Nature Quest 🌲

A gamified backend service that helps people reconnect with nature through location-based quests and environmental challenges.

[![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=flat&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-316192?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-20.10+-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-package%20manager-FF6B6B?style=flat)](https://github.com/astral-sh/uv)

## 🌟 Features

- **Location-Based Quests:** GPS-enabled nature discovery challenges
- **Gamification System:** Points, badges, and achievement tracking
- **Environmental Impact:** Carbon footprint tracking and offset suggestions
- **Community Features:** Social sharing and group challenges
- **REST API:** Comprehensive API for mobile and web applications
- **Real-time Updates:** Live quest progress and notifications

## 🚀 Quick Start

**See [Setup Guide](docs/SETUP.md) for full instructions.**

### Prerequisites

- Python 3.11+ (with [uv](https://github.com/astral-sh/uv) package manager recommended)
- PostgreSQL 15+
- Git

### 5-Minute Setup

```bash
git clone https://github.com/Fidelisaboke/nature-quest.git
cd nature-quest

# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

cp .env.example .env  # Edit with your database credentials

chmod +x scripts/*.sh
./scripts/setup-db.sh

./scripts/run-local.sh
```

### Verify Installation

- Health check: [http://localhost:8000/api/v1/health/](http://localhost:8000/api/v1/health/) → Should return `{"status": "ok"}`
- Admin panel: [http://localhost:8000/admin/](http://localhost:8000/admin/)

### Docker Alternative

```bash
git clone https://github.com/Fidelisaboke/nature-quest.git
cd nature-quest
cp .env.example .env  # Edit with your settings
docker-compose up --build
```

## 📚 Documentation

- [Setup Guide](docs/SETUP.md)
- [Development Guide](docs/DEVELOPMENT.md)

## 🏗️ Project Structure

```
nature-quest/
├── apps/                    # Django applications
│   ├── backend/            # Core settings and configuration
│   └── health/             # Health check endpoints
├── docs/                   # Project documentation
├── scripts/                # Development and deployment scripts
├── requirements.txt        # Python dependencies (uv compatible)
├── docker-compose.yml      # Multi-service orchestration
└── manage.py              # Django management interface
```

## ⚡ Common Commands

```bash
./scripts/run-local.sh                # Start development server
python manage.py makemigrations       # Create new migrations
python manage.py migrate              # Apply migrations
python manage.py createsuperuser      # Create admin user
python manage.py test                 # Run all tests
docker-compose up --build             # Start Docker services
docker-compose exec web python manage.py shell  # Django shell in container
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Follow [Development Guide](docs/DEVELOPMENT.md)
4. Submit a pull request

**Commit Convention:** [Conventional Commits](https://www.conventionalcommits.org/)

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation
- `refactor:` Code refactoring

## 🆘 Need Help?

- [Setup Guide](docs/SETUP.md)
- [GitHub Issues](https://github.com/Fidelisaboke/nature-quest/issues)
- [GitHub Discussions](https://github.com/Fidelisaboke/nature-quest/discussions)

## 📄 License

MIT License – see [LICENSE](LICENSE) for details.
