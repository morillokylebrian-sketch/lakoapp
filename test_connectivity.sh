#!/bin/bash
# Quick connectivity test for Lako backend

echo "🔍 Testing Lako Backend Connectivity..."
echo ""

BASE_URL="http://localhost:5000/api"

# Test health check
echo "1. Testing API Health..."
curl -s "$BASE_URL/health" | jq . && echo "✅ Health check passed" || echo "❌ Health check failed"
echo ""

# Test API index
echo "2. Testing API Index..."
curl -s "$BASE_URL" | jq . && echo "✅ API index passed" || echo "❌ API index failed"
echo ""

# Test guest endpoints (no auth required)
echo "3. Testing Guest Endpoints..."
GUEST_TEST=$(curl -s "$BASE_URL/guest/vendors?lat=14.5995&lng=120.9842" | jq .)
if echo "$GUEST_TEST" | grep -q "vendors"; then
    echo "✅ Guest vendors endpoint works"
else
    echo "⚠️  Guest vendors endpoint responded"
fi
echo ""

# Test authentication
echo "4. Testing Authentication..."
LOGIN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@lako.com","password":"admin123"}' | jq .)

TOKEN=$(echo "$LOGIN" | jq -r '.session_token // empty')
if [ ! -z "$TOKEN" ]; then
    echo "✅ Authentication successful (token: ${TOKEN:0:10}...)"
    
    # Test authenticated endpoint
    echo ""
    echo "5. Testing Authenticated Endpoints..."
    curl -s "$BASE_URL/auth/me" \
      -H "X-Session-Token: $TOKEN" | jq . && echo "✅ Auth endpoint works" || echo "❌ Auth endpoint failed"
else
    echo "❌ Authentication failed"
fi

echo ""
echo "================================"
echo "✅ Connectivity Tests Complete"
echo "================================"
