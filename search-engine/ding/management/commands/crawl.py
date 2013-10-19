__author__ = 'Amandeep Grewal'

import urllib2
import urlparse
from collections import defaultdict
import re
from optparse import make_option

from django.core.management.base import BaseCommand
from BeautifulSoup import *

from ding.models import Word, Document, WordOnPage


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

    def add_link(self, from_doc_id, to_doc_id):
        """Add a link into the database, or increase the number of links between
        two pages in the database."""
        # TODO

    def _visit_title(self, elem):
        """Called when visiting the <title> tag."""
        title_text = self._text_of(elem).strip()
        self._curr_document.title = title_text
        print "document title=" + repr(title_text)

    def _visit_a(self, elem):
        """Called when visiting <a> tags."""

        dest_url = self._fix_url(self._curr_document.url, self._attr(elem, "href"))

        #print "href="+repr(dest_url), \
        #      "title="+repr(attr(elem,"title")), \
        #      "alt="+repr(attr(elem,"alt")), \
        #      "text="+repr(self._text_of(elem))

        # add the just found URL to the url queue
        self._url_queue.append((dest_url, self._curr_depth))

        # add a link entry into the database from the current document to the
        # other document
        # self.add_link(self._curr_document.id, self.document_id(dest_url))

        # TODO add title/alt/text to index for destination url


    def _enter_meta(self, elem):
        """Check meta tag for description"""
        if self._attr(elem, "name") == "description":
            self._curr_document.description = self._attr(elem, "content")

    def _increase_font_factor(self, factor):
        """Increade/decrease the current font size."""

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

            word_created, _ = Word.objects.get_or_create(text=word)
            WordOnPage.objects.get_or_create(word=word_created,
                                             document=self._curr_document,
                                             font_size=self._font_size)

    def _text_of(self, elem):
        """Get the text inside some element without any tags."""
        if isinstance(elem, Tag):
            text = []
            for sub_elem in elem:
                text.append(self._text_of(sub_elem))

            return " ".join(text)
        else:
            return elem.string

    def _index_document(self, soup):
        """Traverse the document in depth-first order and call functions when entering
        and leaving tags. When we come across some text, add it into the index. This
        handles ignoring tags that we have no business looking at."""

        class DummyTag(object):
            next = False
            name = ''

        class NextTag(object):
            def __init__(self, obj):
                self.next = obj

        tag = soup.html
        stack = [DummyTag(), soup.html]

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
        Word.objects.all().delete()
        Document.objects.all().delete()
        WordOnPage.objects.all().delete()

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

    def crawl(self, depth=2, timeout=3):
        """Crawl the web!"""

        while len(self._url_queue):
            url, depth_ = self._url_queue.pop()

            # skip this url; it's too deep
            if depth_ > depth:
                continue

            if Document.objects.filter(url=url).exists():
                continue

            socket = None
            file_stream = None
            try:
                if url.startswith("http://"):
                    socket = urllib2.urlopen(url, timeout=timeout)
                    soup = BeautifulSoup(socket.read())
                else:
                    file_stream = open(url, 'r')
                    soup = BeautifulSoup(file_stream)

                self._curr_document = Document.objects.create()
                self._curr_document.url = url
                self._curr_description_words = []
                self._curr_depth = depth_ + 1
                self._font_size = 0
                self._index_document(soup)

                # If description from meta tag wasn't detected, fallback to the first 25 words detected instead
                if not self._curr_document.description:
                    self._curr_document.description = " ".join(self._curr_description_words[:25])

                self._curr_document.save()

                print "    url = " + repr(self._curr_document.url)
                print "    num words = " + str(self._curr_document.words.count())

            except Exception as e:
                print e
                pass
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
    )

    def _handle(self, *args, **options):
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

            Crawler.clean_db()
            return

        bot = Crawler("ignored_page_test.txt")
        bot.crawl(10000)  # crawl to a big depth

        bot = Crawler("pages_crawl_test.txt")
        bot.crawl(10000)  # crawl to a big depth

        #    def handle(self, *args, **options):
        #        profiler = Profile()
        #        profiler.runcall(self._handle, *args, **options)
        #        s = StringIO.StringIO()
        #        sortby = 'cumulative'
        #        ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
        #        ps.print_stats()
        #        print s.getvalue()
        #
        #from cProfile import Profile
        #import pstats, StringIO