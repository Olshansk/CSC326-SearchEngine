from django.conf.urls import patterns, url

from ding import views

urlpatterns = patterns('',
    url(r'^$', views.search, name='search'),
    url(r'^parsed_query/$', views.parsed_query, name='parsed_query'),
)
