from django.db import models

class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(unique=True, max_length=255) # Assuming max_length, adjust if known
    password_hash = models.CharField(max_length=255) # Assuming max_length
    role = models.CharField(max_length=50)  # 'client', 'employee', 'admin'
    is_active = models.BooleanField(default=True)

    # Relationships will be defined by related models using ForeignKey or OneToOneField
    # client = models.OneToOneField('Client', on_delete=models.CASCADE, related_name='user_reverse') # Defined by Client.user
    # employee = models.OneToOneField('Employee', on_delete=models.CASCADE, related_name='user_reverse') # Defined by Employee.user


    class Meta:
        managed = False
        db_table = 'users'

    def __str__(self):
        return self.username

class Client(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile') # user_id in SQLAlchemy
    full_name = models.CharField(max_length=255)
    email = models.CharField(unique=True, max_length=255)
    phone_number = models.CharField(max_length=50, blank=True, null=True) # Allow null
    address = models.TextField(blank=True, null=True) # Allow null

    # rentals = relationship("StorageRental", back_populates="client") # Defined by StorageRental.client

    class Meta:
        managed = False
        db_table = 'clients'

    def __str__(self):
        return self.full_name

class Employee(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile') # user_id in SQLAlchemy
    full_name = models.CharField(max_length=255)
    employee_id_number = models.CharField(unique=True, max_length=255)

    # rentals_registered = relationship("StorageRental", back_populates="employee") # Defined by StorageRental.employee

    class Meta:
        managed = False
        db_table = 'employees'

    def __str__(self):
        return self.full_name

class StorageLocation(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=255)
    address = models.TextField()

    # storage_units = relationship("StorageUnit", back_populates="location") # Defined by StorageUnit.location

    class Meta:
        managed = False
        db_table = 'storage_locations'

    def __str__(self):
        return self.name

class StorageUnitType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=255)
    description = models.TextField(blank=True, null=True)
    size = models.CharField(max_length=100, blank=True, null=True) # Assuming max_length
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2)

    # storage_units = relationship("StorageUnit", back_populates="type") # Defined by StorageUnit.type

    class Meta:
        managed = False
        db_table = 'storage_unit_types'

    def __str__(self):
        return self.name

class StorageUnit(models.Model):
    id = models.AutoField(primary_key=True)
    unit_identifier = models.CharField(unique=True, max_length=255)
    location = models.ForeignKey(StorageLocation, on_delete=models.CASCADE, related_name='storage_units') # location_id
    type = models.ForeignKey(StorageUnitType, on_delete=models.CASCADE, related_name='storage_units') # type_id
    is_available = models.BooleanField(default=True)

    # rentals = relationship("StorageRental", back_populates="storage_unit") # Defined by StorageRental.storage_unit

    class Meta:
        managed = False
        db_table = 'storage_units'

    def __str__(self):
        return self.unit_identifier

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'products'

    def __str__(self):
        return self.name

class StorageRental(models.Model):
    id = models.AutoField(primary_key=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='rentals') # client_id
    storage_unit = models.ForeignKey(StorageUnit, on_delete=models.CASCADE, related_name='rentals') # storage_unit_id
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='rentals_registered') # employee_id
    start_date = models.DateTimeField() # default=func.now() handled by SQLAlchemy
    end_date = models.DateTimeField()
    price_at_rental = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'storage_rentals'

    def __str__(self):
        return f"Rental {self.id} for {self.client} - Unit {self.storage_unit}"
