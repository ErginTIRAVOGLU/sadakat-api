from enum import Enum


class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    BUSINESS = "BUSINESS"
    ADMIN = "ADMIN"


class BusinessUserRole(str, Enum):
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    STAFF = "STAFF"