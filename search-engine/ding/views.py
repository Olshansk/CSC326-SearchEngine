from django.http import HttpResponse
from django.shortcuts import render
from collections import Counter
from ding.models import SearchWord
from collections import OrderedDict
import operator

def search(request):
	set_sw = SearchWord.objects.all()
	list_sw = list(set_sw)
	list_sw.sort(key = operator.attrgetter('word_freq'), reverse=True)
	words = OrderedDict()
	for s in list_sw[0:20]:
		words.update({s.word_text:s.word_freq})
	context = {'frequencyDictionary' : words.iteritems()}
	return render(request, 'ding/search.html', context)

def parsed_query(request):
	query = request.POST['query'].lower()
	context = {'query': query}
	shouldShowTable = False
	split_query = query.split()
	for word in split_query:
		list_sw = SearchWord.objects.filter(word_text=word)
		if (len(list_sw) == 0):
			sw = SearchWord(word_text=word, word_freq=1)
			sw.save()
		else:
			sw = list_sw[0]
			sw.word_freq += 1
			sw.save()
	
	if (len(split_query) > 1):
		shouldShowTable = True
		context.update({'frequencyDictionary' : Counter(split_query).iteritems()})

	context.update({'numOfWords' : str(len(split_query))})
	context.update({'shouldShowTable' : shouldShowTable})
	return render(request, 'ding/parsed_query.html', context)
	