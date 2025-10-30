# Contributing to SCAILE Notification System

**Thank you for considering contributing!** 🎉

We welcome contributions from everyone. This document will help you get started.

---

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How to Contribute](#how-to-contribute)
3. [Development Setup](#development-setup)
4. [Code Style](#code-style)
5. [Testing](#testing)
6. [Pull Request Process](#pull-request-process)
7. [Issue Guidelines](#issue-guidelines)
8. [Project Structure](#project-structure)

---

## 🤝 Code of Conduct

This project adheres to a Code of Conduct based on the [Contributor Covenant](https://www.contributor-covenant.org/).

**TL;DR:** Be respectful, inclusive, and professional.

---

## 🚀 How to Contribute

### Ways to Contribute

- 🐛 **Report bugs** - Found a bug? [Open an issue](https://github.com/SCAILE-it/gtm-notification-system/issues/new?template=bug_report.md)
- ✨ **Request features** - Have an idea? [Submit a feature request](https://github.com/SCAILE-it/gtm-notification-system/issues/new?template=feature_request.md)
- 📝 **Improve documentation** - Fix typos, clarify instructions, add examples
- 🧪 **Write tests** - Improve test coverage
- 🎨 **Design email templates** - Create beautiful, accessible templates
- 🛠️ **Fix bugs** - Pick an [issue labeled `good first issue`](https://github.com/SCAILE-it/gtm-notification-system/labels/good%20first%20issue)
- 💡 **Implement features** - See [ROADMAP.md](ROADMAP.md) for planned features

---

## 🛠️ Development Setup

### Prerequisites

- **Python 3.12+**
- **Node.js 18+** (for Edge Functions)
- **Docker** (for integration tests)
- **Git**

### 1. Fork and Clone

```bash
# Fork the repo on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/gtm-notification-system.git
cd gtm-notification-system

# Add upstream remote
git remote add upstream https://github.com/SCAILE-it/gtm-notification-system.git
```

### 2. Install Dependencies

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Supabase CLI (optional, for Edge Functions)
npm install -g supabase
```

### 3. Set Up Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your keys (for local testing)
# You can leave most values as-is for development
```

### 4. Start Test Environment

```bash
# Start local Supabase + MailHog
docker-compose up -d

# Verify services are running
docker-compose ps

# Run integration tests
python tests/test_full_flow.py
```

### 5. Make Changes

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes
# Write tests
# Run tests locally

# Commit your changes
git add .
git commit -m "feat: add your feature description"

# Push to your fork
git push origin feature/your-feature-name
```

### 6. Open Pull Request

- Go to your fork on GitHub
- Click "Compare & pull request"
- Fill out the PR template
- Wait for review

---

## 💅 Code Style

### Python

We follow **PEP 8** with these modifications:

- **Line length:** 100 characters (not 79)
- **Type hints:** Required for all functions
- **Docstrings:** Google style

**Example:**
```python
async def send_notification(
    user_id: str,
    notification_type: NotificationType,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send a notification to a user.

    Args:
        user_id: User UUID
        notification_type: Type of notification
        data: Notification data

    Returns:
        {"success": bool, "email_id": Optional[str]}

    Raises:
        RateLimitExceeded: If rate limit is hit
    """
    pass
```

**Tools:**
- **Formatter:** `black backend/` (auto-format)
- **Linter:** `flake8 backend/` (check style)
- **Type Checker:** `mypy backend/` (type checking)

### TypeScript/JavaScript

We follow **Airbnb style** with Prettier:

- **Semicolons:** Yes
- **Quotes:** Single quotes
- **Indent:** 2 spaces
- **Trailing commas:** Yes

**Tools:**
- **Formatter:** `prettier --write .`
- **Linter:** `eslint .`

### General Principles

- ✅ **SOLID** - Single responsibility, Open/closed, Liskov substitution, Interface segregation, Dependency inversion
- ✅ **DRY** - Don't repeat yourself
- ✅ **KISS** - Keep it simple, stupid
- ✅ **Write tests** - All new features need tests
- ✅ **Document** - Add docstrings and comments
- ❌ **No console.log** - Remove before committing
- ❌ **No commented code** - Delete or document why

---

## 🧪 Testing

### Run Tests

```bash
# Unit tests
cd backend
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Integration tests
docker-compose up -d
python tests/test_full_flow.py
```

### Writing Tests

**Unit tests** go in `backend/tests/`:
```python
@pytest.mark.asyncio
async def test_send_notification():
    """Test sending a notification"""
    # Arrange
    ns = NotificationSystem(...)

    # Act
    result = await ns.send_job_complete(...)

    # Assert
    assert result['success'] is True
```

**Integration tests** go in `tests/`:
```python
def test_full_notification_flow():
    """Test complete workflow"""
    # Start services, send email, verify in MailHog, check DB
    pass
```

### Test Coverage

- **Minimum:** 70% overall
- **Goal:** 85%+ for new code
- **Critical paths:** 95%+ (email sending, preferences, rate limiting)

---

## 📬 Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass (`pytest tests/`)
- [ ] New tests added for new features
- [ ] Documentation updated (README, API docs, etc.)
- [ ] Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
- [ ] No console.log or debugger statements
- [ ] Type hints added (Python)

### PR Title Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add welcome email functionality
fix: resolve rate limiter race condition
docs: update integration guide with examples
test: add tests for Sentry integration
refactor: extract email rendering to templates
chore: update dependencies
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `perf:` - Performance improvement
- `chore:` - Maintenance

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How did you test this?

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No console.log statements
- [ ] Follows code style guidelines

## Related Issues
Closes #123
```

### Review Process

1. **Automated checks** - CI/CD runs tests and linters
2. **Maintainer review** - At least one approval required
3. **Feedback** - Address review comments
4. **Merge** - Squash and merge when approved

### After Merge

- Delete your feature branch
- Update your fork:
  ```bash
  git checkout main
  git pull upstream main
  git push origin main
  ```

---

## 🐛 Issue Guidelines

### Bug Reports

Use the [bug report template](https://github.com/SCAILE-it/gtm-notification-system/issues/new?template=bug_report.md).

**Include:**
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment (Python version, OS, etc.)
- Error messages/logs
- Screenshots if relevant

### Feature Requests

Use the [feature request template](https://github.com/SCAILE-it/gtm-notification-system/issues/new?template=feature_request.md).

**Include:**
- Problem you're trying to solve
- Proposed solution
- Alternative solutions considered
- Use case examples

### Questions

For questions, use [GitHub Discussions](https://github.com/SCAILE-it/gtm-notification-system/discussions) instead of issues.

---

## 📁 Project Structure

```
gtm-notification-system/
├── backend/
│   ├── notifications.py       # Main notification module
│   ├── rate_limiter.py        # Rate limiting
│   ├── monitoring.py          # Sentry integration
│   ├── templates/             # Jinja2 email templates
│   │   ├── base.html          # Base template
│   │   ├── job_complete.html  # Job complete email
│   │   ├── job_failed.html    # Job failed email
│   │   └── quota_warning.html # Quota warning email
│   ├── tests/                 # Unit tests
│   │   ├── conftest.py        # Test fixtures
│   │   └── test_*.py          # Test files
│   └── requirements.txt       # Python dependencies
│
├── supabase/
│   ├── functions/             # Edge Functions (Deno)
│   │   ├── resend-webhook/    # Webhook handler
│   │   ├── send-welcome-email/ # Welcome email
│   │   └── _shared/           # Shared utilities
│   └── migrations/            # Database migrations
│       ├── 00_setup_auth_mock.sql
│       └── 20250128_notification_tables.sql
│
├── frontend/
│   └── components/            # React components
│       ├── NotificationPreferences.tsx
│       └── EmailStatsCard.tsx
│
├── tests/
│   ├── test_full_flow.py      # Integration tests
│   └── conftest.py            # Test fixtures
│
├── scripts/
│   ├── reset_local_db.sh      # Reset test database
│   └── send_test_emails.py    # Send test emails
│
├── docs/
│   ├── API.md                 # API documentation
│   ├── INTEGRATION_GUIDE.md   # Integration guide
│   └── EMAIL_VISUAL_CHECKLIST.md  # Email QA
│
├── docker-compose.yml         # Test environment
├── README.md                  # Project README
├── ROADMAP.md                 # Product roadmap
├── CHANGELOG.md               # Version history
├── CONTRIBUTING.md            # This file
└── .env.example               # Environment template
```

### Key Files to Know

- **`backend/notifications.py`** - Main notification system class
- **`backend/rate_limiter.py`** - Rate limiting implementation
- **`backend/monitoring.py`** - Sentry integration
- **`backend/templates/`** - Email HTML templates (Jinja2)
- **`supabase/migrations/`** - Database schema
- **`docs/API.md`** - Complete API reference

---

## 🎯 Good First Issues

Looking for something to work on? Check out issues labeled [`good first issue`](https://github.com/SCAILE-it/gtm-notification-system/labels/good%20first%20issue).

**Suggestions for first contributions:**
- Add more email templates
- Improve test coverage
- Fix typos in documentation
- Add examples to API docs
- Create visual email templates

---

## 📝 License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT).

---

## 💬 Communication

- **GitHub Issues** - Bug reports, feature requests
- **GitHub Discussions** - Questions, ideas
- **Pull Requests** - Code contributions
- **Email** - For security issues: security@g-gpt.com

---

## 🙏 Thank You!

Your contributions make this project better. We appreciate your time and effort!

**Happy coding!** 🚀

---

**Links:**
- [Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [ROADMAP.md](ROADMAP.md)
- [CHANGELOG.md](CHANGELOG.md)
