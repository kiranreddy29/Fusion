from datetime import timezone
from django.db import models
from datetime import date

# Create your models here.
from applications.globals.models import ExtraInfo , DepartmentInfo

  
class SpecialRequest(models.Model):
    request_maker = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    request_date = models.DateTimeField(default=date.today)
    brief = models.CharField(max_length=20, default='--')
    request_details = models.CharField(max_length=200)
    upload_request = models.FileField(blank=True)
    status = models.CharField(max_length=50,default='Pending')
    remarks = models.CharField(max_length=300, default="--")
    request_receiver = models.CharField(max_length=30, default="--")

    def __str__(self):
        return str(self.request_maker.user.username)


class Announcements(models.Model):
    maker_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    ann_date = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=200)
    batch = models.CharField(max_length=40,default="Year-1")
    department = models.CharField(max_length=40,default="ALL")
    programme = models.CharField(max_length=10)
    upload_announcement = models.FileField(upload_to='department/upload_announcement', null=True, default=None)
    is_hidden = models.BooleanField(default=False)
    
    def __str__(self):
        return str(self.maker_id.user.username)
    
class Information(models.Model):
    department = models.OneToOneField(
        DepartmentInfo,
        on_delete=models.CASCADE,
    )

    phone_number = models.BigIntegerField()
    email = models.CharField(max_length=200)
    facilites = models.TextField()
    labs = models.TextField()


class Lab(models.Model):
    department = models.CharField(max_length=50)  # Store department as a string field instead of a foreign key
    location = models.CharField(max_length=200)
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()

    def __str__(self):
        return f"{self.name} ({self.department})"

class Feedback(models.Model):
    department = models.CharField(max_length=50)  # no need to validate department name
    rating = models.CharField(max_length=20)
    remark = models.TextField()

    def __str__(self):
        return f"{self.department} - {self.rating}"
    
class Facility(models.Model):
    name = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)  # No foreign key, just a plain string
    location = models.CharField(max_length=200)
    amount = models.PositiveIntegerField(default=0)  # New amount field
    picture = models.ImageField(upload_to='department/facility_pictures/', blank=True, null=True)

    def __str__(self):
        return f"{self.branch} - {self.name}"


class StockItem(models.Model):
    """
    Represents an inventory item within a department.
    Supports DEPT-UC-004, UC-005, UC-006 (Stock Request/Approve/Issue workflow).
    """
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    department = models.CharField(max_length=50)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.department}) - Qty: {self.quantity}"

    class Meta:
        ordering = ['-last_updated']


class StockRequest(models.Model):
    """
    Represents a stock request made by faculty/staff.
    Part of workflow DEPT-WF-103: Stock Request → Approval → Issuance.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Issued', 'Issued'),
    ]

    requester = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='stock_requests')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='requests')
    quantity_requested = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    request_date = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, default='')
    approved_by = models.ForeignKey(
        ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='stock_approvals'
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    issued_by = models.ForeignKey(
        ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='stock_issuances'
    )
    issued_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Request by {self.requester} for {self.stock_item.name} - {self.status}"

    class Meta:
        ordering = ['-request_date']


class StockLog(models.Model):
    """
    Audit log for all stock-related actions.
    Maintains transparency and traceability for DEPT-WF-103.
    """
    ACTION_CHOICES = [
        ('Request', 'Request'),
        ('Approve', 'Approve'),
        ('Reject', 'Reject'),
        ('Issue', 'Issue'),
        ('Add', 'Add'),
        ('Update', 'Update'),
    ]

    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.action} - {self.stock_item.name} by {self.performed_by}"

    class Meta:
        ordering = ['-timestamp']