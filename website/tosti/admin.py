from django.contrib import admin
from django.contrib.auth.models import Group

admin.site.site_header = "T.O.S.T.I. Administration"
admin.site.site_title = "TOSTI"

admin.site.unregister(Group)
