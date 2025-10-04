#!/usr/bin/env bash
# Production build script for Render deployment
# This script is automatically executed by Render during deployment

set -o errexit  # Exit immediately if any command fails

echo "🔧 Installing Python dependencies..."
pip install -r requirements.txt

echo "📦 Collecting static files for production..."
python manage.py collectstatic --no-input

echo "🗄️  Running database migrations..."
python manage.py migrate

echo "✅ Build completed successfully!"
