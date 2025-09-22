"""
University API Service
Handles integration with university systems for live data
"""

import os
import asyncio
import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class UniversityAPIService:
    def __init__(self):
        self.api_base = os.getenv("UNIVERSITY_API_BASE", "https://api.university.edu")
        self.api_key = os.getenv("UNIVERSITY_API_KEY")
        self.timeout = 10.0
    
    async def get_student_info(self, student_id: str) -> Dict[str, Any]:
        """Get student information from university API"""
        try:
            if not self.api_key:
                logger.warning("University API key not configured")
                return {"error": "API not configured"}
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_base}/students/{student_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"University API error: {response.status_code}")
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"University API connection failed: {e}")
            return {"error": "API connection failed"}
    
    async def get_fee_info(self, student_id: Optional[str] = None) -> Dict[str, Any]:
        """Get fee information"""
        # Mock data for demo - replace with real API call
        return {
            "semester_fee": 75000,
            "due_date": "2024-07-31",
            "late_fee": 5000,
            "payment_methods": ["Online Banking", "UPI", "Card Payment", "Bank Transfer"],
            "status": "pending"
        }
    
    async def get_schedule_info(self, student_id: Optional[str] = None) -> Dict[str, Any]:
        """Get schedule information"""
        # Mock data for demo - replace with real API call
        return {
            "current_semester": "Fall 2024",
            "classes": [
                {"subject": "Computer Science", "time": "09:00-10:30", "room": "CS-101"},
                {"subject": "Mathematics", "time": "11:00-12:30", "room": "MATH-201"},
                {"subject": "Physics", "time": "14:00-15:30", "room": "PHY-301"}
            ],
            "exams": [
                {"subject": "Computer Science", "date": "2024-12-15", "time": "10:00"},
                {"subject": "Mathematics", "date": "2024-12-17", "time": "14:00"}
            ]
        }
    
    async def get_library_info(self) -> Dict[str, Any]:
        """Get library information"""
        # Mock data for demo - replace with real API call
        return {
            "hours": {
                "weekdays": "08:00-22:00",
                "weekends": "10:00-18:00"
            },
            "services": ["Book Borrowing", "Digital Resources", "Study Rooms", "Printing"],
            "available_books": 50000,
            "digital_resources": 10000
        }
    
    async def get_scholarship_info(self) -> Dict[str, Any]:
        """Get scholarship information"""
        # Mock data for demo - replace with real API call
        return {
            "available_scholarships": [
                {
                    "name": "Merit Scholarship",
                    "amount": 25000,
                    "eligibility": "75% marks in previous year",
                    "deadline": "2024-08-15"
                },
                {
                    "name": "Need-based Scholarship", 
                    "amount": 50000,
                    "eligibility": "Family income < 3 lakhs",
                    "deadline": "2024-08-30"
                }
            ]
        }
