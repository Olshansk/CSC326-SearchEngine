from django.conf.urls import patterns, url
from django.conf.urls.defaults import *
from ding import views

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.views.generic import RedirectView

urlpatterns = patterns('',
                       url(r'^$', views.sign_in, name='sign_in'),
                       url(r'^connect/$', views.connect, name='connect'),
                       url(r'^disconnect/$', views.disconnect, name='disconnect'),
                       url(r'^disconnect/sign_in/$', RedirectView.as_view(url=reverse_lazy('ding:sign_in')), name="disconnect_sign_in"),
                       url(r'^search/$', views.search, name='search'),
                       url(r'^parsed_query/(?P<query>.+)/(?P<scroll_num>(\-|)\d+)/$', views.get_search_results, name='get_search_results'),
                       url(r'^parsed_query/', views.parsed_query, name='parsed_query'),
                       url(r'^parsed_query_redirect/', views.parsed_query_redirect, name='parsed_query_redirect'),
                       url(r'^error_401/', views.error_401, name='error_401'),
)
