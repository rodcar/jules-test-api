from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from ..extensions import db # Changed from .. import db

class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'client', 'employee', 'admin'
    is_active = Column(Boolean, default=True)

    client = relationship("Client", uselist=False, back_populates="user")
    employee = relationship("Employee", uselist=False, back_populates="user")

class Client(db.Model):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String)
    address = Column(Text)
    
    user = relationship("User", back_populates="client")
    rentals = relationship("StorageRental", back_populates="client")

class Employee(db.Model):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    full_name = Column(String, nullable=False)
    employee_id_number = Column(String, unique=True, nullable=False)
    
    user = relationship("User", back_populates="employee")
    rentals_registered = relationship("StorageRental", back_populates="employee")

class StorageLocation(db.Model):
    __tablename__ = 'storage_locations'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    address = Column(Text, nullable=False)
    
    storage_units = relationship("StorageUnit", back_populates="location")

class StorageUnitType(db.Model):
    __tablename__ = 'storage_unit_types'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    size = Column(String)
    price_per_month = Column(Numeric, nullable=False)
    
    storage_units = relationship("StorageUnit", back_populates="type")

class StorageUnit(db.Model):
    __tablename__ = 'storage_units'
    id = Column(Integer, primary_key=True)
    unit_identifier = Column(String, nullable=False, unique=True)
    location_id = Column(Integer, ForeignKey('storage_locations.id'), nullable=False)
    type_id = Column(Integer, ForeignKey('storage_unit_types.id'), nullable=False)
    is_available = Column(Boolean, default=True)
    
    location = relationship("StorageLocation", back_populates="storage_units")
    type = relationship("StorageUnitType", back_populates="storage_units")
    rentals = relationship("StorageRental", back_populates="storage_unit")

class Product(db.Model):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    price = Column(Numeric, nullable=False)

class StorageRental(db.Model):
    __tablename__ = 'storage_rentals'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    storage_unit_id = Column(Integer, ForeignKey('storage_units.id'), nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    start_date = Column(DateTime, nullable=False, default=func.now())
    end_date = Column(DateTime, nullable=False)
    price_at_rental = Column(Numeric, nullable=False)
    is_paid = Column(Boolean, default=False)
    payment_date = Column(DateTime, nullable=True)
    
    client = relationship("Client", back_populates="rentals")
    storage_unit = relationship("StorageUnit", back_populates="rentals")
    employee = relationship("Employee", back_populates="rentals_registered")
