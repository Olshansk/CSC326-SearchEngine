from collections import Counter
from collections import OrderedDict
import operator
import urllib

from django.core import serializers
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models.query import EmptyQuerySet

from django.core.urlresolvers import reverse

from ding.my_sessions import SessionStore
from ding.models import SearchWord, Word

import json
import random
import string
import os.path
import httplib2

from apiclient.errors import HttpError
from apiclient.discovery import build

import oauth2client.client
from oauth2client.client import Credentials
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

from apiclient.errors import HttpError
from apiclient.discovery import build

RESULTS_PER_PAGE = 20
BASE = os.path.dirname(os.path.abspath(__file__))
CLIENT_ID = json.loads(open(os.path.join(BASE, "client_secrets.json"), 'r').read())['web']['client_id']

# The view used to sign in the user
def sign_in(request):
    if request.session.get('credentials') is not None:
        return redirect(reverse("ding:search"))
    # Generate a random starting state value
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    # Store the state
    request.session['state'] = state
    # Pass in the state and the client ID to the page
    context = {"CLIENT_ID": CLIENT_ID, "STATE":state}
    # Render the sign in page
    return render(request, 'ding/sign_in.html', context)

# Call this to properly connect and initiate the session after the user successfully logged in
def connect(request):

    # Ensure that the request is not a forgery and that the user sending this connect request is the expected user.
    if request.POST['state'.decode("utf-8")] != request.session['state']:
        return redirect(reverse("ding:error_401"))

    # Retrieve the authorization code
    code = request.POST['authCode'.decode("utf-8")]
    # Upgrade the authorization code into a credentials object
    try:
        oauth_flow = flow_from_clientsecrets(os.path.join(BASE, "client_secrets.json"), scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        return redirect(reverse("ding:error_401"))
    # Access the currently connected user
    gplus_id = credentials.id_token['sub']

    stored_credentials = request.session.get('credentials')
    stored_gplus_id = request.session.get('gplus_id')

    # Updated the credentials and id if necessary
    if stored_gplus_id != gplus_id or stored_credentials is None:
        request.session['credentials'] = credentials.to_json()
        request.session['gplus_id'] = gplus_id

    # Respond with success url
    response_data = {}
    response_data['result'] = 'Success'
    response_data['message'] = 'User authenticated and session stored.'
    response_data['redirect_url'] = reverse("ding:search")
    return HttpResponse(json.dumps(response_data), content_type="application/json")

# Disconnect the user and ends the session
def disconnect(request):
    # Check to make sure the user is logged in
    url = redirect_if_not_logged_in(request)
    if url is not None:
        return url

    # Only disconnect a connected user.
    creditionals_in_json = request.session['credentials']
    if creditionals_in_json is None:
        # Trying to disconnect a connected user so some sort of error probably occured
        return redirect(reverse("ding:error_401"))
    # Retrieve the dcredentials object
    credentials = Credentials.new_from_json(creditionals_in_json)

    # Execute HTTP GET request to revoke current token.
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's session.
        del request.session['credentials']
        request.session.delete()
        # Redirect back to sign in page
        url = reverse("ding:disconnect_sign_in");
        return redirect(url)
    else:
        # For whatever reason, the given token was invalid.
        error = {'error_type': 400, 'request_path': request.path}
        return render(request, 'ding/error.html', error, status=400)

# Does setup work and renders the search page
def search(request):
    # Check to make sure the user is logged in
    url = redirect_if_not_logged_in(request)
    if url is not None:
        return url

    # Retrieve all the keywords in the database
    set_sw = SearchWord.objects.all()
    list_sw = list(set_sw)
    # Sort all the keywords in the database in decreasing frequency order
    list_sw.sort(key=operator.attrgetter('word_freq'), reverse=True)
    words = OrderedDict()
    # Extract the top 20 most searched keywords and put them into a dictionary
    for s in list_sw[0:20]:
        words.update({s.word_text: s.word_freq})
        # Passes in the dictionary as input and renders the search html page
    
    context = {'frequency_dictionary': words.iteritems()}

    # Retrieve the user name and profile image url and add it to context
    credentials = oauth2client.client.Credentials.new_from_json(request.session['credentials'])
    user_data = user_data_from_credentials(credentials)
    context.update(user_data)

    return render(request, 'ding/search.html', context)

# This view is used to redirect the post request from the search form
def parsed_query_redirect(request):
    # Check to make sure the user is logged in
    url = redirect_if_not_logged_in(request)
    if url is not None:
        return url

    query = request.POST['query']
    url = reverse("ding:parsed_query")
    url = url + "?query=" + query
    return redirect(url)

# Does setup work and renders the results page
def parsed_query(request):
    # Check to make sure the user is logged in
    url = redirect_if_not_logged_in(request)
    if url is not None:
        return url

    # Extracts the input to this method; the search query
    query = request.GET['query']
    context = {'query': query}
    should_show_table = False
    # Splits the search query into words
    split_query = query.split()
    for word in split_query:
        # Increments the count of each keyword if its already in the databse
        # or adds it to the database if this is the first time it is encountered
        list_sw = SearchWord.objects.filter(word_text=word)
        if len(list_sw) == 0:
            sw = SearchWord(word_text=word, word_freq=1)
            sw.save()
        else:
            sw = list_sw[0]
            sw.word_freq += 1
            sw.save()

    # Determines if the table should or shouldn't be shown
    if len(split_query) > 1:
        should_show_table = True
        context.update({'frequency_dictionary': Counter(split_query).iteritems()})

    # Prepares the input and passes is it in to the HTML page to be rendered
    context.update({'num_of_words': str(len(split_query))})
    context.update({'should_show_table': should_show_table})
    # Prepare list of results to be presented - query is escaped because method expects escaped input
    filtered_docs = document_objects_for_keyword_in_range(0, urllib.quote_plus(query))
    context.update({'documents': filtered_docs})

    # Retrieve the user name and profile image url and add it to context
    credentials = oauth2client.client.Credentials.new_from_json(request.session['credentials'])
    user_data = user_data_from_credentials(credentials)
    context.update(user_data)

    return render(request, 'ding/parsed_query.html', context)

# Used to make agex calls to retrieve more search results
def get_search_results(request, query, scroll_num):
    # Check to make sure the user is logged in
    url = redirect_if_not_logged_in(request)
    if url is not None:
        return url
    
    # Retrieve list of search results
    filtered_docs = document_objects_for_keyword_in_range(int(scroll_num), query)
    # Serializes results into json
    json_data = serializers.serialize('json', filtered_docs, fields=('title', 'url', 'description'))
    return HttpResponse(json_data, mimetype="application/json")

def document_objects_for_keyword_in_range(first_index, keyword):
    #unescapes and splits the query into keywords
    keywords = list(set((urllib.unquote_plus(keyword)).split(" ")))
    query_set = EmptyQuerySet()
    # Retrieves the set of documents corresponding to each keyword
    for key in keywords:
        word = get_or_none(Word, text=key)
        if word is not None:
            query_set = query_set | word.document_set.all()
        # Orders the set, removes duplicates, and returns a list of the resultant documents
    document_objects = list(query_set.order_by("-pagerank").distinct()[
                            first_index * RESULTS_PER_PAGE: (first_index + 1) * RESULTS_PER_PAGE])
    return document_objects

# Retrieve the user's name and profile photo
def user_data_from_credentials(credentials):
    # Authorize the credentials
    http = httplib2.Http()
    http = credentials.authorize(http)
    # Get user name and image url
    users_service = build('plus', 'v1', http=http)
    profile = users_service.people().get(userId='me').execute()
    user_name = profile['displayName']
    user_image= profile['image']['url']

    return {'user_image_url':user_image, 'user_name':user_name}

# Returns a None object if there is not Word object corresponding to the keyword
def get_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None

# Prevents the user from accessing search pages if the user is not logged in
def redirect_if_not_logged_in(request):
    if request.session.get('credentials') is None:
        return redirect(reverse("ding:sign_in"))
    return None

def error_400(request):
    # Check to make sure the user is logged in
    url = redirect_if_not_logged_in(request)
    if url is not None:
        return url

    error = {'error_type': 400, 'request_path': request.path}
    return render(request, 'ding/error.html', error, status=400)

def error_401(request):
    # Check to make sure the user is logged in
    url = redirect_if_not_logged_in(request)
    if url is not None:
        return url

    error = {'error_type': 401, 'request_path': request.path}
    return render(request, 'ding/error.html', error, status=401)

def error_403(request):
    # Check to make sure the user is logged in
    url = redirect_if_not_logged_in(request)
    if url is not None:
        return url

    error = {'error_type': 403, 'request_path': request.path}
    return render(request, 'ding/error.html', error, status=403)

def error_404(request):
    # Check to make sure the user is logged in
    url = redirect_if_not_logged_in(request)
    if url is not None:
        return url

    error = {'error_type': 404, 'request_path': request.path}
    return render(request, 'ding/error.html', error, status=404)

def error_500(request):
    # Check to make sure the user is logged in
    url = redirect_if_not_logged_in(request)
    if url is not None:
        return url
    
    error = {'error_type': 500, 'request_path': request.path}
    return render(request, 'ding/error.html', error, status=500)