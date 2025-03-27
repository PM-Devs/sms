from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, HttpUrl, field_validator, ConfigDict
from datetime import date, datetime, time
from enum import Enum
from bson import ObjectId
from pydantic_core import core_schema


class PyObjectId:
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.no_info_plain_validator_function(cls.validate),
            core_schema.str_schema()
        ])

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            try:
                return ObjectId(v)
            except:
                raise ValueError("Invalid ObjectId")
        raise TypeError("ObjectId or string expected")

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, _handler):
        return {"type": "string"}


class BaseModelWithId(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id", validation_alias="id")
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_encoders={
            ObjectId: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            time: lambda v: v.isoformat(),
        }
    )


class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    SUPPORT_STAFF = "support"
    TEMPORARY_STAFF = "temporary"


class User(BaseModelWithId):
    username: Optional[str] = Field(
        None, 
        min_length=3, 
        max_length=50,
        description="Unique username for the user"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="User's email address"
    )
    password: Optional[str] = Field(
        None,
        min_length=8,
        description="Hashed password (optional for some operations)"
    )
    first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User's first name"
    )
    last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User's last name"
    )
    role: Optional[UserRole] = Field(
        None,
        description="User's role in the system"
    )
    is_active: Optional[bool] = Field(
        True,
        description="Whether the user account is active"
    )
    last_login: Optional[datetime] = Field(
        None,
        description="Timestamp of last login"
    )
    department: Optional[str] = Field(
        None,
        max_length=100,
        description="User's department or organizational unit"
    )
    contact_info: Optional[Dict[str, str]] = Field(
        None,
        description="Additional contact information"
    )

    @field_validator('id', mode='before')
    def validate_id(cls, v):
        if v is None:
            return None
        return PyObjectId.validate(v)


class Profile(BaseModelWithId):
    user_id: PyObjectId
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[0-9\s\-]+$')
    address: Optional[str] = Field(None, max_length=200)
    date_of_birth: Optional[date] = None
    profile_picture: Optional[HttpUrl] = None
    emergency_contacts: List[Dict[str, str]] = Field(
        default_factory=list,
        max_length=5,
        description="List of emergency contacts (name, relationship, phone)"
    )

    @field_validator('user_id', mode='before')
    def validate_user_id(cls, v):
        return PyObjectId.validate(v)


class Transaction(BaseModelWithId):
    user_id: PyObjectId
    amount: float = Field(ge=0)
    transaction_type: str = Field(min_length=2, max_length=50)
    description: str = Field(min_length=2, max_length=200)
    date: datetime = Field(default_factory=datetime.utcnow)
    category: str = Field(min_length=2, max_length=50)
    payment_method: str = Field(min_length=2, max_length=50)
    status: str = Field(default="completed", min_length=2, max_length=20)
    invoice_number: Optional[str] = Field(None, min_length=2, max_length=50)

    @field_validator('user_id', mode='before')
    def validate_user_id(cls, v):
        return PyObjectId.validate(v)


class Transactions(BaseModelWithId):
    total_income: float = Field(ge=0)
    total_expenses: float = Field(ge=0)
    current_balance: float
    income_sources: List[Dict[str, float]] = Field(default_factory=list)
    expense_channels: List[Dict[str, float]] = Field(default_factory=list)
    recent_transactions: List[Transaction] = Field(default_factory=list)


class InventoryItem(BaseModelWithId):
    name: str = Field(min_length=2, max_length=100)
    category: str = Field(min_length=2, max_length=50)
    quantity: int = Field(ge=0)
    unit_price: float = Field(ge=0)
    total_value: float = Field(ge=0)
    reorder_point: int = Field(ge=0)
    supplier: Optional[str] = Field(None, min_length=2, max_length=100)
    last_restocked: Optional[date] = None
    sales_trend: Optional[List[float]] = None


class Book(BaseModelWithId):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=2, max_length=100)
    isbn: str = Field(min_length=10, max_length=20)
    category: str = Field(min_length=2, max_length=50)
    available_copies: int = Field(ge=0)
    total_copies: int = Field(ge=0)
    download_link: Optional[HttpUrl] = None
    publisher: Optional[str] = Field(None, min_length=2, max_length=100)
    is_borrowed: bool = False


