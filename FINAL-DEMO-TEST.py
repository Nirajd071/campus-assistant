#!/usr/bin/env python3
"""
KPRIET Campus Assistant - Final Demo Test Script
Tests all multilingual functionality for submission
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Test endpoints
BACKEND_URL = "http://localhost:3007"
NLP_ENGINE_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3008"

# Test languages and queries
TEST_LANGUAGES = {
    'en': {
        'name': 'English',
        'queries': [
            "Hello, I need help with fee information",
            "What are the library hours?",
            "Tell me about scholarships",
            "When are the exams scheduled?"
        ]
    },
    'hi': {
        'name': 'Hindi (हिंदी)',
        'queries': [
            "नमस्ते, मुझे फीस की जानकारी चाहिए",
            "पुस्तकालय का समय क्या है?",
            "छात्रवृत्ति के बारे में बताएं",
            "परीक्षा कब है?"
        ]
    },
    'bn': {
        'name': 'Bengali (বাংলা)',
        'queries': [
            "হ্যালো, আমার ফি সম্পর্কে তথ্য দরকার",
            "লাইব্রেরির সময় কি?",
            "বৃত্তি সম্পর্কে বলুন",
            "পরীক্ষা কখন?"
        ]
    },
    'ta': {
        'name': 'Tamil (தமிழ்)',
        'queries': [
            "வணக்கம், எனக்கு கட்டணம் பற்றிய தகவல் வேண்டும்",
            "நூலகத்தின் நேரம் என்ன?",
            "உதவித்தொகை பற்றி சொல்லுங்கள்",
            "தேர்வுகள் எப்போது?"
        ]
    }
}

class DemoTester:
    def __init__(self):
        self.session = None
        self.results = {
            'services_status': {},
            'multilingual_tests': {},
            'performance_metrics': {},
            'demo_ready': False
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_service_health(self, service_name: str, url: str) -> bool:
        """Check if a service is running and healthy"""
        try:
            async with self.session.get(f"{url}/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    self.results['services_status'][service_name] = {
                        'status': 'healthy',
                        'response_time': data.get('response_time', 'N/A'),
                        'timestamp': datetime.now().isoformat()
                    }
                    print(f"✅ {service_name}: HEALTHY")
                    return True
                else:
                    print(f"❌ {service_name}: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ {service_name}: {str(e)}")
            self.results['services_status'][service_name] = {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return False
    
    async def test_multilingual_chat(self, language: str, query: str) -> dict:
        """Test multilingual chat functionality"""
        try:
            start_time = time.time()
            
            # Test chat endpoint
            payload = {
                "message": query,
                "language": language,
                "session_id": f"demo_test_{language}",
                "student_id": "DEMO_STUDENT_001"
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/api/chat",
                json=payload,
                timeout=15
            ) as response:
                
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    result = {
                        'status': 'success',
                        'query': query,
                        'response': data.get('response', ''),
                        'language_detected': data.get('language', language),
                        'intent': data.get('intent', 'unknown'),
                        'confidence': data.get('confidence', 0),
                        'response_time': round(response_time, 2),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    print(f"✅ {language.upper()}: {query[:50]}... -> {len(data.get('response', ''))} chars")
                    return result
                else:
                    print(f"❌ {language.upper()}: HTTP {response.status}")
                    return {
                        'status': 'error',
                        'query': query,
                        'error': f"HTTP {response.status}",
                        'response_time': round(response_time, 2)
                    }
                    
        except Exception as e:
            print(f"❌ {language.upper()}: {str(e)}")
            return {
                'status': 'error',
                'query': query,
                'error': str(e),
                'response_time': 0
            }
    
    async def run_comprehensive_demo_test(self):
        """Run comprehensive demo test for all functionality"""
        print("🎓 KPRIET CAMPUS ASSISTANT - FINAL DEMO TEST")
        print("=" * 60)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. Check all services
        print("1️⃣ CHECKING SERVICE HEALTH...")
        services = [
            ("Backend API", BACKEND_URL),
            ("NLP Engine", NLP_ENGINE_URL),
            ("Frontend", FRONTEND_URL)
        ]
        
        all_services_healthy = True
        for service_name, url in services:
            is_healthy = await self.check_service_health(service_name, url)
            if not is_healthy:
                all_services_healthy = False
        
        print()
        
        # 2. Test multilingual functionality
        print("2️⃣ TESTING MULTILINGUAL FUNCTIONALITY...")
        
        for lang_code, lang_data in TEST_LANGUAGES.items():
            print(f"\n🌍 Testing {lang_data['name']}:")
            self.results['multilingual_tests'][lang_code] = {
                'language_name': lang_data['name'],
                'tests': []
            }
            
            for query in lang_data['queries']:
                result = await self.test_multilingual_chat(lang_code, query)
                self.results['multilingual_tests'][lang_code]['tests'].append(result)
                
                # Small delay between requests
                await asyncio.sleep(1)
        
        print()
        
        # 3. Calculate performance metrics
        print("3️⃣ CALCULATING PERFORMANCE METRICS...")
        
        total_tests = 0
        successful_tests = 0
        total_response_time = 0
        
        for lang_code, lang_results in self.results['multilingual_tests'].items():
            for test in lang_results['tests']:
                total_tests += 1
                if test['status'] == 'success':
                    successful_tests += 1
                    total_response_time += test.get('response_time', 0)
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        avg_response_time = (total_response_time / successful_tests) if successful_tests > 0 else 0
        
        self.results['performance_metrics'] = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': round(success_rate, 1),
            'average_response_time': round(avg_response_time, 2),
            'languages_tested': len(TEST_LANGUAGES)
        }
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"📊 Successful: {successful_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        print(f"📊 Avg Response Time: {avg_response_time:.2f}s")
        print()
        
        # 4. Final assessment
        print("4️⃣ FINAL DEMO ASSESSMENT...")
        
        demo_ready = (
            all_services_healthy and 
            success_rate >= 80 and 
            avg_response_time <= 10
        )
        
        self.results['demo_ready'] = demo_ready
        
        if demo_ready:
            print("🎉 DEMO READY FOR SUBMISSION!")
            print("✅ All services are healthy")
            print("✅ Multilingual functionality working")
            print("✅ Performance metrics acceptable")
        else:
            print("⚠️  DEMO NEEDS ATTENTION!")
            if not all_services_healthy:
                print("❌ Some services are not healthy")
            if success_rate < 80:
                print("❌ Success rate below 80%")
            if avg_response_time > 10:
                print("❌ Response time too slow")
        
        print()
        
        # 5. Save detailed results
        results_file = f"demo_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detailed results saved to: {results_file}")
        print()
        
        return demo_ready

async def main():
    """Main demo test function"""
    async with DemoTester() as tester:
        demo_ready = await tester.run_comprehensive_demo_test()
        
        print("=" * 60)
        if demo_ready:
            print("🎓 KPRIET CAMPUS ASSISTANT IS READY FOR SUBMISSION! 🎓")
        else:
            print("⚠️  Please fix issues before submission")
        print("=" * 60)
        
        return demo_ready

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        exit(1)
