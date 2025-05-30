from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import User, Client, Employee, StorageLocation, StorageUnitType, StorageUnit, Product, StorageRental

class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'role', 'is_active')
    search_fields = ('username', 'role')
    list_filter = ('role', 'is_active')
    readonly_fields = ('id',)

class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email', 'user_link')
    search_fields = ('full_name', 'email', 'user__username')
    readonly_fields = ('id',)
    def user_link(self, obj):
        if obj.user:
            link = reverse("admin:management_user_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return "-"
    user_link.short_description = 'User Account'

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'employee_id_number', 'user_link')
    search_fields = ('full_name', 'employee_id_number', 'user__username')
    readonly_fields = ('id',)
    def user_link(self, obj):
        if obj.user:
            link = reverse("admin:management_user_change", args=[obj.user.id]) # Assumes app_label is 'management'
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return "-"
    user_link.short_description = 'User Account'


class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address')
    search_fields = ('name',)
    readonly_fields = ('id',)

class StorageUnitTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'size', 'price_per_month')
    search_fields = ('name', 'size')
    list_filter = ('size',)
    readonly_fields = ('id',)

class StorageUnitAdmin(admin.ModelAdmin):
    list_display = ('id', 'unit_identifier', 'location', 'type', 'is_available')
    search_fields = ('unit_identifier', 'location__name', 'type__name')
    list_filter = ('is_available', 'location', 'type')
    readonly_fields = ('id',)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price')
    search_fields = ('name',)
    readonly_fields = ('id',)

class StorageRentalAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'storage_unit', 'employee', 'start_date', 'end_date', 'is_paid')
    search_fields = ('client__full_name', 'storage_unit__unit_identifier', 'employee__full_name')
    list_filter = ('is_paid', 'start_date', 'end_date', 'employee', 'storage_unit__location')
    readonly_fields = ('id', 'payment_date') # start_date could also be here if always auto-set
    date_hierarchy = 'start_date'


# Unregister models if already registered, then re-register with ModelAdmin
# This ensures that the new ModelAdmin classes are used.
# Using a loop to make it more concise and avoid errors if a model was not previously registered.
models_to_register = [
    (User, UserAdmin),
    (Client, ClientAdmin),
    (Employee, EmployeeAdmin),
    (StorageLocation, StorageLocationAdmin),
    (StorageUnitType, StorageUnitTypeAdmin),
    (StorageUnit, StorageUnitAdmin),
    (Product, ProductAdmin),
    (StorageRental, StorageRentalAdmin),
]

for model, model_admin in models_to_register:
    if admin.site.is_registered(model):
        admin.site.unregister(model)
    admin.site.register(model, model_admin)
