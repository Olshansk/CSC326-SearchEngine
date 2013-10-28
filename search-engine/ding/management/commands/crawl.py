__author__ = 'Amandeep Grewal'

import urllib2
import urlparse
from collections import defaultdict
import re
from optparse import make_option
from cProfile import Profile
import pstats
import StringIO
from django.core.management.base import BaseCommand
from BeautifulSoup import *
from ding.models import Word, Document, WordOccurrence, DocumentLink
import sys
import traceback


WORD_SEPARATORS = re.compile(r'\s|\n|\r|\t|[^a-zA-Z0-9\-_]')


class Crawler(object):
    """Represents 'Googlebot'. Populates a database by crawling and indexing
    a subset of the Internet.

    This crawler keeps track of font sizes and makes it simpler to manage word
    ids and document ids."""

    def __init__(self, url_file):
        """Initialize the crawler with a connection to the database to populate
        and with the file containing the list of seed URLs to begin indexing."""
        self._url_queue = []

        # functions to call when entering and exiting tags that we don't specify font sizes for
        self._enter = defaultdict(lambda *a, **ka: self._visit_ignore)
        self._exit = defaultdict(lambda *a, **ka: self._visit_ignore)

        # add a link to our graph, and indexing info to the related page
        self._enter['a'] = self._visit_a

        # record the currently indexed document's title an increase
        # the font size
        def visit_title(*args, **kargs):
            self._visit_title(*args, **kargs)
            self._increase_font_factor(7)(*args, **kargs)

        # increase the font size when we enter these tags
        self._enter['b'] = self._increase_font_factor(2)
        self._enter['strong'] = self._increase_font_factor(2)
        self._enter['i'] = self._increase_font_factor(1)
        self._enter['em'] = self._increase_font_factor(1)
        self._enter['h1'] = self._increase_font_factor(7)
        self._enter['h2'] = self._increase_font_factor(6)
        self._enter['h3'] = self._increase_font_factor(5)
        self._enter['h4'] = self._increase_font_factor(4)
        self._enter['h5'] = self._increase_font_factor(3)
        self._enter['title'] = visit_title

        self._enter['meta'] = self._enter_meta

        # decrease the font size when we exit these tags
        self._exit['b'] = self._increase_font_factor(-2)
        self._exit['strong'] = self._increase_font_factor(-2)
        self._exit['i'] = self._increase_font_factor(-1)
        self._exit['em'] = self._increase_font_factor(-1)
        self._exit['h1'] = self._increase_font_factor(-7)
        self._exit['h2'] = self._increase_font_factor(-6)
        self._exit['h3'] = self._increase_font_factor(-5)
        self._exit['h4'] = self._increase_font_factor(-4)
        self._exit['h5'] = self._increase_font_factor(-3)
        self._exit['title'] = self._increase_font_factor(-7)

        # never go in and parse these tags
        self._ignored_tags = set([
            'script', 'link', 'embed', 'iframe', 'frame',
            'noscript', 'object', 'svg', 'canvas', 'applet', 'frameset',
            'textarea', 'style', 'area', 'map', 'base', 'basefont', 'param',
        ])

        # set of words to ignore
        self._ignored_words = set([
            '', 'the', 'of', 'at', 'on', 'in', 'is', 'it',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
            'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
            'u', 'v', 'w', 'x', 'y', 'z', 'and', 'or',
        ])

        # keep track of some info about the page we are currently parsing
        self._curr_depth = 0
        self._font_size = 0
        self._curr_description_words = []
        self._curr_document = None
        self._words_found = []
        self._outgoing_urls = defaultdict(lambda: 0)
        self._unique_words = []

        # get all urls into the queue
        try:
            with open(url_file, 'r') as f:
                for line in f:
                    self._url_queue.append((self._fix_url(line.strip(), ""), 0))
        except IOError:
            pass

    @staticmethod
    def _fix_url(curr_url, rel):
        """Given a url and either something relative to that url or another url,
        get a properly parsed url."""

        rel_l = rel.lower()
        if rel_l.startswith("http://") or rel_l.startswith("https://"):
            curr_url, rel = rel, ""

        # compute the new url based on import
        curr_url = urlparse.urldefrag(curr_url)[0]
        parsed_url = urlparse.urlparse(curr_url)
        return urlparse.urljoin(parsed_url.geturl(), rel)

    @staticmethod
    def _attr(elem, attr):
        """An html attribute from an html element. E.g. <a href="">, then
        attr(elem, "href") will get the href or an empty string."""
        try:
            return elem[attr]
        except:
            return ""

    def _visit_title(self, elem):
        """Called when visiting the <title> tag."""
        title_text = self._text_of(elem).strip()
        self._curr_document.title = title_text
        print "    document title=" + repr(title_text)

    def _visit_a(self, elem):
        """Called when visiting <a> tags."""

        dest_url = self._fix_url(self._curr_document.url, self._attr(elem, "href"))

        #print "href="+repr(dest_url), \
        #      "title="+repr(attr(elem,"title")), \
        #      "alt="+repr(attr(elem,"alt")), \
        #      "text="+repr(self._text_of(elem))

        # add the just found URL to the url queue
        self._url_queue.append((dest_url, self._curr_depth))

        self._outgoing_urls[dest_url] += 1

        # TODO add title/alt/text to index for destination url

    def _enter_meta(self, elem):
        """Check meta tag for description"""
        if self._attr(elem, "name") == "description":
            self._curr_document.description = self._attr(elem, "content")

    def _increase_font_factor(self, factor):
        """Increase/decrease the current font size."""

        def increase_it(elem):
            self._font_size += factor

        return increase_it

    def _visit_ignore(self, elem):
        """Ignore visiting this type of tag"""
        pass

    def _add_text(self, elem):
        """Add some text to the document. This records word ids and word font sizes
        into the self._curr_words list for later processing."""
        words = WORD_SEPARATORS.split(elem.string.lower())
        for word in words:
            word = word.strip()
            # If word isn't empty add it to description array
            if word:
                self._curr_description_words.append(word)
            if word in self._ignored_words:
                continue

            self._words_found.append((word, self._font_size))

    def _text_of(self, elem):
        """Get the text inside some element without any tags."""
        if isinstance(elem, Tag):
            text = []
            for sub_elem in elem:
                text.append(self._text_of(sub_elem))

            return " ".join(text)
        else:
            return elem.string

    def _index_document(self, soup_data):
        """Traverse the document in depth-first order and call functions when entering
        and leaving tags. When we come across some text, add it into the index. This
        handles ignoring tags that we have no business looking at."""

        class DummyTag(object):
            next = False
            name = ''

        class NextTag(object):
            def __init__(self, obj):
                self.next = obj

        tag = soup_data.html
        stack = [DummyTag(), soup_data.html]

        while tag and tag.next:
            tag = tag.next

            # html tag
            if isinstance(tag, Tag):

                if tag.parent != stack[-1]:
                    self._exit[stack[-1].name.lower()](stack[-1])
                    stack.pop()

                tag_name = tag.name.lower()

                # ignore this tag and everything in it
                if tag_name in self._ignored_tags:
                    if tag.nextSibling:
                        tag = NextTag(tag.nextSibling)
                    else:
                        self._exit[stack[-1].name.lower()](stack[-1])
                        stack.pop()
                        tag = NextTag(tag.parent.nextSibling)

                    continue

                # enter the tag
                self._enter[tag_name](tag)
                stack.append(tag)

            # text (text, cdata, comments, etc.)
            else:
                self._add_text(tag)

    @staticmethod
    def clean_db():
        """Remove all words and documents from database"""

        Word.objects.all().delete()
        Document.objects.all().delete()
        WordOccurrence.objects.all().delete()

    @staticmethod
    def get_inverted_index():
        """Get a dictionary mapping word_id to doc_id"""

        inv_index = defaultdict(set)

        for word in Word.objects.prefetch_related('document_set'):
            for doc in word.document_set.all():
                inv_index[word.id].add(doc.id)

        return dict(inv_index)

    @staticmethod
    def get_resolved_inverted_index():
        """Get a dictionary mapping words to urls"""

        resolved_index = defaultdict(set)

        for word in Word.objects.prefetch_related('document_set'):
            for doc in word.document_set.all():
                resolved_index[word.text].add(doc.url)

        return dict(resolved_index)

    @staticmethod
    def calculate_all_pagerank():
        #PR(A) = (1-d) + d (PR(T1)/C(T1) + ... + PR(Tn)/C(Tn))

        d = 0.85
        for i in xrange(0, 10):
            print "Running iteration " + str(i) + " of pagerank calculation"
            Word.objects.count()
            for doc in queryset_iterator(Document.objects.filter(visited=True).prefetch_related('incoming_link').only("pagerank").all()):
                doc.pagerank = 1 - d
                for doc_link in queryset_iterator(doc.incoming_link.all()):
                    outgoing_doc = doc_link.outgoing_link
                    single_page_rank = outgoing_doc.pagerank / outgoing_doc.outgoing_links.count()
                    doc.pagerank += d * doc_link.count * single_page_rank
                doc.save()

    def _batch_query_words(self):
        """Query the database for word rows corresponding to words found in
        the current document, and return it as dictionary mapping word strings
        to the word row (represented by a Word object)"""

        word_dict = {}

        for x in xrange(0, len(self._unique_words), 999):
            chunk_of_word_list = self._unique_words[x:x + 999]
            for word_in_db in Word.objects.filter(text__in=chunk_of_word_list):
                word_dict[word_in_db.text] = word_in_db

        return word_dict

    def _save_only_words(self):
        """Save words to the database"""

        words_to_bulk_create = []
        queried_words = self._batch_query_words()

        for word in self._unique_words:
            if word not in queried_words:
                words_to_bulk_create.append(Word(text=word))
        Word.objects.bulk_create(words_to_bulk_create)

    def _save_word_occurrences(self):
        """Save words to document relationship to database"""

        word_occurrences = []
        queried_words = self._batch_query_words()

        for word, font_size in self._words_found:
            word_occurrences.append(WordOccurrence(word=queried_words[word],
                                                   document=self._curr_document,
                                                   font_size=font_size))

        WordOccurrence.objects.bulk_create(word_occurrences)

    def _save_words(self):
        """Save words and words-to-documents relationship to database"""

        self._unique_words = list(set(map(lambda w: w[0], self._words_found)))
        self._save_only_words()
        self._save_word_occurrences()

    def _batch_query_documents(self):
        """Query the database for document rows corresponding to outgoing links
        found in the current document, and return it as dictionary mapping urls
        to the document row (represented by a Document object)"""

        doc_dict = {}

        for x in xrange(0, len(self._outgoing_urls), 999):
            chunk_of_doc_list = self._outgoing_urls.keys()[x:x + 999]
            for doc_in_db in Document.objects.filter(url__in=chunk_of_doc_list):
                doc_dict[doc_in_db.url] = doc_in_db

        return doc_dict

    def _save_new_outgoing_docs(self):
        """Save outgoing links to the database"""

        docs_to_bulk_create = []
        queried_docs = self._batch_query_documents()

        for url, _ in self._outgoing_urls.iteritems():
            if url not in queried_docs:
                docs_to_bulk_create.append(Document(url=url))
        Document.objects.bulk_create(docs_to_bulk_create)

    def _save_outgoing_links(self):
        doc_links = []
        queried_docs = self._batch_query_documents()
        for url, url_count in self._outgoing_urls.iteritems():
            doc_links.append(DocumentLink(outgoing_link=self._curr_document,
                                          incoming_link=queried_docs[url],
                                          count=url_count))
        DocumentLink.objects.bulk_create(doc_links)

    def _save_document(self):
        """Save document and document-to-document relationship to database"""

        self._curr_document.save()
        self._save_new_outgoing_docs()
        self._save_outgoing_links()

    def _save(self):
        """Save all data obtained while crawling current page to database"""

        self._save_document()
        self._save_words()

    def crawl(self, depth=2, timeout=3):
        """Crawl the web!"""

        while len(self._url_queue):
            url, depth_ = self._url_queue.pop()

            # skip this url; it's too deep
            if depth_ > depth:
                continue

            self._curr_document = None

            doc_from_db = Document.objects.filter(url=url)
            if doc_from_db.exists():
                self._curr_document = doc_from_db[0]
                if self._curr_document.visited:
                    continue

            socket = None
            file_stream = None
            try:
                if url.startswith("http"):
                    socket = urllib2.urlopen(url, timeout=timeout)
                    soup_data = BeautifulSoup(socket.read())
                else:
                    file_stream = open(url, 'r')
                    soup_data = BeautifulSoup(file_stream)

                # Create new document in db if we haven't already retrieved it from above
                if not self._curr_document:
                    self._curr_document = Document(url=url)

                self._curr_description_words = []
                self._curr_depth = depth_ + 1
                self._font_size = 0
                self._words_found = []
                self._outgoing_urls = defaultdict(lambda: 0)

                print "url = " + repr(self._curr_document.url)
                self._index_document(soup_data)

                # If description from meta tag wasn't detected, fallback to the first 25 words detected instead
                if not self._curr_document.description:
                    self._curr_document.description = " ".join(self._curr_description_words[:25])

                self._curr_document.visited = True
                self._save()

                print "    description = " + str(self._curr_document.description)
                print "    num words = " + str(len(self._words_found))

            except Exception as e:
                print "Exception in user code: " + str(e)
                print '-'*60
                traceback.print_exc(file=sys.stdout)
                print '-'*60
            finally:
                if socket:
                    socket.close()
                if file_stream:
                    file_stream.close()


