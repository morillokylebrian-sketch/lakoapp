#!/bin/bash

echo "================================================"
echo "🚀 Lako Platform - Simple Runner (No venv)"
echo "================================================"
echo ""

# Check directories
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ ERROR: Run from Lako project root"
    exit 1
fi

# ============================================
# BACKEND
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Starting Backend"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd backend

# Install missing packages if needed
echo "📦 Checking dependencies..."
pip3 install Flask Flask-CORS Flask-SocketIO python-socketio bcrypt Pillow python-dotenv geopy requests eventlet -q 2>/dev/null

# Create .env if missing
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
SECRET_KEY=dev-secret-key
PORT=5000
DEBUG=True
DATABASE_URL=sqlite:///lako.db
RENDER=false
EOF
fi

# Start backend
python3 run.py &
BACKEND_PID=$!
cd ..

# Wait for backend
sleep 3

# Check backend
if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✅ Backend:  http://localhost:5000"
else
    echo "⚠️  Backend may still be starting..."
    echo "   Check manually: http://localhost:5000/api/health"
fi

# ============================================
# FRONTEND
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎨 Starting Frontend"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd frontend

# Find available port
PORT=3000
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; do
    PORT=$((PORT + 1))
done

python3 -m http.server $PORT &
FRONTEND_PID=$!
cd ..

echo "✅ Frontend: http://localhost:$PORT"

# ============================================
# SUMMARY
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ LAKO IS RUNNING!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   🌐 Backend:  http://localhost:5000"
echo "   🎨 Frontend: http://localhost:$PORT"
echo ""
echo "   👤 Test Accounts:"
echo "      Admin: admin@lako.com / admin123"
echo "      Customer: Register at /pages/register.html"
echo "      Vendor: Register at /pages/register.html?type=vendor"
echo "      Guest: Browse at /pages/guest/browse.html"
echo ""
echo "   📋 API Endpoints:"
echo "      GET  /api/health"
echo "      POST /api/auth/login"
echo "      POST /api/auth/register/customer"
echo "      GET  /api/guest/vendors"
echo ""
echo "   ⚠️  If backend fails:"
echo "      cd backend && pip3 install Flask Flask-CORS"
echo "      python3 run.py"
echo ""
echo "   Press Ctrl+C to stop all services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Cleanup
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Done"
    exit 0
}

trap cleanup INT
wait