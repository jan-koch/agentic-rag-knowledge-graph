#!/usr/bin/env python3
"""
Test script for n8n integration endpoints.
"""

import asyncio
import json
import aiohttp
import sys

async def test_n8n_endpoints():
    """Test the n8n integration endpoints."""
    base_url = "http://127.0.0.1:8058"
    
    # Test data
    test_cases = [
        {
            "name": "Chat Trigger Format",
            "endpoint": "/n8n/chat",
            "payload": {
                "chatInput": "What is the purpose of this RAG system?",
                "sessionId": None,
                "userId": "test-user"
            }
        },
        {
            "name": "Simple Webhook Format",
            "endpoint": "/n8n/simple", 
            "payload": {
                "message": "How does vector search work?"
            }
        },
        {
            "name": "Alternative Message Field",
            "endpoint": "/n8n/chat",
            "payload": {
                "question": "Tell me about the knowledge graph.",
                "userId": "test-user-2"
            }
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for test_case in test_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            print(f"📍 Endpoint: {test_case['endpoint']}")
            
            try:
                async with session.post(
                    f"{base_url}{test_case['endpoint']}",
                    json=test_case["payload"],
                    headers={"Content-Type": "application/json"}
                ) as response:
                    status = response.status
                    content = await response.json()
                    
                    print(f"✅ Status: {status}")
                    if status == 200:
                        if test_case['endpoint'] == '/n8n/simple':
                            print(f"📄 Answer: {content.get('answer', 'No answer field')[:100]}...")
                        else:
                            print(f"📄 Response: {content.get('response', 'No response field')[:100]}...")
                            print(f"🔧 Tools Used: {content.get('toolsUsed', 0)}")
                    else:
                        print(f"❌ Error: {content}")
                        
            except aiohttp.ClientConnectorError:
                print("❌ Connection failed - make sure the API server is running on port 8058")
                print("   Start it with: python -m agent.api")
                break
            except Exception as e:
                print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🚀 Testing n8n Integration Endpoints")
    print("=" * 50)
    
    try:
        asyncio.run(test_n8n_endpoints())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        sys.exit(1)