from django.contrib import admin

# Register your models here.
from .models import (Announcements, SpecialRequest, Information, Lab,
                     Feedback, Facility, StockItem, StockRequest, StockLog)

admin.site.register(Announcements)
admin.site.register(SpecialRequest)
admin.site.register(Information)
admin.site.register(Lab)
admin.site.register(Feedback)
admin.site.register(Facility)
admin.site.register(StockItem)
admin.site.register(StockRequest)
admin.site.register(StockLog)