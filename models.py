from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, HttpUrl, constr, conint, confloat
from datetime import date, datetime, time
from enum import Enum
from bson import ObjectId
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any, handler=None) -> ObjectId:
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )


class BaseModelWithId(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    SUPPORT_STAFF = "support"
    TEMPORARY_STAFF = "temporary"


class User(BaseModelWithId):
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool = True
    last_login: Optional[datetime] = None
    department: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None


class Profile(BaseModelWithId):
    user_id: PyObjectId
    phone_number: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    profile_picture: Optional[HttpUrl] = None
    emergency_contacts: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of emergency contact details with name, relationship, and contact number"
    )


class Transaction(BaseModelWithId):
    user_id: PyObjectId
    amount: confloat(ge=0)
    transaction_type: str
    description: str
    date: datetime = Field(default_factory=datetime.utcnow)
    category: str
    payment_method: str
    status: str = "completed"
    invoice_number: Optional[str] = None


class Transactions(BaseModelWithId):
    total_income: float
    total_expenses: float
    current_balance: float
    income_sources: List[Dict[str, float]] = []
    expense_channels: List[Dict[str, float]] = []
    recent_transactions: List[Transaction] = []


class InventoryItem(BaseModelWithId):
    name: str
    category: str
    quantity: conint(ge=0)
    unit_price: confloat(ge=0)
    total_value: float
    reorder_point: int
    supplier: Optional[str] = None
    last_restocked: Optional[date] = None
    sales_trend: Optional[List[float]] = None


class Book(BaseModelWithId):
    title: str
    author: str
    isbn: str
    category: str
    available_copies: int
    total_copies: int
    download_link: Optional[HttpUrl] = None
    publisher: Optional[str] = None
    is_borrowed: bool = False


class Message(BaseModelWithId):
    sender_id: PyObjectId
    recipients: List[PyObjectId]
    subject: str
    body: str
    channel: str
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "sent"
    template_used: Optional[str] = None
    delivery_rate: Optional[float] = None
    open_rate: Optional[float] = None


class Bus(BaseModelWithId):
    name: str
    number: str
    capacity: int
    driver_id: PyObjectId
    current_route_id: PyObjectId
    status: str = "active"
    last_maintenance: date
    next_maintenance_due: date
    maintenance_history: List[Dict[str, Any]] = []


class BusRoute(BaseModelWithId):
    name: str
    stops: List[str]
    assigned_bus_id: PyObjectId
    schedule: Dict[str, List[time]]
    total_students_route: int = 0


class Course(BaseModelWithId):
    name: str
    code: str
    department: str
    teacher_id: PyObjectId
    students: List[PyObjectId] = []
    schedule: Dict[str, Any] = {}
    credits: int
    semester: str
    grade_scale: Dict[str, Dict[str, float]] = {}


class Timetable(BaseModelWithId):
    grade: str
    day_of_week: int
    start_time: time
    end_time: time
    course_id: PyObjectId
    room: str
    teacher_id: Optional[PyObjectId] = None


class SystemLog(BaseModelWithId):
    timestamp: datetime
    severity: str
    component: str
    message: str
    user_id: Optional[PyObjectId] = None


class Settings(BaseModelWithId):
    school_name: str
    academic_year_start: date
    academic_year_end: date
    default_password: str
    max_class_size: int
    timezone: str = "UTC"
    enable_online_payments: bool = False
    maintenance_mode: bool = False
    notification_settings: Dict[str, bool] = {
        "sms": True,
        "email": True
    }
    communication_channels: List[str] = ["SMS", "Email"]


class Logout(BaseModelWithId):
    user_id: PyObjectId
    logout_time: datetime = Field(default_factory=datetime.utcnow)
    session_duration: Optional[int] = None


class ProfileSettings(BaseModelWithId):
    user_id: PyObjectId
    language_preference: str = "English"
    notification_settings: Dict[str, bool] = {
        "email": True,
        "sms": False,
        "push_notification": False
    }
    two_factor_authentication: bool = False
    theme: str = "default"