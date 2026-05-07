from rest_framework import serializers
from applications.department.models import Announcements
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation,Faculty)
from applications.eis.models import (faculty_about, emp_research_projects)
from applications.department.models import Information
from applications.department.models import Lab
from applications.department.models import Feedback
from applications.department.models import Facility
from applications.department.models import StockItem, StockRequest, StockLog

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcements 
        fields = ('__all__')
        
        extra_kwargs = {
            'maker_id': {'required': False}
        }
        
    def create(self, validated_data):
        user = self.context['request'].user
        user_info = ExtraInfo.objects.all().select_related('user','department').filter(user=user).first()
        validated_data['maker_id'] = user_info
        return Announcements.objects.create(**validated_data)
    
class ExtraInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtraInfo 
        fields = ('__all__')

class SpiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Spi 
        fields = ('__all__')
        
class StudentSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='id.user.first_name', read_only=True)
    last_name = serializers.CharField(source='id.user.last_name', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'programme', 'batch', 'specialization', 
            'cpi', 'category', 'hall_no', 'room_no',
            'first_name', 'last_name'  # ✅ Add these fields
        ]
        
class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation 
        fields = ('__all__')
        
class HoldsDesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = HoldsDesignation 
        fields = ('__all__')
        
class FacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty 
        fields = ('__all__')

class faculty_aboutSerializer(serializers.ModelSerializer):
    class Meta:
        model = faculty_about 
        fields = ('__all__')
        
class emp_research_projectsSerializer(serializers.ModelSerializer):
    class Meta:
        model = emp_research_projects 
        fields = ('__all__')

class InformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Information
        fields = '__all__'  # or specify fields as needed

# serializers.py
class LabSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lab
        fields = '__all__'


class FeedbackSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    admin_remarks = serializers.SerializerMethodField()
    submitter = serializers.SerializerMethodField()
    text_remark = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = ['id', 'department', 'rating', 'remark', 'status', 'admin_remarks', 'submitter', 'text_remark']

    def _parse_remark(self, obj):
        import json
        try:
            return json.loads(obj.remark)
        except (ValueError, TypeError):
            return {}

    def get_status(self, obj):
        return self._parse_remark(obj).get('status', 'New')

    def get_admin_remarks(self, obj):
        return self._parse_remark(obj).get('admin_remarks', '')

    def get_submitter(self, obj):
        return self._parse_remark(obj).get('submitter', 'Anonymous')

    def get_text_remark(self, obj):
        import json
        try:
            data = json.loads(obj.remark)
            return data.get('text', obj.remark)
        except (ValueError, TypeError):
            return obj.remark


class FacilitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = '__all__'  # Include all fields from the model


class StockItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockItem
        fields = '__all__'


class StockRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='requester.user.username', read_only=True)
    stock_item_name = serializers.CharField(source='stock_item.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.user.username', read_only=True, default=None)
    issued_by_name = serializers.CharField(source='issued_by.user.username', read_only=True, default=None)

    class Meta:
        model = StockRequest
        fields = [
            'id', 'requester', 'requester_name', 'stock_item', 'stock_item_name',
            'quantity_requested', 'status', 'request_date', 'remarks',
            'approved_by', 'approved_by_name', 'approval_date',
            'issued_by', 'issued_by_name', 'issued_date'
        ]
        extra_kwargs = {
            'requester': {'required': False},
            'status': {'required': False},
            'approved_by': {'required': False},
            'issued_by': {'required': False},
        }


class StockLogSerializer(serializers.ModelSerializer):
    stock_item_name = serializers.CharField(source='stock_item.name', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.user.username', read_only=True)

    class Meta:
        model = StockLog
        fields = [
            'id', 'stock_item', 'stock_item_name', 'action',
            'performed_by', 'performed_by_name', 'quantity',
            'timestamp', 'remarks'
        ]