class Command(BaseCommand):
    help = 'Crawls a list of webpages'
    option_list = BaseCommand.option_list + (
        make_option('--test',
                    action='store_true',
                    dest='test',
                    default=False,
                    help='Test the crawler on some local HTML pages'),
        make_option('--profile',
                    action='store_true',
                    dest='profile',
                    default=False,
                    help='Profile the crawler'),
    )

    @staticmethod
    def _handle(*args, **options):
        if options['test']:
            Crawler.clean_db()
            bot = Crawler("ignored_page_test.txt")
            bot.crawl(10000)  # crawl to a big depth

            assert (Document.objects.count() == 1)  # only 1 document in list, and it has no links
            inverted_index = bot.get_resolved_inverted_index()
            for word in ['this', 'page', 'should', 'include', 'this', 'text']:
                pages = inverted_index[word]

                # All words appear only in 'ignored_test.html'
                assert (len(pages) == 1)
                assert ('ignored_test.html' in pages)

            Crawler.clean_db()

            bot = Crawler("pages_crawl_test.txt")
            bot.crawl(10000)  # crawl to a big depth
            assert (Document.objects.count() == 5)  # total of 5 pages in this crawl
            inverted_index = bot.get_resolved_inverted_index()
            assert (len(inverted_index['crawl']) == 5)  # 'crawl' occurs in all 5 pages
            assert (len(inverted_index['fifth']) == 1)  # 'fifth' occur in all 1 page
            assert ('second_page.html' in inverted_index['fifth'])  # 'fifth' occurs in 'second_page.html'

            Crawler.calculate_all_pagerank()

            #Round to eliminate float errors when the number is off by something like 0.000000000000001
            assert(("%.8f" % Document.objects.get(url="first_page.html").pagerank) == "0.15000000")
            assert(("%.8f" % Document.objects.get(url="second_page.html").pagerank) == "0.21375000")
            assert(("%.8f" % Document.objects.get(url="third_page.html").pagerank) == "0.21375000")
            assert(("%.8f" % Document.objects.get(url="fourth_page.html").pagerank) == "0.24084375")
            assert(("%.8f" % Document.objects.get(url="fifth_page.html").pagerank) == "0.24084375")

            Crawler.clean_db()
        else:
            bot = Crawler("urls.txt")
            bot.crawl(1)
            Crawler.calculate_all_pagerank()

    def handle(self, *args, **options):
        if options['profile']:
            profiler = Profile()
            s = StringIO.StringIO()

            profiler.runcall(self._handle, *args, **options)
            pstats.Stats(profiler, stream=s).sort_stats('cumulative').print_stats()
            print s.getvalue()
        else:
            Command._handle(*args, **options)


def queryset_iterator(queryset, chunk_size=1000):
    """
    Iterate over a QuerySet, 1000 rows at a time.
    """

    for x in xrange(0, queryset.count(), chunk_size):
        for row in queryset.all()[x:x + chunk_size]:
            yield row
