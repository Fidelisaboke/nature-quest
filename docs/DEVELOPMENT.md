# 🛠️ Development Guide

This document outlines the recommended workflow, coding standards, and security practices for this project.

---

## 🔧 Development Workflow

### Package Management (UV)

```bash
# Add new dependency
uv pip install package_name

# Update requirements.txt
uv pip freeze > requirements.txt

# Install from requirements
uv pip install -r requirements.txt

# Sync environment (removes unused packages)
uv pip sync requirements.txt
```

### Adding New Apps

```bash
# Create new Django app
python manage.py startapp your_app apps/your_app

# Update settings.py
# Add 'your_app' to LOCAL_APPS list

# Create app URLs
touch apps/your_app/urls.py

# Include in main URLs
# Add path to apps/backend/urls.py
```

### Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.health

# Run with coverage
uv pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Code Quality

```bash
# Install development tools
uv pip install ruff

# Format and lint code
ruff check .
ruff format .
```

### Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

## 🔐 Security Considerations

- **Secret Key**: Generate a unique secret key for production
- **Database**: Use strong passwords and enable SSL
- **CORS**: Configure allowed origins for production
- **DEBUG**: Always set `DEBUG=False` in production
- **HTTPS**: Use HTTPS in production environments
- **Environment Variables**: Never commit sensitive data to version control
