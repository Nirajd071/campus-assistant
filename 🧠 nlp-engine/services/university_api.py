"""
University API Integration Service
Connects to real university systems for live data
"""

import os
import json
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from loguru import logger

class UniversityAPIService:
    """
    Service to integrate with real university APIs
    """
    
    def __init__(self):
        self.base_url = os.getenv("UNIVERSITY_API_BASE", "https://api.university.edu")
        self.api_key = os.getenv("UNIVERSITY_API_KEY", "")
        self.timeout = 10  # seconds
        
        # Mock data for when real APIs are not available
        self.mock_mode = os.getenv("USE_MOCK_DATA", "true").lower() == "true"
        
    async def get_student_info(self, student_id: str) -> Dict[str, Any]:
        """Get comprehensive student information"""
        if self.mock_mode:
            return self._get_mock_student_info(student_id)
            
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                url = f"{self.base_url}/students/{student_id}"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Student API returned {response.status}")
                        return self._get_mock_student_info(student_id)
                        
        except Exception as e:
            logger.error(f"Student API error: {e}")
            return self._get_mock_student_info(student_id)
    
    async def get_fee_information(self, student_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current fee structure and student-specific fee details"""
        if self.mock_mode:
            return self._get_mock_fee_info(student_id)
            
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                # Get general fee structure
                fee_url = f"{self.base_url}/fees/current-structure"
                async with session.get(fee_url, headers=headers) as response:
                    if response.status == 200:
                        fee_structure = await response.json()
                    else:
                        fee_structure = self._get_mock_fee_info()
                
                # Get student-specific fees if ID provided
                if student_id:
                    student_fee_url = f"{self.base_url}/students/{student_id}/fees"
                    async with session.get(student_fee_url, headers=headers) as response:
                        if response.status == 200:
                            student_fees = await response.json()
                            fee_structure.update({"student_specific": student_fees})
                
                return fee_structure
                
        except Exception as e:
            logger.error(f"Fee API error: {e}")
            return self._get_mock_fee_info(student_id)
    
    async def get_academic_schedule(self, student_id: Optional[str] = None) -> Dict[str, Any]:
        """Get academic calendar and student-specific schedule"""
        if self.mock_mode:
            return self._get_mock_schedule_info(student_id)
            
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                # Get academic calendar
                calendar_url = f"{self.base_url}/academic/calendar/current"
                async with session.get(calendar_url, headers=headers) as response:
                    if response.status == 200:
                        calendar = await response.json()
                    else:
                        calendar = self._get_mock_schedule_info()
                
                # Get student-specific schedule if ID provided
                if student_id:
                    schedule_url = f"{self.base_url}/students/{student_id}/schedule"
                    async with session.get(schedule_url, headers=headers) as response:
                        if response.status == 200:
                            student_schedule = await response.json()
                            calendar.update({"student_schedule": student_schedule})
                
                return calendar
                
        except Exception as e:
            logger.error(f"Schedule API error: {e}")
            return self._get_mock_schedule_info(student_id)
    
    async def get_admission_info(self) -> Dict[str, Any]:
        """Get current admission information and deadlines"""
        if self.mock_mode:
            return self._get_mock_admission_info()
            
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                url = f"{self.base_url}/admissions/current-cycle"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return self._get_mock_admission_info()
                        
        except Exception as e:
            logger.error(f"Admission API error: {e}")
            return self._get_mock_admission_info()
    
    async def get_library_info(self, student_id: Optional[str] = None) -> Dict[str, Any]:
        """Get library information and student-specific data"""
        if self.mock_mode:
            return self._get_mock_library_info(student_id)
            
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                # Get general library info
                lib_url = f"{self.base_url}/library/info"
                async with session.get(lib_url, headers=headers) as response:
                    if response.status == 200:
                        library_info = await response.json()
                    else:
                        library_info = self._get_mock_library_info()
                
                # Get student-specific library data
                if student_id:
                    student_lib_url = f"{self.base_url}/library/student/{student_id}"
                    async with session.get(student_lib_url, headers=headers) as response:
                        if response.status == 200:
                            student_library = await response.json()
                            library_info.update({"student_data": student_library})
                
                return library_info
                
        except Exception as e:
            logger.error(f"Library API error: {e}")
            return self._get_mock_library_info(student_id)
    
    async def get_grades(self, student_id: str) -> Dict[str, Any]:
        """Get student grades and academic performance"""
        if self.mock_mode:
            return self._get_mock_grades(student_id)
            
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                url = f"{self.base_url}/students/{student_id}/grades"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": "Grades not available", "status": response.status}
                        
        except Exception as e:
            logger.error(f"Grades API error: {e}")
            return {"error": f"Unable to fetch grades: {str(e)}"}
    
    # Mock data methods for development/testing
    def _get_mock_student_info(self, student_id: str) -> Dict[str, Any]:
        return {
            "student_id": student_id,
            "name": "John Doe",
            "email": f"{student_id}@university.edu",
            "program": "Computer Science",
            "year": "3rd Year",
            "semester": "Fall 2024",
            "status": "Active",
            "advisor": "Dr. Smith",
            "contact": "+1-234-567-8900"
        }
    
    def _get_mock_fee_info(self, student_id: Optional[str] = None) -> Dict[str, Any]:
        base_info = {
            "academic_year": "2024-25",
            "semester_fee": 75000,
            "hostel_fee": 25000,
            "mess_fee": 15000,
            "library_fee": 2000,
            "lab_fee": 5000,
            "total_semester_fee": 122000,
            "payment_deadlines": {
                "semester_1": "2024-07-31",
                "semester_2": "2024-12-31"
            },
            "late_fee": 5000,
            "payment_methods": ["Online Banking", "UPI", "Credit/Debit Card", "Bank Transfer"],
            "fee_structure_url": "https://university.edu/fees"
        }
        
        if student_id:
            base_info.update({
                "student_specific": {
                    "outstanding_amount": 25000,
                    "last_payment": "2024-06-15",
                    "payment_history": [
                        {"date": "2024-06-15", "amount": 97000, "status": "Paid"},
                        {"date": "2024-01-10", "amount": 122000, "status": "Paid"}
                    ],
                    "scholarship_applied": 15000,
                    "next_due_date": "2024-12-31"
                }
            })
        
        return base_info
    
    def _get_mock_schedule_info(self, student_id: Optional[str] = None) -> Dict[str, Any]:
        base_info = {
            "academic_year": "2024-25",
            "current_semester": "Fall 2024",
            "semester_start": "2024-08-01",
            "semester_end": "2024-12-15",
            "exam_period": {
                "mid_term": "2024-10-01 to 2024-10-15",
                "final_term": "2024-12-01 to 2024-12-15"
            },
            "holidays": [
                {"name": "Independence Day", "date": "2024-08-15"},
                {"name": "Gandhi Jayanti", "date": "2024-10-02"},
                {"name": "Diwali Break", "dates": "2024-11-01 to 2024-11-05"}
            ],
            "important_dates": {
                "registration_deadline": "2024-07-25",
                "course_add_drop": "2024-08-15",
                "fee_payment_deadline": "2024-07-31"
            }
        }
        
        if student_id:
            base_info.update({
                "student_schedule": {
                    "courses": [
                        {"code": "CS301", "name": "Data Structures", "credits": 4, "schedule": "Mon/Wed/Fri 9:00-10:00"},
                        {"code": "CS302", "name": "Database Systems", "credits": 3, "schedule": "Tue/Thu 10:00-11:30"},
                        {"code": "CS303", "name": "Software Engineering", "credits": 3, "schedule": "Mon/Wed 2:00-3:30"}
                    ],
                    "total_credits": 10,
                    "next_class": "CS301 - Tomorrow 9:00 AM",
                    "upcoming_assignments": [
                        {"course": "CS302", "title": "Database Design Project", "due": "2024-09-25"},
                        {"course": "CS303", "title": "Requirements Analysis", "due": "2024-09-30"}
                    ]
                }
            })
        
        return base_info
    
    def _get_mock_admission_info(self) -> Dict[str, Any]:
        return {
            "admission_cycle": "2025-26",
            "application_period": {
                "start": "2024-11-01",
                "end": "2024-12-31"
            },
            "entrance_exams": [
                {"name": "JEE Main", "date": "2025-01-24 to 2025-02-01"},
                {"name": "University Entrance", "date": "2025-02-15"}
            ],
            "programs_offered": [
                {"name": "B.Tech Computer Science", "seats": 120, "eligibility": "12th with Math, Physics, Chemistry"},
                {"name": "B.Tech Electronics", "seats": 80, "eligibility": "12th with Math, Physics, Chemistry"},
                {"name": "MBA", "seats": 60, "eligibility": "Bachelor's degree with 50% marks"}
            ],
            "application_fee": 1500,
            "counseling_dates": "2025-03-01 to 2025-03-15",
            "contact": {
                "phone": "+91-11-2345-6789",
                "email": "admissions@university.edu",
                "office": "Admission Office, Ground Floor, Admin Block"
            }
        }
    
    def _get_mock_library_info(self, student_id: Optional[str] = None) -> Dict[str, Any]:
        base_info = {
            "name": "Central Library",
            "hours": {
                "weekdays": "8:00 AM - 10:00 PM",
                "weekends": "9:00 AM - 6:00 PM",
                "holidays": "Closed"
            },
            "floors": 4,
            "total_books": 150000,
            "digital_resources": 25000,
            "study_seats": 500,
            "computer_terminals": 50,
            "services": [
                "Book Issue/Return",
                "Digital Library Access",
                "Inter-library Loan",
                "Research Assistance",
                "Printing/Scanning"
            ],
            "contact": {
                "phone": "+91-11-2345-6790",
                "email": "library@university.edu"
            }
        }
        
        if student_id:
            base_info.update({
                "student_data": {
                    "books_issued": 3,
                    "books_limit": 5,
                    "current_books": [
                        {"title": "Introduction to Algorithms", "due_date": "2024-09-30"},
                        {"title": "Database System Concepts", "due_date": "2024-10-05"},
                        {"title": "Software Engineering", "due_date": "2024-10-10"}
                    ],
                    "overdue_books": 0,
                    "fine_amount": 0,
                    "reservation_queue": []
                }
            })
        
        return base_info
    
    def _get_mock_grades(self, student_id: str) -> Dict[str, Any]:
        return {
            "student_id": student_id,
            "semester": "Spring 2024",
            "gpa": 8.5,
            "cgpa": 8.2,
            "courses": [
                {"code": "CS201", "name": "Data Structures", "credits": 4, "grade": "A", "points": 9},
                {"code": "CS202", "name": "Computer Networks", "credits": 3, "grade": "A-", "points": 8},
                {"code": "CS203", "name": "Operating Systems", "credits": 3, "grade": "B+", "points": 7}
            ],
            "total_credits": 10,
            "status": "Promoted to next semester",
            "remarks": "Good academic performance"
        }
