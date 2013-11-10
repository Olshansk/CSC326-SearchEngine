from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from ding import views

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^ding/', include('ding.urls', namespace='ding', app_name='ding')),
                       # Examples:
                       # url(r'^$', 'search-engine.views.home', name='home'),
                       # url(r'^search-engine/', include('search-engine.foo.urls')),

                       # Uncomment the admin/doc line below to enable admin documentation:
                       # url(r'^admin/doc/', include('ding.contrib.admindocs.urls')),

                       # Uncomment the next line to enable the admin:
                       url(r'^admin/', include(admin.site.urls)),
)

handler400 = 'ding.views.error_400'
handler403 = 'ding.views.error_403'
handler404 = 'ding.views.error_404'
handler500 = 'ding.views.error_500'

