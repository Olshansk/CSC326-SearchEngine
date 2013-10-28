from collections import Counter
from collections import OrderedDict
import operator
import urllib

from django.core import serializers
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models.query import EmptyQuerySet

from ding.models import SearchWord, Word


RESULTS_PER_PAGE = 20


# Does setup work and renders the search page
def search(request):
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
    return render(request, 'ding/search.html', context)


# This view is used to redirect the post request from the search form
def parsed_query_redirect(request):
    query = request.POST['query']
    url = "http://localhost:8000/ding/parsed_query?query=" + query
    return redirect(url)


# Does setup work and renders the results page
def parsed_query(request):
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

    return render(request, 'ding/parsed_query.html', context)


# Used to make agex calls to retrieve more search results
def get_search_results(request, query, scroll_num):
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


# Returns a None object if there is not Word object corresponding to the keyword
def get_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None


def error_400(request):
    error = {'error_type': 400, 'request_path': request.path}
    return render(request, 'ding/error.html', error, status=400)


def error_403(request):
    error = {'error_type': 403, 'request_path': request.path}
    return render(request, 'ding/error.html', error, status=403)


def error_404(request):
    error = {'error_type': 404, 'request_path': request.path}
    return render(request, 'ding/error.html', error, status=404)


def error_500(request):
    error = {'error_type': 500, 'request_path': request.path}
    return render(request, 'ding/error.html', error, status=500)