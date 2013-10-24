from django.conf.urls import patterns, url
from django.conf.urls.defaults import *
from ding import views

urlpatterns = patterns('',
                       url(r'^$', views.search, name='search'),
                       url(r'^parsed_query/$', views.parsed_query, name='parsed_query'),
                       url(r'^parsed_query/(?P<result_num>(\-|)\d+)/$', views.get_search_results, name='get_search_results'),
)
