from django.http import HttpResponse
from django.shortcuts import render
from collections import Counter
from ding.models import SearchWord
from collections import OrderedDict
import operator

# Does setup work and renders the search page
def search(request):
	# Retrieve all the keywords in the database
	set_sw = SearchWord.objects.all()
	list_sw = list(set_sw)
	# Sort all the keywords in the database in decreasing frequency order
	list_sw.sort(key = operator.attrgetter('word_freq'), reverse=True)
	words = OrderedDict()
	# Extract the top 20 most searched keywords and put them into a dictionary
	for s in list_sw[0:20]:
		words.update({s.word_text:s.word_freq})
	# Passes in the dictionary as input and renders the search html page
	context = {'frequencyDictionary' : words.iteritems()}
	return render(request, 'ding/search.html', context)

# Does setup work and renders the results page
def parsed_query(request):
	# Extracts the input to this method; the search query
	query = request.POST['query'].lower()
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
		context.update({'frequencyDictionary' : Counter(split_query).iteritems()})

	# Prepares the input and passes is it in to the HTML page to be rendered
	context.update({'numOfWords' : str(len(split_query))})
	context.update({'shouldShowTable' : shouldShowTable})
	return render(request, 'ding/parsed_query.html', context)
	