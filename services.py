#services.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from bson import ObjectId
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging
import bcrypt

from models import (
    User, Profile, Transaction, Transactions, InventoryItem, Book, 
    Message, Bus, BusRoute, Course, Timetable, SystemLog, Settings, 
    Logout, ProfileSettings, UserRole, PyObjectId
)
# Add these imports at the top of services.py
from typing import Optional
import jwt
from datetime import datetime, timedelta

# Secret key for JWT token generation (in a real-world scenario, use a secure environment variable)
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# MongoDB Configuration
mongo_uri = os.environ.get("MONGODB_URI")
database_name = os.environ.get("DATABASE_NAME")
client = AsyncIOMotorClient(mongo_uri)
db = client[database_name]

# 1. Dashboard Services
async def get_dashboard_metrics():
    """
    Retrieve comprehensive dashboard metrics
    """
    try:
        # Student Enrollment Metrics
        total_students = await db.users.count_documents({"role": "student"})
        
        # Staff Metrics
        staff_distribution = {
            "admin": await db.users.count_documents({"role": "admin"}),
            "teacher": await db.users.count_documents({"role": "teacher"}),
            "support": await db.users.count_documents({"role": "support"})
        }
        
        # Course Metrics
        total_courses = await db.courses.count_documents({})
        
        # Financial Metrics
        total_revenue = await db.transactions.aggregate([
            {"$match": {"transaction_type": "income"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        
        # Notifications and Messages
        unread_notifications = await db.system_logs.count_documents({"severity": "unread"})
        unread_messages = await db.messages.count_documents({"status": "unread"})
        
        return {
            "total_students": total_students,
            "staff_distribution": staff_distribution,
            "total_courses": total_courses,
            "total_revenue": total_revenue[0]['total'] if total_revenue else 0,
            "unread_notifications": unread_notifications,
            "unread_messages": unread_messages
        }
    except Exception as e:
        logger.error(f"Error retrieving dashboard metrics: {e}")
        raise

# 2. Student Management Services
async def list_students(skip: int = 0, limit: int = 100, filters: dict = None):
    """
    List students with optional filtering and pagination
    """
    query = filters or {}
    query["role"] = "student"
    try:
        students = await db.users.find(query).skip(skip).limit(limit).to_list(limit)
        return [User(**student) for student in students]
    except Exception as e:
        logger.error(f"Error listing students: {e}")
        raise

async def add_student(student_data: Dict[str, Any]):
    """
    Add a new student to the system
    """
    try:
        # Ensure role is set to student
        student_data['role'] = UserRole.STUDENT
        
        # Hash password
        if 'password' in student_data:
            student_data['password'] = bcrypt.hashpw(student_data['password'].encode(), bcrypt.gensalt())
        
        # Insert user
        result = await db.users.insert_one(student_data)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error adding student: {e}")
        raise

async def update_student(student_id: str, update_data: Dict[str, Any]):
    """
    Update existing student information
    """
    try:
        result = await db.users.update_one(
            {"_id": ObjectId(student_id), "role": "student"},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating student: {e}")
        raise

async def delete_student(student_id: str, archive: bool = True):
    """
    Delete or archive a student record
    """
    try:
        if archive:
            result = await db.users.update_one(
                {"_id": ObjectId(student_id), "role": "student"},
                {"$set": {"is_active": False}}
            )
        else:
            result = await db.users.delete_one(
                {"_id": ObjectId(student_id), "role": "student"}
            )
        return result.modified_count > 0 if archive else result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error deleting student: {e}")
        raise

# 3. Payroll Management Services
async def list_current_payroll(skip: int = 0, limit: int = 100):
    """
    List upcoming payroll information
    """
    try:
        payroll_data = await db.transactions.find({
            "transaction_type": "salary"
        }).skip(skip).limit(limit).to_list(limit)
        return [Transaction(**pay) for pay in payroll_data]
    except Exception as e:
        logger.error(f"Error listing payroll: {e}")
        raise

async def process_payroll(period: datetime):
    """
    Process payroll for a specific period
    """
    try:
        # Fetch all active employees
        employees = await db.users.find({
            "is_active": True, 
            "role": {"$in": ["teacher", "admin", "support"]}
        }).to_list(None)
        
        payroll_transactions = []
        for employee in employees:
            # Simplified salary calculation (would need more complex logic in real-world)
            salary_transaction = Transaction(
                user_id=employee['_id'],
                amount=employee.get('salary', 0),
                transaction_type="salary",
                description=f"Salary for {period.strftime('%B %Y')}",
                date=period,
                category="payroll",
                payment_method="bank_transfer",
                status="processed"
            )
            payroll_transactions.append(salary_transaction)
        
        # Bulk insert payroll transactions
        if payroll_transactions:
            await db.transactions.insert_many([t.dict() for t in payroll_transactions])
        
        return len(payroll_transactions)
    except Exception as e:
        logger.error(f"Error processing payroll: {e}")
        raise

# 4. Employee Management Services
async def list_employees(role: Optional[str] = None, skip: int = 0, limit: int = 100):
    """
    List employees with optional role filtering
    """
    try:
        query = {"role": role} if role else {}
        employees = await db.users.find(query).skip(skip).limit(limit).to_list(limit)
        return [User(**emp) for emp in employees]
    except Exception as e:
        logger.error(f"Error listing employees: {e}")
        raise

async def add_employee(employee_data: Dict[str, Any]):
    """
    Add a new employee
    """
    try:
        # Ensure password is hashed
        if 'password' in employee_data:
            employee_data['password'] = bcrypt.hashpw(employee_data['password'].encode(), bcrypt.gensalt())
        
        result = await db.users.insert_one(employee_data)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error adding employee: {e}")
        raise

async def update_employee(employee_id: str, update_data: Dict[str, Any]):
    """
    Update employee information
    """
    try:
        result = await db.users.update_one(
            {"_id": ObjectId(employee_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating employee: {e}")
        raise

# 5. Transactions Management Services
async def create_transaction(transaction_data: Dict[str, Any]):
    """
    Create a new financial transaction
    """
    try:
        result = await db.transactions.insert_one(transaction_data)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise

async def get_financial_summary():
    """
    Retrieve comprehensive financial summary
    """
    try:
        # Aggregate total income and expenses
        financial_summary = await db.transactions.aggregate([
            {
                "$group": {
                    "_id": None,
                    "total_income": {"$sum": {"$cond": [{"$eq": ["$transaction_type", "income"]}, "$amount", 0]}},
                    "total_expenses": {"$sum": {"$cond": [{"$eq": ["$transaction_type", "expense"]}, "$amount", 0]}}
                }
            }
        ]).to_list(1)
        
        return financial_summary[0] if financial_summary else {"total_income": 0, "total_expenses": 0}
    except Exception as e:
        logger.error(f"Error retrieving financial summary: {e}")
        raise

# 6. Inventory Management Services
async def manage_inventory_item(action: str, item_data: Dict[str, Any]):
    """
    Manage inventory items (create, update, delete)
    """
    try:
        if action == "create":
            result = await db.inventory.insert_one(item_data)
            return str(result.inserted_id)
        elif action == "update":
            result = await db.inventory.update_one(
                {"_id": ObjectId(item_data['id'])},
                {"$set": item_data}
            )
            return result.modified_count > 0
        elif action == "delete":
            result = await db.inventory.delete_one({"_id": ObjectId(item_data['id'])})
            return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error managing inventory: {e}")
        raise

# 7. E-Library Management Services
async def manage_book(action: str, book_data: Dict[str, Any]):
    """
    Manage e-library books
    """
    try:
        if action == "create":
            result = await db.books.insert_one(book_data)
            return str(result.inserted_id)
        elif action == "update":
            result = await db.books.update_one(
                {"_id": ObjectId(book_data['id'])},
                {"$set": book_data}
            )
            return result.modified_count > 0
        elif action == "delete":
            result = await db.books.delete_one({"_id": ObjectId(book_data['id'])})
            return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error managing book: {e}")
        raise

# 8. Messaging Services
async def send_mass_message(message_data: Dict[str, Any]):
    """
    Send mass SMS or email messages
    """
    try:
        # Insert message record
        result = await db.messages.insert_one(message_data)
        
        # In a real system, you'd integrate with SMS/Email gateway here
        # This is a placeholder for actual message sending logic
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error sending mass message: {e}")
        raise

# 9. Transportation Management Services
async def manage_bus(action: str, bus_data: Dict[str, Any]):
    """
    Manage school buses
    """
    try:
        if action == "create":
            result = await db.buses.insert_one(bus_data)
            return str(result.inserted_id)
        elif action == "update":
            result = await db.buses.update_one(
                {"_id": ObjectId(bus_data['id'])},
                {"$set": bus_data}
            )
            return result.modified_count > 0
        elif action == "delete":
            result = await db.buses.delete_one({"_id": ObjectId(bus_data['id'])})
            return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error managing bus: {e}")
        raise

# 10. Academics Management Services
async def manage_course(action: str, course_data: Dict[str, Any]):
    """
    Manage academic courses
    """
    try:
        if action == "create":
            result = await db.courses.insert_one(course_data)
            return str(result.inserted_id)
        elif action == "update":
            result = await db.courses.update_one(
                {"_id": ObjectId(course_data['id'])},
                {"$set": course_data}
            )
            return result.modified_count > 0
        elif action == "delete":
            result = await db.courses.delete_one({"_id": ObjectId(course_data['id'])})
            return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error managing course: {e}")
        raise

# 11. System Logging Services
async def log_system_event(log_data: Dict[str, Any]):
    """
    Log system events
    """
    try:
        result = await db.system_logs.insert_one(log_data)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error logging system event: {e}")
        raise

# 12. System Settings Services
async def update_system_settings(settings_data: Dict[str, Any]):
    """
    Update system-wide settings
    """
    try:
        result = await db.settings.update_one(
            {},  # Assuming a single settings document
            {"$set": settings_data},
            upsert=True
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating system settings: {e}")
        raise

# 13. Logout Services
async def handle_user_logout(user_id: str):
    """
    Handle user logout
    """
    try:
        logout_record = {
            "user_id": ObjectId(user_id),
            "logout_time": datetime.utcnow()
        }
        result = await db.logout_logs.insert_one(logout_record)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error handling user logout: {e}")
        raise

# 14. Profile Management Services
async def update_user_profile(user_id: str, profile_data: Dict[str, Any]):
    """
    Update user profile settings
    """
    try:
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": profile_data}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise


async def create_user(user_data: Dict[str, Any]):
    """
    Create a new user with role-based registration
    Required fields: username, password, email, role
    """
    try:
        # Validate required fields
        required_fields = ['username', 'password', 'email', 'role']
        for field in required_fields:
            if field not in user_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate role
        if user_data['role'] not in [r.value for r in UserRole]:
            raise ValueError(f"Invalid user role. Must be one of: {[r.value for r in UserRole]}")
        
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", user_data['email']):
            raise ValueError("Invalid email format")
        
        # Check if username or email already exists
        existing_user = await db.users.find_one({
            '$or': [
                {'username': user_data['username']},
                {'email': user_data['email']}
            ]
        })
        if existing_user:
            raise ValueError("Username or email already exists")
        
        # Hash password
        hashed_password = bcrypt.hashpw(user_data['password'].encode(), bcrypt.gensalt())
        
        # Create user document
        user_doc = {
            'username': user_data['username'],
            'email': user_data['email'],
            'password': hashed_password,
            'role': user_data['role'],
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Insert user
        result = await db.users.insert_one(user_doc)
        return str(result.inserted_id)
        
    except ValueError as ve:
        logger.error(f"Validation error creating user: {ve}")
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise

    
async def generate_access_token(user_id: str, role: str):
    """
    Generate JWT access token
    """
    try:
        # Token expiration
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Payload with user details
        to_encode = {
            "sub": str(user_id),
            "role": role,
            "exp": expire
        }
        
        # Encode token
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        raise

async def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT access token
    """
    try:
        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        return None
    except jwt.InvalidTokenError:
        logger.error("Invalid token")
        return None

async def get_user_by_id(user_id: str):
    """
    Retrieve user by ID
    """
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        return User(**user) if user else None
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        raise

async def list_users_by_role(role: UserRole, skip: int = 0, limit: int = 100):
    """
    List users by specific role
    """
    try:
        users = await db.users.find({"role": role.value}).skip(skip).limit(limit).to_list(limit)
        return [User(**user) for user in users]
    except Exception as e:
        logger.error(f"Error listing users by role: {e}")
        raise

# Update the existing authenticate_user function
async def authenticate_user(username: str, password: str):
    """
    Enhanced user authentication with token generation
    """
    try:
        user = await db.users.find_one({"username": username})
        if user and bcrypt.checkpw(password.encode(), user['password']):
            # Generate access token
            user_obj = User(**user)
            token = await generate_access_token(str(user_obj.id), user_obj.role)
            return {
                "user": user_obj,
                "access_token": token
            }
        return None
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        raise