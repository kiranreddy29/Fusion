from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from applications.department.models import Announcements
from applications.department.models import Facility
from applications.department.models import StockItem, StockRequest, StockLog
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation,Faculty)
from applications.eis.models import (faculty_about, emp_research_projects)
from .serializers import (AnnouncementSerializer,ExtraInfoSerializer,SpiSerializer,StudentSerializer,DesignationSerializer
                          ,HoldsDesignationSerializer,FacultySerializer,faculty_aboutSerializer,emp_research_projectsSerializer, FacilitiesSerializer,
                          StockItemSerializer, StockRequestSerializer, StockLogSerializer)
from .permissions import (IsFacultyStaffOrReadOnly, IsStudentOrFaculty,
                          IsFacultyOrStaff, IsHODOrDeptAdmin, IsHOD, IsStudentOnly, IsHODOrDeptAdminOrFaculty, IsDeptAdmin)
from ..selectors import (
    get_announcements_selector,
    get_stock_items_selector,
    get_stock_requests_selector,
    get_stock_logs_selector,
    get_student_courses_selector
)
from ..services import (
    create_announcement_service,
    create_stock_request_service,
    approve_stock_request_service,
    issue_stock_service
)
from django.http import JsonResponse 
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from datetime import date
from notification.views import department_notif
from collections import defaultdict
import re

from applications.department.models import Information
from .serializers import InformationSerializer
from .serializers import LabSerializer
from applications.globals.models import DepartmentInfo
from applications.department.models import Lab
from .serializers import FeedbackSerializer
from applications.department.models import Feedback
from datetime import datetime

current_year = datetime.now().year
current_month = datetime.now().month
yearset = current_year if current_month > 8 else current_year - 1


# =====================
# Announcement Views
# =====================

class ListCreateAnnouncementView(generics.ListCreateAPIView):
    """
    Create announcements. Only faculty/staff can create (BR-DEPT-001).
    Sends notification to department users on creation (BR-DEPT-014).
    """
    permission_classes = [IsAuthenticated, IsFacultyOrStaff]

    def post(self, request):
        create_announcement_service(
            maker_user=request.user,
            message=request.data.get('message', ''),
            batch=request.data.get('batch', 'ALL'),
            programme=request.data.get('programme', 'ALL'),
            department=request.data.get('department', 'ALL'),
            upload_announcement=request.FILES.get('upload_announcement')
        )
        return Response({"detail": "Announcement created"}, status=status.HTTP_201_CREATED)


