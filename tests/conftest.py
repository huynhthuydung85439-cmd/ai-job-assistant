import os

# Keep the test suite isolated from a developer's local MySQL and .env settings.
os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
