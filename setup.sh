#!/bin/bash

# OpsLens Setup Script

echo "🚀 Setting up OpsLens..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Check if secrets.env exists
if [ ! -f "secrets.env" ]; then
    echo "📝 Creating secrets.env from template..."
    cp secrets.env.example secrets.env
    echo "⚠️  Please edit secrets.env and add your API keys before continuing."
    echo "   Required keys:"
    echo "   - HUGGINGFACE_API_KEY"
    echo "   - GITHUB_API_KEY"
    echo "   - PAGERDUTY_API_KEY"
    read -p "Press Enter after you've added your API keys..."
fi

# Create artifacts directory
mkdir -p artifacts

# Start Docker containers
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Initialize database
echo "🗄️  Initializing database..."
docker-compose exec -T backend python -m app.db.init_db

# Generate synthetic data (optional)
read -p "Generate synthetic data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📊 Generating synthetic data..."
    docker-compose exec -T backend python -m app.data.generate_synthetic
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📝 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 To stop:"
echo "   docker-compose down"

