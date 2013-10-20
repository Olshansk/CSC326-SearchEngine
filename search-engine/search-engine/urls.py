from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^ding/', include('ding.urls', namespace='ding')),
                       # Examples:
                       # url(r'^$', 'search-engine.views.home', name='home'),
                       # url(r'^search-engine/', include('search-engine.foo.urls')),

                       # Uncomment the admin/doc line below to enable admin documentation:
                       # url(r'^admin/doc/', include('ding.contrib.admindocs.urls')),

                       # Uncomment the next line to enable the admin:
                       url(r'^admin/', include(admin.site.urls)),
)

#handler404 = 'ding.views.parsed_query'
