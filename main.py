from fastapi import FastAPI, HTTPException, Depends, Query, Path, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

# Ensure PyJWT is imported
import jwt

# Import models and services
from models import (
    User, Profile, Transaction, Transactions, InventoryItem, Book, 
    Message, Bus, BusRoute, Course, Timetable, SystemLog, Settings, 
    Logout, ProfileSettings, UserRole, PyObjectId
)
import services

# Create FastAPI app
app = FastAPI(title="School Management System API")

# Authentication Dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 1. Dashboard Metrics Endpoint
@app.get("/dashboard/metrics")
async def get_dashboard_metrics():
    """
    Retrieve comprehensive dashboard metrics
    """
    try:
        metrics = await services.get_dashboard_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Student Management Endpoints
@app.get("/students", response_model=List[Dict[str, Any]])
async def list_students(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000),
    filters: Optional[Dict[str, Any]] = None
):
    """
    List students with optional filtering and pagination
    """
    try:
        students = await services.list_students(skip, limit, filters)
        return [student.dict() for student in students]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/students")
async def add_student(student_data: dict):
    """
    Add a new student to the system
    """
    try:
        student_id = await services.add_student(student_data)
        return {"student_id": student_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/students/{student_id}")
async def update_student(
    student_id: str = Path(..., description="Student ID"),
    update_data: dict = {}
):
    """
    Update existing student information
    """
    try:
        success = await services.update_student(student_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Student not found")
        return {"message": "Student updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/students/{student_id}")
async def delete_student(
    student_id: str = Path(..., description="Student ID"),
    archive: bool = Query(True, description="Archive instead of permanent delete")
):
    """
    Delete or archive a student record
    """
    try:
        success = await services.delete_student(student_id, archive)
        if not success:
            raise HTTPException(status_code=404, detail="Student not found")
        return {"message": "Student deleted/archived successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 3. Payroll Management Endpoints
@app.get("/payroll")
async def list_current_payroll(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000)
):
    """
    List upcoming payroll information
    """
    try:
        payroll_data = await services.list_current_payroll(skip, limit)
        return [pay.dict() for pay in payroll_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/payroll/process")
async def process_payroll(period: datetime = datetime.utcnow()):
    """
    Process payroll for a specific period
    """
    try:
        processed_count = await services.process_payroll(period)
        return {"message": f"Processed payroll for {processed_count} employees"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Employee Management Endpoints
@app.get("/employees")
async def list_employees(
    role: Optional[str] = Query(None),
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000)
):
    """
    List employees with optional role filtering
    """
    try:
        employees = await services.list_employees(role, skip, limit)
        return [emp.dict() for emp in employees]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/employees")
async def add_employee(employee_data: dict):
    """
    Add a new employee
    """
    try:
        employee_id = await services.add_employee(employee_data)
        return {"employee_id": employee_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/employees/{employee_id}")
async def update_employee(
    employee_id: str = Path(..., description="Employee ID"),
    update_data: dict = {}
):
    """
    Update employee information
    """
    try:
        success = await services.update_employee(employee_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Employee not found")
        return {"message": "Employee updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 5. Transactions Management Endpoints
@app.post("/transactions")
async def create_transaction(transaction_data: dict):
    """
    Create a new financial transaction
    """
    try:
        transaction_id = await services.create_transaction(transaction_data)
        return {"transaction_id": transaction_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/financial/summary")
async def get_financial_summary():
    """
    Retrieve comprehensive financial summary
    """
    try:
        summary = await services.get_financial_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6. Inventory Management Endpoint
@app.post("/inventory/{action}")
async def manage_inventory_item(
    action: str = Path(..., description="Action to perform"),
    item_data: dict = {}
):
    """
    Manage inventory items (create/update/delete)
    """
    try:
        result = await services.manage_inventory_item(action, item_data)
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 7. E-Library Management Endpoint
@app.post("/books/{action}")
async def manage_book(
    action: str = Path(..., description="Action to perform"),
    book_data: dict = {}
):
    """
    Manage e-library books (create/update/delete)
    """
    try:
        result = await services.manage_book(action, book_data)
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 8. Messaging Endpoint
@app.post("/messages/send")
async def send_mass_message(message_data: dict):
    """
    Send mass SMS or email messages
    """
    try:
        message_id = await services.send_mass_message(message_data)
        return {"message_id": message_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 9. Transportation Management Endpoint
@app.post("/buses/{action}")
async def manage_bus(
    action: str = Path(..., description="Action to perform"),
    bus_data: dict = {}
):
    """
    Manage school buses (create/update/delete)
    """
    try:
        result = await services.manage_bus(action, bus_data)
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 10. Academics Management Endpoint
@app.post("/courses/{action}")
async def manage_course(
    action: str = Path(..., description="Action to perform"),
    course_data: dict = {}
):
    """
    Manage academic courses (create/update/delete)
    """
    try:
        result = await services.manage_course(action, course_data)
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 11. System Logging Endpoint
@app.post("/system/log")
async def log_system_event(log_data: dict):
    """
    Log system events
    """
    try:
        log_id = await services.log_system_event(log_data)
        return {"log_id": log_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 12. System Settings Endpoint
@app.put("/system/settings")
async def update_system_settings(settings_data: dict):
    """
    Update system-wide settings
    """
    try:
        success = await services.update_system_settings(settings_data)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 13. Logout Endpoint
@app.post("/logout/{user_id}")
async def handle_user_logout(user_id: str):
    """
    Handle user logout
    """
    try:
        logout_id = await services.handle_user_logout(user_id)
        return {"logout_id": logout_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 14. Profile Management Endpoint
@app.put("/update/profile/{user_id}")
async def update_user_profile(
    user_id: str = Path(..., description="User ID"),
    profile_data: dict = {}
):
    """
    Update user profile settings
    """
    try:
        success = await services.update_user_profile(user_id, profile_data)
        if not success:
            raise HTTPException(status_code=404, detail="User profile not found")
        return {"message": "Profile updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Internal function to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get current authenticated user from token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = await services.verify_access_token(token)
        if payload is None:
            raise credentials_exception
        user_id: str = payload.get("sub")
        user_role: str = payload.get("role")
        if user_id is None:
            raise credentials_exception
        user = await services.get_user_by_id(user_id)
        if user is None:
            raise credentials_exception
        return user
    except Exception:
        raise credentials_exception

# User Registration Endpoint for Different Roles
@app.post("/register/{role}")
async def register_user(
    role: str, 
    user_data: dict
):
    """
    Register a new user with specific role
    """
    try:
        # Ensure role matches the path parameter
        user_data['role'] = role
        user_id = await services.create_user(user_data)
        return {"user_id": user_id, "message": f"{role.capitalize()} registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Enhanced Login Endpoint with Token Generation
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    User authentication endpoint with JWT token generation
    """
    try:
        auth_result = await services.authenticate_user(form_data.username, form_data.password)
        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return {
            "access_token": auth_result['access_token'], 
            "token_type": "bearer",
            "user_role": auth_result['user'].role
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# List Users by Role
@app.get("/users/{role}")
async def list_users_by_role(
    role: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """
    List users by role with authentication
    """
    try:
        # Optional: Add role-based access control
        if current_user.role not in ["ADMIN", "SUPPORT_STAFF"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        users = await services.list_users_by_role(role, skip, limit)
        return [user.dict() for user in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get Current User Profile
@app.get("/me")
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's profile
    """
    return current_user.dict()

@app.get("/")
async def home():
    return "Hello world"
