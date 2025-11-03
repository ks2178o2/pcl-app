"""Wrapper for Elastic Beanstalk compatibility"""
import sys
from pathlib import Path

# Add apps/app-api to Python path
app_api_path = Path(__file__).parent / "apps" / "app-api"
sys.path.insert(0, str(app_api_path))

from main import app

# EB looks for 'application' variable
application = app
