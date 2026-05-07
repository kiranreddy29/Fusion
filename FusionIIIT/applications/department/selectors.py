from django.shortcuts import get_object_or_404
from django.db import models
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, DepartmentInfo
from applications.academic_information.models import Student, Curriculum, Curriculum_Instructor
from .models import Information, Announcements, SpecialRequest, StockItem, StockRequest, StockLog, Feedback, Lab, Facility

def get_department_information_selector():
    return {
        "cse_info": Information.objects.filter(department_id=51).first(),
        "ece_info": Information.objects.filter(department_id=30).first(),
        "me_info": Information.objects.filter(department_id=37).first(),
        "sm_info": Information.objects.filter(department_id=28).first(),
    }

def get_student_courses_selector(user):
    student = Student.objects.filter(id__user=user).first()
    if not student:
        return []
    
    courses = Curriculum.objects.filter(
        programme=student.programme,
        batch=student.batch,
        sem=student.curr_semester_no
    ).select_related('course_id')
    
    return courses

def get_announcements_selector(department=None, programme=None, batch=None):
    queryset = Announcements.objects.all()
    
    if department and department.upper() != "ALL":
        queryset = queryset.filter(models.Q(department=department) | models.Q(department__iexact="ALL"))
    
    if programme and programme.upper() != "ALL":
        queryset = queryset.filter(models.Q(programme=programme) | models.Q(programme__iexact="ALL"))
        
    if batch and batch.upper() != "ALL":
        queryset = queryset.filter(models.Q(batch=batch) | models.Q(batch__iexact="ALL"))
        
    return queryset.order_by('-ann_date')

def get_faculty_by_dept_selector():
    return {
        "cse_f": ExtraInfo.objects.filter(department__name='CSE', user_type='faculty'),
        "ece_f": ExtraInfo.objects.filter(department__name='ECE', user_type='faculty'),
        "me_f": ExtraInfo.objects.filter(department__name='ME', user_type='faculty'),
        "sm_f": ExtraInfo.objects.filter(department__name='SM', user_type='faculty'),
        "staff": ExtraInfo.objects.filter(user_type='staff'),
    }

def get_make_request_by_maker_selector(user_info):
    return SpecialRequest.objects.filter(request_maker=user_info)

def get_to_request_by_receiver_selector(username):
    return SpecialRequest.objects.filter(request_receiver=username)

def get_stock_items_selector(department=None):
    if department:
        return StockItem.objects.filter(department=department)
    return StockItem.objects.all()

def get_stock_requests_selector(department=None, status=None):
    queryset = StockRequest.objects.all().select_related(
        'requester__user', 'stock_item', 'approved_by__user', 'issued_by__user'
    )
    if department:
        queryset = queryset.filter(stock_item__department=department)
    if status:
        queryset = queryset.filter(status=status)
    return queryset

def get_stock_logs_selector(department=None):
    if department:
        return StockLog.objects.filter(stock_item__department=department).order_by('-timestamp')
    return StockLog.objects.all().order_by('-timestamp')

def get_feedback_selector():
    return Feedback.objects.all()

def get_labs_selector():
    return Lab.objects.all()

def get_facilities_selector():
    return Facility.objects.all()
