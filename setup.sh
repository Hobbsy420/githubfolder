#!/bin/bash

# Create virtual environment for Python
echo "Setting up Python virtual environment..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up frontend
echo "Setting up Next.js frontend..."
cd ../frontend
npm install

echo "Setup complete!"
echo "To start the backend: cd backend && source venv/bin/activate && python -m flask run"
echo "To start the frontend: cd frontend && npm run dev"
