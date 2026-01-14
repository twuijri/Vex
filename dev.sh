#!/bin/bash
# Quick development scripts for CoffeeBot

set -e

case "${1:-help}" in
  # Local development
  dev)
    echo "🚀 Starting local development..."
    python3 -m bot
    ;;
  
  # Docker local
  docker-up)
    echo "🐳 Starting with Docker Compose..."
    docker-compose up -d
    echo "✅ Bot is running"
    docker-compose logs -f bot
    ;;
  
  docker-down)
    echo "⬇️  Stopping Docker Compose..."
    docker-compose down
    echo "✅ Bot stopped"
    ;;
  
  docker-logs)
    echo "📋 Bot logs:"
    docker-compose logs -f bot
    ;;
  
  docker-restart)
    echo "🔄 Restarting bot..."
    docker-compose restart bot
    docker-compose logs -f bot
    ;;
  
  # Database
  db-test)
    echo "🧪 Testing database connection..."
    python3 << 'EOF'
import asyncio
from bot.core.config import config
from motor.motor_asyncio import AsyncIOMotorClient

async def test():
    try:
        client = AsyncIOMotorClient(config.MONGO_URI)
        await client.admin.command('ping')
        print("✅ Database connection OK")
        db = client[config.MONGO_DB_NAME]
        collections = await db.list_collection_names()
        print(f"📊 Collections: {collections}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

asyncio.run(test())
EOF
    ;;
  
  # Build
  build)
    echo "🔨 Building Docker image..."
    docker build -t abdulaziz/coffeebot:latest .
    echo "✅ Build complete"
    ;;
  
  # Help
  *)
    echo "CoffeeBot Development Tools"
    echo ""
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  dev              - Run bot locally"
    echo "  docker-up        - Start with Docker Compose"
    echo "  docker-down      - Stop Docker Compose"
    echo "  docker-logs      - View bot logs"
    echo "  docker-restart   - Restart bot container"
    echo "  db-test          - Test database connection"
    echo "  build            - Build Docker image"
    echo ""
    ;;
esac
