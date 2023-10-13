from django.contrib import admin
from .models import Team,MatchResult,Points

# Register your models here.

admin.site.register(Team)
admin.site.register(MatchResult)
admin.site.register(Points)