class Message(BaseModelWithId):
    sender_id: PyObjectId
    recipients: List[PyObjectId]
    subject: str = Field(min_length=1, max_length=100)
    body: str = Field(min_length=1)
    channel: str = Field(pattern="^(SMS|Email)$")
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="sent", pattern="^(sent|delivered|read|failed)$")
    template_used: Optional[str] = Field(None, min_length=2, max_length=50)
    delivery_rate: Optional[float] = Field(None, ge=0, le=100)
    open_rate: Optional[float] = Field(None, ge=0, le=100)

    @field_validator('sender_id', 'recipients', mode='before')
    def validate_ids(cls, v):
        if isinstance(v, list):
            return [PyObjectId.validate(item) for item in v]
        return PyObjectId.validate(v)


class Bus(BaseModelWithId):
    name: str = Field(min_length=2, max_length=50)
    number: str = Field(min_length=1, max_length=20)
    capacity: int = Field(gt=0)
    driver_id: PyObjectId
    current_route_id: PyObjectId
    status: str = Field(default="active", pattern="^(active|maintenance|retired)$")
    last_maintenance: date
    next_maintenance_due: date
    maintenance_history: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator('driver_id', 'current_route_id', mode='before')
    def validate_ids(cls, v):
        return PyObjectId.validate(v)


class BusRoute(BaseModelWithId):
    name: str = Field(min_length=2, max_length=100)
    stops: List[str] = Field(min_length=1)
    assigned_bus_id: PyObjectId
    schedule: Dict[str, List[time]]
    total_students_route: int = Field(default=0, ge=0)

    @field_validator('assigned_bus_id', mode='before')
    def validate_bus_id(cls, v):
        return PyObjectId.validate(v)


class Course(BaseModelWithId):
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=20)
    department: str = Field(min_length=2, max_length=50)
    teacher_id: PyObjectId
    students: List[PyObjectId] = Field(default_factory=list)
    schedule: Dict[str, Any] = Field(default_factory=dict)
    credits: int = Field(gt=0)
    semester: str = Field(min_length=2, max_length=20)
    grade_scale: Dict[str, Dict[str, float]] = Field(default_factory=dict)

    @field_validator('teacher_id', 'students', mode='before')
    def validate_ids(cls, v):
        if isinstance(v, list):
            return [PyObjectId.validate(item) for item in v]
        return PyObjectId.validate(v)


class Timetable(BaseModelWithId):
    grade: str = Field(min_length=1, max_length=20)
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    course_id: PyObjectId
    room: str = Field(min_length=1, max_length=20)
    teacher_id: Optional[PyObjectId] = None

    @field_validator('course_id', 'teacher_id', mode='before')
    def validate_ids(cls, v):
        if v is None:
            return None
        return PyObjectId.validate(v)


class SystemLog(BaseModelWithId):
    timestamp: datetime
    severity: str = Field(pattern="^(info|warning|error|critical)$")
    component: str = Field(min_length=2, max_length=50)
    message: str = Field(min_length=1)
    user_id: Optional[PyObjectId] = None

    @field_validator('user_id', mode='before')
    def validate_user_id(cls, v):
        if v is None:
            return None
        return PyObjectId.validate(v)


class Settings(BaseModelWithId):
    school_name: str = Field(min_length=2, max_length=100)
    academic_year_start: date
    academic_year_end: date
    default_password: str = Field(min_length=8)
    max_class_size: int = Field(gt=0)
    timezone: str = Field(default="UTC", min_length=2, max_length=50)
    enable_online_payments: bool = False
    maintenance_mode: bool = False
    notification_settings: Dict[str, bool] = Field(
        default={"sms": True, "email": True}
    )
    communication_channels: List[str] = Field(
        default=["SMS", "Email"],
        min_length=1
    )


class Logout(BaseModelWithId):
    user_id: PyObjectId
    logout_time: datetime = Field(default_factory=datetime.utcnow)
    session_duration: Optional[int] = Field(None, ge=0)

    @field_validator('user_id', mode='before')
    def validate_user_id(cls, v):
        return PyObjectId.validate(v)


class ProfileSettings(BaseModelWithId):
    user_id: PyObjectId
    language_preference: str = Field(default="English", min_length=2, max_length=50)
    notification_settings: Dict[str, bool] = Field(
        default={"email": True, "sms": False, "push_notification": False}
    )
    two_factor_authentication: bool = False
    theme: str = Field(default="default", min_length=2, max_length=20)

    @field_validator('user_id', mode='before')
    def validate_user_id(cls, v):
        return PyObjectId.validate(v)