class AnnouncementDeleteView(APIView):
    """
    Delete announcements. Only HOD or Admin can delete (BR-DEPT-004).
    """
    permission_classes = [IsAuthenticated, IsHODOrDeptAdmin]

    def delete(self, request):
        ann_ids = request.data.get('announcement_ids', [])
        if not ann_ids:
            return Response({"detail": "No announcement IDs provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = Announcements.objects.filter(id__in=ann_ids).delete()[0]
        return Response(
            {"detail": f"Successfully deleted {deleted_count} announcement(s)."},
            status=status.HTTP_204_NO_CONTENT
        )

    def put(self, request):
        """
        Edit or hide an announcement.
        Expects: { "id": 1, "message": "Updated message", "is_hidden": true }
        """
        ann_id = request.data.get('id')
        if not ann_id:
            return Response({"detail": "Announcement ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            announcement = Announcements.objects.get(id=ann_id)
            if 'message' in request.data:
                announcement.message = request.data.get('message')
            if 'is_hidden' in request.data:
                announcement.is_hidden = request.data.get('is_hidden')
            announcement.save()
            return Response({"detail": "Announcement updated successfully."}, status=status.HTTP_200_OK)
        except Announcements.DoesNotExist:
            return Response({"detail": "Announcement not found."}, status=status.HTTP_404_NOT_FOUND)


# =====================
# Department Info Views
# =====================

class DepMainAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Efficiently fetch ExtraInfo and Department
        user_info = ExtraInfo.objects.select_related('department').filter(user=user).first()
        
        department_name = "Unknown"
        if user_info and user_info.department:
            department_name = user_info.department.name

        # Check designations to determine role - Prioritize administrative roles
        designations = user.holds_designations.values_list('designation__name', flat=True)
        designations_lower = [d.lower() for d in designations]

        is_hod = any('hod' in d for d in designations_lower)
        is_admin = any('admin' in d for d in designations_lower)
        is_faculty = 'faculty' in designations_lower
        is_student = 'student' in designations_lower
        
        if is_hod:
            # Return a string containing 'hod' so frontend detects it
            user_designation = "hod"
            # Try to be more specific if possible (optional but helpful)
            for d in designations:
                if 'HOD' in d:
                    user_designation = d
                    break
        elif is_admin:
            user_designation = "dept_admin"
            for d in designations:
                if 'admin' in d.lower():
                    user_designation = d
                    break
        elif is_faculty:
            user_designation = "faculty"
        elif is_student:
            user_designation = "student"
        else:
            user_designation = "staff"

        response_data = {
            "user_designation": user_designation,
            "department": department_name,
        }

        return Response(data=response_data, status=status.HTTP_200_OK)

        
class FacAPIView(APIView):
    def get(self,request):
        usrnm = get_object_or_404(User, username=request.user.username)
        user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()

        # Serialize the data into JSON formats
        data = {
            "user_designation": user_info.user_type,
        }

        return Response(data)
    
class StaffAPIView(APIView):
    def get(self,request):
        usrnm = get_object_or_404(User, username=request.user.username)
        user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=usrnm).first()

        # Serialize the data into JSON formats
        data = {
            "user_designation": user_info.user_type,
        }

        return Response(data)


# =====================
# Announcements Data Views
# =====================

class AnnouncementsDataAPIView(APIView):
    def get(self, request, bid):
        filter_branch = decode_branch(bid)
        if not filter_branch:
            return Response({'detail': 'Invalid bid value'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        programme = "ALL"
        batch = "ALL"

        # If it's a student, we should filter by their specific programme and batch
        student = Student.objects.filter(id__user=user).first()
        if student:
            programme = student.programme
            # Map absolute batch back to relative Year-X for display filtering
            current_year = datetime.now().year
            current_month = datetime.now().month
            yearset = current_year if current_month > 8 else current_year - 1
            # Batch is e.g. 2022. Year-3 = 2024 - 2022 + 1 = 3
            try:
                relative_year = int(yearset) - int(student.batch) + 1
                batch = f"Year-{relative_year}"
            except:
                batch = "ALL"

        ann = get_announcements_selector(
            department=filter_branch,
            programme=programme,
            batch=batch
        )
        ann_serialized = AnnouncementSerializer(ann, many=True).data
        return Response(ann_serialized, status=status.HTTP_200_OK)


# =====================
# Faculty Data Views
# =====================

class FacultyDataAPIView(APIView):
    def get(self, request, bid):
        filter_branch = decode_branch(bid)
        if not filter_branch:
            return Response({'detail': 'Invalid bid value'}, status=status.HTTP_400_BAD_REQUEST)
        
        fac=ExtraInfo.objects.filter(department__name=filter_branch,user_type='faculty')
        response_data = ExtraInfoSerializer(fac, many=True).data
        return Response(response_data, status=status.HTTP_200_OK)
    

def decode_branch(bid):
    try:
        branch = bid.replace('_', ' ')
        match = re.match(r"^([a-zA-Z]+)", branch)
        if match:
            return branch  # Return the branch name

    except (IndexError, KeyError):
        return None  # Handle malformed bid values


# =====================
# Student Data Views
# =====================

class AllStudentsAPIView(APIView):
    def get(self, request, bid):
        # Decode bid to filter criteria
        filter_criteria = decode_bid(bid)
        if not filter_criteria:
            return Response({'detail': 'Invalid bid value'}, status=status.HTTP_400_BAD_REQUEST)

        # Query the student list based on filter criteria
        student_list = Student.objects.filter(
            id__user_type='student',
            **filter_criteria
        ).select_related('id')

        # Create a nested dictionary with programme, year, and specialization
        response_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        # Populate the dictionary by programme, year, and department
        for student in student_list:
            programme = student.programme  # E.g., 'B.Tech'
            year = student.batch  # E.g., '2022'
            department = student.specialization  # E.g., 'CSE'
            serializer = StudentSerializer(student)
            response_data[programme][year][department].append(serializer.data)

        # Convert defaultdict to a regular dict for JSON response
        response_data = {prog: {yr: dict(depts) for yr, depts in years.items()} for prog, years in response_data.items()}

        return Response(response_data, status=status.HTTP_200_OK)


class StudentCoursesAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStudentOnly]

    def get(self, request):
        courses = get_student_courses_selector(request.user)
        results = []
        for c in courses:
            results.append({
                'id': c.curriculum_id,
                'course_code': c.course_code,
                'course_name': c.course_id.course_name,
                'sem': c.sem
            })
        return Response(results, status=status.HTTP_200_OK)

def decode_bid(bid):
    """Decode bid into filter criteria."""
    try:
        match = re.match(r"([a-zA-Z]+)(\d+)([a-zA-Z]+)", bid)
        if match:
            level = match.group(1)  # e.g., 'btech'
            year = match.group(2)   # e.g., '1'
            specialization = match.group(3)  # e.g., 'CSE'
        
            # Map the level to program name and process year
            programme = {
                'btech': 'B.Tech',
                'bdes': 'B.Des',
                'mtech': 'M.Tech',
                'phd': 'PhD',  
            }.get(level.lower(), None)

            if programme:
                return {
                    'programme': programme,
                    'batch': int(yearset) - int(year) + 1,  # Example: calculate batch based on year
                    'specialization': specialization.upper()  # Normalize specialization to uppercase
                }
    except (IndexError, KeyError):
        return None  # Handle malformed bid values


# =====================
# Department Information Views
# =====================

class InformationAPIView(generics.ListAPIView):
    queryset = Information.objects.all()
    serializer_class = InformationSerializer
    permission_classes = (IsFacultyStaffOrReadOnly,)

class InformationUpdateAPIView(APIView):
    def put(self, request):
        # Ensure the data only contains phone_number, email, and facilities
        data = request.data
        fields_to_update = {key: data[key] for key in ["phone_number", "email", "facilites"] if key in data}

        # Get the department string from the request
        department_name = data.get("department")

        # Get the department info using the department name string
        department_info = DepartmentInfo.objects.filter(name=department_name).first()

        if not department_info:
            return Response({"detail": "Department not found."}, status=status.HTTP_404_NOT_FOUND)

        # Update or create the Information entry for the department
        information_instance, created = Information.objects.update_or_create(
            department=department_info,
            defaults=fields_to_update
        )

        serializer = InformationSerializer(information_instance)
        if created:
            message = "Information created successfully."
        else:
            message = "Information updated successfully."

        return Response({"message": message, "data": serializer.data}, status=status.HTTP_200_OK)


# =====================
# Lab Views
# =====================

class LabListView(generics.ListAPIView):
    queryset = Lab.objects.all()  # Fetch all lab entries
    serializer_class = LabSerializer


class LabAPIView(APIView):
    def post(self, request):
        data = request.data

        # Ensure all required fields are in the data
        if not all(key in data for key in ["department", "location", "name", "capacity"]):
            return Response({"detail": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the Lab instance directly with the data provided
        serializer = LabSerializer(data=data)
        if serializer.is_valid():
            lab = serializer.save()  # No need to set a department object
            return Response(LabSerializer(lab).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LabDeleteAPIView(APIView):
    def delete(self, request):
        lab_ids = request.data.get('lab_ids', [])
        
        if not lab_ids:
            return Response({"detail": "No lab IDs provided."}, status=status.HTTP_400_BAD_REQUEST)

        deleted_count = 0
        for lab_id in lab_ids:
            try:
                lab = Lab.objects.get(id=lab_id)
                lab.delete()
                deleted_count += 1
            except Lab.DoesNotExist:
                return Response({"detail": f"Lab with id {lab_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"detail": f"Successfully deleted {deleted_count} labs."}, status=status.HTTP_204_NO_CONTENT)
    

# =====================
# Feedback Views (T5: Permission fix - BR-DEPT-008)
# =====================

class FeedbackCreateAPIView(generics.CreateAPIView):
    """
    Submit department feedback. Only students and faculty can submit (BR-DEPT-008).
    Sends notification to HOD/Admin on new feedback (T8: BR-DEPT-014).
    """
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated, IsStudentOrFaculty]

    def perform_create(self, serializer):
        import json
        user = self.request.user
        raw_remark = serializer.validated_data.get('remark', '')
        course_name = self.request.data.get('course_name', 'General')
        course_id = self.request.data.get('course_id', None)

        json_remark = json.dumps({
            'text': raw_remark,
            'status': 'New',
            'admin_remarks': '',
            'submitter': user.username,
            'course': course_name,
            'course_id': course_id
        })
        feedback = serializer.save(remark=json_remark)

        # Notification logic
        try:
            # 1. Always notify HOD
            hod_recipients = User.objects.filter(
                holds_designations__designation__name__startswith='HOD'
            ).distinct()
            
            if hod_recipients.exists():
                department_notif(
                    user, hod_recipients,
                    f"New {course_name} feedback for {feedback.department}: {feedback.rating}"
                )

            # 2. If course specific, notify instructor
            if course_id:
                instructors = Curriculum_Instructor.objects.filter(
                    curriculum_id_id=course_id
                ).select_related('instructor_id__user')
                
                instructor_users = [ins.instructor_id.user for ins in instructors]
                if instructor_users:
                    department_notif(
                        user, instructor_users,
                        f"Course Feedback received for {course_name}: {feedback.rating}"
                    )
        except Exception as e:
            print(f"Feedback notification error: {e}")

class FeedbackListView(generics.ListAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Feedback.objects.all()
        
        # 1. Check if user is HOD or Admin (Full Access)
        user_designations = user.holds_designations.values_list('designation__name', flat=True)
        is_hod_or_admin = any('hod' in d.lower() or 'admin' in d.lower() for d in user_designations)
        
        if is_hod_or_admin:
            return queryset

        # 2. If Faculty, filter by courses they teach (Restricted Access)
        is_faculty = ExtraInfo.objects.filter(user=user, user_type='faculty').exists() or \
                     any('professor' in d.lower() or 'faculty' in d.lower() for d in user_designations)
        
        if is_faculty:
            from applications.academic_information.models import Curriculum_Instructor
            from django.db.models import Q
            
            # Use the user's ExtraInfo to find taught curriculums
            user_info = ExtraInfo.objects.filter(user=user).first()
            if not user_info:
                return queryset.none()

            taught_curriculums = Curriculum_Instructor.objects.filter(
                instructor_id=user_info
            ).values_list('curriculum_id', flat=True)

            if not taught_curriculums:
                return queryset.filter(remark__contains=f'"submitter": "{user.username}"')
            else:
                q_objects = Q()
                for cid in taught_curriculums:
                    # Highly robust search: Match the ID in any JSON format
                    q_objects |= Q(remark__contains=f'"course_id": {cid}')
                    q_objects |= Q(remark__contains=f'"course_id":{cid}')
                    q_objects |= Q(remark__contains=f'"course_id": "{cid}"')
                    q_objects |= Q(remark__contains=f'"course_id":"{cid}"')
                
                # Return both feedback they received for their courses and feedback they submitted
                return queryset.filter(q_objects) | queryset.filter(remark__contains=f'"submitter": "{user.username}"')

        # 3. If Student, filter by their own username in the remark JSON
        is_student = any('student' in d.lower() for d in user_designations) or \
                     ExtraInfo.objects.filter(user=user, user_type='student').exists()
        
        if is_student:
            # We match the submitter field we saved in perform_create
            return queryset.filter(remark__contains=f'"submitter": "{user.username}"')

        # 4. Default: No access if roles don't match
        return queryset.none()


class FeedbackUpdateAPIView(APIView):
    """
    Update feedback status and add admin remarks.
    Only HOD or Admin can perform this. (BR-DEPT-009)
    """
    permission_classes = [IsAuthenticated, IsHODOrDeptAdmin]

    def put(self, request, pk):
        import json
        try:
            feedback = Feedback.objects.get(pk=pk)
        except Feedback.DoesNotExist:
            return Response({'error': 'Feedback not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            current_remark = json.loads(feedback.remark)
        except (ValueError, TypeError):
            current_remark = {'text': feedback.remark, 'submitter': 'Anonymous'}

        new_status = request.data.get('status', current_remark.get('status', 'New'))
        admin_remarks = request.data.get('admin_remarks', current_remark.get('admin_remarks', ''))

        current_remark['status'] = new_status
        current_remark['admin_remarks'] = admin_remarks

        feedback.remark = json.dumps(current_remark)
        feedback.save()

        submitter_username = current_remark.get('submitter', '')
        if submitter_username and submitter_username != 'Anonymous':
            try:
                submitter_user = User.objects.filter(username=submitter_username).first()
                if submitter_user:
                    department_notif(
                        request.user, submitter_user,
                        f"Your feedback status has been updated to {new_status}"
                    )
            except Exception as e:
                pass

        serializer = FeedbackSerializer(feedback)
        return Response(serializer.data, status=status.HTTP_200_OK)


# =====================
# Department Update Approval Views (DEPT-UC-010, DEPT-UC-012)
# =====================
from applications.department.models import SpecialRequest

class DepartmentUpdateProposalCreateView(APIView):
    """
    Create a SpecialRequest for Department Info update (DEPT-UC-010).
    Allows HOD/Admin/Faculty to propose changes.
    """
    permission_classes = [IsAuthenticated, IsFacultyOrStaff]

    def post(self, request):
        import json
        user = request.user
        usrnm = get_object_or_404(User, username=user.username)
        user_info = ExtraInfo.objects.filter(user=usrnm).first()
        
        department_name = user_info.department.name if user_info.department else "Unknown"

        data = request.data
        fields_to_update = {key: data[key] for key in ["phone_number", "email", "facilites"] if key in data}
        
        json_changes = json.dumps(fields_to_update)[:200]  # Ensure it fits in max_length=200

        SpecialRequest.objects.create(
            request_maker=user_info,
            brief='DEPT_UPDATE',
            request_details=json_changes,
            status='Pending',
            remarks=str(department_name)[:300],
            request_receiver='HOD'
        )
        
        # Notify HOD
        try:
            recipients = User.objects.filter(holds_designations__designation__name__startswith='HOD')
            department_notif(user, recipients, f"New Department Profile Update Proposal received.")
        except Exception:
            pass

        return Response({'message': 'Proposal created successfully.'}, status=status.HTTP_201_CREATED)

class DepartmentUpdateProposalReviewView(APIView):
    """
    HOD approves/rejects Department Info update (DEPT-UC-012).
    """
    permission_classes = [IsAuthenticated, IsHODOrDeptAdmin]  # Assuming admin can also fetch it

    def get(self, request):
        # List all pending dept updates
        updates = SpecialRequest.objects.filter(brief='DEPT_UPDATE').order_by('-request_date')
        
        results = []
        for u in updates:
            results.append({
                'id': u.id,
                'proposer': u.request_maker.user.username,
                'request_date': u.request_date,
                'status': u.status,
                'department': u.remarks,
                'changes': u.request_details
            })
        return Response(results, status=status.HTTP_200_OK)

    def put(self, request, pk):
        import json
        try:
            update_req = SpecialRequest.objects.get(pk=pk, brief='DEPT_UPDATE')
        except SpecialRequest.DoesNotExist:
            return Response({'error': 'Proposal not found'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')
        
        if action == 'approve':
            # Apply changes
            department_name = update_req.remarks
            department_info = DepartmentInfo.objects.filter(name=department_name).first()
            if department_info:
                try:
                    changes = json.loads(update_req.request_details)
                    Information.objects.update_or_create(
                        department=department_info,
                        defaults=changes
                    )
                except Exception as e:
                    pass
            update_req.status = 'Approved'
            update_req.save()
            return Response({'message': 'Approved successfully'}, status=status.HTTP_200_OK)
            
        elif action == 'reject':
            update_req.status = 'Rejected'
            update_req.save()
            return Response({'message': 'Rejected successfully'}, status=status.HTTP_200_OK)
            
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)


# =====================
# Facility Views
# =====================

# View for listing and creating facilities
class FacilityListCreateAPIView(generics.ListCreateAPIView):
    queryset = Facility.objects.all()  # Get all facilities
    serializer_class = FacilitiesSerializer  # Use FacilitiesSerializer

    def get(self, request):
        # List all the facilities
        facilities = Facility.objects.all()
        serializer = FacilitiesSerializer(facilities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # Create a new facility
        serializer = FacilitiesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Save the new facility to the database
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# View for retrieving, updating, and deleting a single facility
class FacilityDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Facility.objects.all()  # Get all facilities
    serializer_class = FacilitiesSerializer  # Use FacilitiesSerializer

    def get(self, request, pk):
        # Retrieve a specific facility
        facility = self.get_object()  # Get the facility by pk
        serializer = FacilitiesSerializer(facility)
        return Response(serializer.data)

    def put(self, request, pk):
        # Update a specific facility
        facility = self.get_object()  # Get the facility by pk
        serializer = FacilitiesSerializer(facility, data=request.data)
        if serializer.is_valid():
            serializer.save()  # Save the updated data
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        # Delete a specific facility
        facility = self.get_object()  # Get the facility by pk
        facility.delete()  # Delete the facility from the database
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class FacilityBulkDeleteAPIView(APIView):
    def delete(self, request):
        ids = request.data.get("facility_ids", [])
        if not ids:
            return Response({"detail": "No facility IDs provided."}, status=status.HTTP_400_BAD_REQUEST)
        Facility.objects.filter(id__in=ids).delete()
        return Response({"detail": "Facilities deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# =====================
# Stock Views (T1: DEPT-WF-103 Stock Workflow)
# =====================

class StockItemListCreateView(generics.ListCreateAPIView):
    """
    List all stock items or create new ones.
    GET: Any authenticated user can view stock.
    POST: Only HOD/DeptAdmin can add stock items.
    """
    serializer_class = StockItemSerializer
    permission_classes = [IsAuthenticated, IsHODOrDeptAdmin]

    def get_queryset(self):
        department = self.request.query_params.get('department', None)
        return get_stock_items_selector(department=department)

    def perform_create(self, serializer):
        stock_item = serializer.save()
        # Create audit log entry
        user_info = ExtraInfo.objects.filter(user=self.request.user).first()
        if user_info:
            StockLog.objects.create(
                stock_item=stock_item,
                action='Add',
                performed_by=user_info,
                quantity=stock_item.quantity,
                remarks=f"Stock item '{stock_item.name}' added to inventory"
            )


class StockRequestCreateView(APIView):
    """
    Submit a stock request (DEPT-UC-004).
    Any faculty/staff can submit a stock request.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            stock_request = create_stock_request_service(
                requester_user=request.user,
                stock_item_id=request.data.get('stock_item'),
                quantity_requested=request.data.get('quantity_requested'),
                remarks=request.data.get('remarks', '')
            )
            return Response(StockRequestSerializer(stock_request).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StockRequestListView(generics.ListAPIView):
    """
    List stock requests filtered by department.
    """
    serializer_class = StockRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        department = self.request.query_params.get('department', None)
        status_filter = self.request.query_params.get('status', None)
        return get_stock_requests_selector(department=department, status=status_filter)


class StockApprovalView(APIView):
    """
    Approve or reject a stock request (DEPT-UC-005).
    Only HOD can approve/reject.
    """
    permission_classes = [IsAuthenticated, IsHOD]

    def put(self, request, pk):
        try:
            stock_request = approve_stock_request_service(
                approver_user=request.user,
                request_id=pk,
                action=request.data.get('action'),
                remarks=request.data.get('remarks', '')
            )
            return Response(StockRequestSerializer(stock_request).data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StockIssuanceView(APIView):
    """
    Issue approved stock (DEPT-UC-006).
    Only DeptAdmin can issue stock. Updates inventory quantities.
    """
    permission_classes = [IsAuthenticated, IsDeptAdmin]

    def put(self, request, pk):
        try:
            stock_request = issue_stock_service(
                issuer_user=request.user,
                request_id=pk,
                remarks=request.data.get('remarks', '')
            )
            return Response(StockRequestSerializer(stock_request).data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StockLogListView(generics.ListAPIView):
    """
    View stock audit trail.
    """
    serializer_class = StockLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        department = self.request.query_params.get('department', None)
        return get_stock_logs_selector(department=department)
