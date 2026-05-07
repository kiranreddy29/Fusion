from datetime import date, datetime
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, DepartmentInfo
from .models import Announcements, StockItem, StockRequest, StockLog, SpecialRequest, Feedback
from notification.views import department_notif

def create_announcement_service(maker_user, message, batch='ALL', programme='ALL', department='ALL', upload_announcement=None):
    from django.db.models import Q
    user_info = ExtraInfo.objects.get(user=maker_user)
    
    # Standardize wildcards to uppercase
    batch = batch.upper() if batch.lower() == 'all' else batch
    programme = programme.upper() if programme.lower() == 'all' else programme
    department = department.upper() if department.lower() == 'all' else department

    announcement = Announcements.objects.create(
        maker_id=user_info,
        batch=batch,
        programme=programme,
        message=message,
        upload_announcement=upload_announcement,
        department=department,
        ann_date=date.today()
    )
    
    # Send notifications
    try:
        # Build query for recipients
        recipient_filters = Q()
        
        # 1. Department Filter
        if department != 'ALL':
            recipient_filters &= Q(extrainfo__department__name=department)
            
        # 2. Programme Filter
        if programme != 'ALL':
            recipient_filters &= (Q(extrainfo__student__programme=programme) | ~Q(extrainfo__user_type='student'))
            
        # 3. Batch Filter
        if batch != 'ALL' and 'YEAR-' in batch.upper():
            try:
                year_num = int(batch.split('-')[1])
                current_year = datetime.now().year
                current_month = datetime.now().month
                yearset = current_year if current_month > 8 else current_year - 1
                absolute_batch = int(yearset) - year_num + 1
                recipient_filters &= (Q(extrainfo__student__batch=absolute_batch) | ~Q(extrainfo__user_type='student'))
            except:
                pass

        recipients = User.objects.filter(recipient_filters).distinct()
        
        if recipients.exists():
            department_notif(
                maker_user, recipients, message,
                department=department,
                programme=programme,
                batch=batch
            )
    except Exception as e:
        print(f"Notification error: {e}")
        
    return announcement

def create_stock_request_service(requester_user, stock_item_id, quantity_requested, remarks=''):
    user_info = ExtraInfo.objects.get(user=requester_user)
    stock_item = StockItem.objects.get(id=stock_item_id)
    
    request = StockRequest.objects.create(
        requester=user_info,
        stock_item=stock_item,
        quantity_requested=quantity_requested,
        remarks=remarks,
        status='Pending'
    )
    
    # Audit log
    StockLog.objects.create(
        stock_item=stock_item,
        action='Request',
        performed_by=user_info,
        quantity=quantity_requested,
        remarks=f"Stock request submitted by {requester_user.username}"
    )
    
    # Notify HOD
    try:
        hod_users = User.objects.filter(holds_designations__designation__name__startswith='HOD').distinct()
        department_notif(requester_user, hod_users, f"New stock request for {stock_item.name}")
    except Exception as e:
        print(f"Notification error: {e}")
        
    return request

def approve_stock_request_service(approver_user, request_id, action, remarks=''):
    user_info = ExtraInfo.objects.get(user=approver_user)
    stock_request = StockRequest.objects.get(id=request_id)
    
    if action == 'approve':
        stock_request.status = 'Approved'
        log_action = 'Approve'
    else:
        stock_request.status = 'Rejected'
        log_action = 'Reject'
        
    stock_request.approved_by = user_info
    stock_request.approval_date = datetime.now()
    stock_request.remarks = remarks
    stock_request.save()
    
    # Audit log
    StockLog.objects.create(
        stock_item=stock_request.stock_item,
        action=log_action,
        performed_by=user_info,
        quantity=stock_request.quantity_requested,
        remarks=f"Request {action}d by {approver_user.username}. {remarks}"
    )
    
    return stock_request

def issue_stock_service(issuer_user, request_id, remarks=''):
    user_info = ExtraInfo.objects.get(user=issuer_user)
    stock_request = StockRequest.objects.get(id=request_id)
    
    stock_item = stock_request.stock_item
    if stock_item.quantity < stock_request.quantity_requested:
        raise ValueError("Insufficient stock")
        
    stock_item.quantity -= stock_request.quantity_requested
    stock_item.save()
    
    stock_request.status = 'Issued'
    stock_request.issued_by = user_info
    stock_request.issued_date = datetime.now()
    stock_request.save()
    
    # Audit log
    StockLog.objects.create(
        stock_item=stock_item,
        action='Issue',
        performed_by=user_info,
        quantity=stock_request.quantity_requested,
        remarks=f"Stock issued by {issuer_user.username}. {remarks}"
    )
    
    return stock_request

def create_feedback_service(user, department, rating, remark):
    import json
    json_remark = json.dumps({
        'text': remark,
        'status': 'New',
        'admin_remarks': '',
        'submitter': user.username
    })
    feedback = Feedback.objects.create(
        department=department,
        rating=rating,
        remark=json_remark
    )
    return feedback
