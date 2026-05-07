from rest_framework import permissions
from django.shortcuts import get_object_or_404
from applications.academic_information.models import ExtraInfo
from applications.globals.models import User


class IsFacultyStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow faculty and staff to edit it.
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        #only faculty and staff are able to make post request 
        return not request.user.holds_designations.filter(designation__name='student').exists()


class IsStudentOrFaculty(permissions.BasePermission):
    """
    Permission class to restrict feedback submission to students and faculty only.
    Enforces BR-DEPT-008: Only student/faculty can submit feedback.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        is_student = request.user.holds_designations.filter(designation__name='student').exists() or ExtraInfo.objects.filter(user=request.user, user_type='student').exists()
        is_faculty = request.user.holds_designations.filter(designation__name__in=['faculty', 'professor']).exists() or ExtraInfo.objects.filter(user=request.user, user_type='faculty').exists()
        return is_student or is_faculty


class IsStudentOnly(permissions.BasePermission):
    """
    Restrict submission to students only.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.holds_designations.filter(designation__name='student').exists()


class IsFacultyOrStaff(permissions.BasePermission):
    """
    Permission class to restrict announcement creation to faculty and staff only.
    Enforces BR-DEPT-001: Only authorized roles can create announcements.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        # Students cannot create announcements
        return not request.user.holds_designations.filter(designation__name='student').exists()


class IsHODOrDeptAdmin(permissions.BasePermission):
    """
    Permission class to restrict stock management actions to HOD and Department Admin.
    Used for stock approval, issuance, and inventory management.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Check if user holds HOD or deptadmin designation in any form
        user_designations = request.user.holds_designations.values_list(
            'designation__name', flat=True
        )
        return any(
            'hod' in role.lower() or 'admin' in role.lower() 
            for role in user_designations
        )


class IsHODOrDeptAdminOrFaculty(permissions.BasePermission):
    """
    Allow HOD, Admin, and Faculty to view feedback.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_designations = request.user.holds_designations.values_list(
            'designation__name', flat=True
        )
        # Check designations
        is_authorized = any(
            'hod' in role.lower() or 'admin' in role.lower() or 'faculty' in role.lower()
            for role in user_designations
        )
        if is_authorized:
            return True
            
        # Also check ExtraInfo user_type
        return ExtraInfo.objects.filter(user=request.user, user_type='faculty').exists()


class IsHOD(permissions.BasePermission):
    """
    Permission class to restrict actions to HOD only.
    Enforces BR-DEPT-004: Only HOD can delete announcements.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_designations = request.user.holds_designations.values_list(
            'designation__name', flat=True
        )
        return any('hod' in role.lower() for role in user_designations)


class IsDeptAdmin(permissions.BasePermission):
    """
    Permission class to restrict actions to Department Admin only.
    Enforces DEPT-WF-103: Dept Admin allocates and issues stock.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_designations = request.user.holds_designations.values_list(
            'designation__name', flat=True
        )
        return any('admin' in role.lower() for role in user_designations)


class IsFacultyOnly(permissions.BasePermission):
    """
    Restrict to Faculty only.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_designations = request.user.holds_designations.values_list(
            'designation__name', flat=True
        )
        is_faculty = any('faculty' in role.lower() or 'professor' in role.lower() for role in user_designations)
        if is_faculty:
            return True
        return ExtraInfo.objects.filter(user=request.user, user_type='faculty').exists()
