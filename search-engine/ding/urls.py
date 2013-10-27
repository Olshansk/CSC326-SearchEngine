from django.conf.urls import patterns, url
from django.conf.urls.defaults import *
from ding import views
from django.views.generic.base import RedirectView

urlpatterns = patterns('',
                       url(r'^$', views.search, name='search'),
                       url(r'^parsed_query/(?P<query>.+)/(?P<scroll_num>(\-|)\d+)/$', views.get_search_results, name='get_search_results'),
                       url(r'^parsed_query/', views.parsed_query, name='parsed_query'),
                       url(r'^parsed_query_r/', views.parsed_query_redirect, name='parsed_query_redirect'),
)
