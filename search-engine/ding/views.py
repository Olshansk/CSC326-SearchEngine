from collections import Counter
from collections import OrderedDict
import operator
from django.core import serializers
from django.shortcuts import render
from django.http import HttpResponse
from ding.models import SearchWord, Document

RESULTS_PER_PAGE = 20

# Does setup work and renders the search page
def search(request):
    print "here"
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
    context = {'frequencyDictionary': words.iteritems()}
    return render(request, 'ding/search.html', context)

# Does setup work and renders the results page
def parsed_query(request):
    print "parsed_query"
    # Extracts the input to this method; the search query
    query = request.GET['query']

    context = {'query': query}
    shouldShowTable = False
    # Splits the search query into words
    split_query = query.split()
    for word in split_query:
        # Increments the count of each keyword if its already in the databse
        # or adds it to the database if this is the first time it is encountered
        list_sw = SearchWord.objects.filter(word_text=word)
        if (len(list_sw) == 0):
            sw = SearchWord(word_text=word, word_freq=1)
            sw.save()
        else:
            sw = list_sw[0]
            sw.word_freq += 1
            sw.save()

    # Determines if the table should or shouldn't be shown
    if (len(split_query) > 1):
        shouldShowTable = True
        context.update({'frequencyDictionary': Counter(split_query).iteritems()})

    # Prepares the input and passes is it in to the HTML page to be rendered
    context.update({'numOfWords': str(len(split_query))})
    context.update({'shouldShowTable': shouldShowTable})
    # Prepare list of results to be presented
    # TODO: don't display all docs
    filteredDocs = document_objects_for_keyword_in_range(0, "temp")
    context.update({'documents': filteredDocs})

    return render(request, 'ding/parsed_query.html', context)

def get_search_results(request, query, scroll_num):
    print "get_search_results"
    filteredDocs = document_objects_for_keyword_in_range(int(scroll_num), "temp")
    jsonData = serializers.serialize('json', filteredDocs, fields=('title','url', 'description'))
    return HttpResponse(jsonData, mimetype="application/json")

def document_objects_for_keyword_in_range(first_index, keyword):
    #TODO: retrieve objects coresponding to a keyword
    #TODO: change this to use page rank instead of ids
    documentObejcts = list(Document.objects.order_by("id")[first_index * RESULTS_PER_PAGE: (first_index + 1) * RESULTS_PER_PAGE])
    return documentObejcts

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
    return render(request, 'ding/error.html', error , status=500)