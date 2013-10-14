# Copyright (C) 2011 by Peter Goodman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

#
# Updated: Sept 13, 2013
#


import urllib2
import urlparse
from BeautifulSoup import *
from collections import defaultdict
import re

WORD_SEPARATORS = re.compile(r'\s|\n|\r|\t|[^a-zA-Z0-9\-_]')


def attr(elem, attr):
    """An html attribute from an html element. E.g. <a href="">, then
    attr(elem, "href") will get the href or an empty string."""
    try:
        return elem[attr]
    except:
        return ""


class Document:
    def __init__(self):
        self.url = None
        self.words = []
        self.id = None
        self.url = None
        self.title = None
        self.description = None

    def __repr__(self):
        return repr(vars(self))


class Crawler(object):
    """Represents 'Googlebot'. Populates a database by crawling and indexing
    a subset of the Internet.

    This crawler keeps track of font sizes and makes it simpler to manage word
    ids and document ids."""

    def __init__(self, db_conn, url_file):
        """Initialize the crawler with a connection to the database to populate
        and with the file containing the list of seed URLs to begin indexing."""
        self._url_queue = []
        self._doc_id_cache = {}
        self._word_id_cache = {}

        self.documents = dict()
        self.lexicon = dict()

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

        # TODO remove me in real version. we currently simulate database by just storing in dictionary
        self._mock_next_doc_id = 1
        self._mock_next_word_id = 1

        # keep track of some info about the page we are currently parsing
        self._curr_depth = 0
        self._font_size = 0
        self._curr_description_words = []
        self._curr_document = Document()

        # get all urls into the queue
        try:
            with open(url_file, 'r') as f:
                for line in f:
                    self._url_queue.append((self._fix_url(line.strip(), ""), 0))
        except IOError:
            pass


    # TODO remove me in real version
    def _mock_insert_document(self, url):
        """A function that pretends to insert a url into a document db table
        and then returns that newly inserted document's id."""
        ret_id = self._mock_next_doc_id
        self._mock_next_doc_id += 1

        self.documents[ret_id] = self._curr_document
        return ret_id

    # TODO remove me in real version
    def _mock_insert_word(self, word):
        """A function that pretends to insert a word into the lexicon db table
        and then returns that newly inserted word's id."""
        ret_id = self._mock_next_word_id
        self._mock_next_word_id += 1

        self.lexicon[ret_id] = word
        return ret_id

    def word_id(self, word):
        """Get the word id of some specific word."""
        if word in self._word_id_cache:
            return self._word_id_cache[word]

        # TODO: 1) add the word to the lexicon, if that fails, then the
        #          word is in the lexicon
        #       2) query the lexicon for the id assigned to this word,
        #          store it in the word id cache, and return the id.

        word_id = self._mock_insert_word(word)
        self._word_id_cache[word] = word_id
        return word_id

    def document_id(self, url):
        """Get the document id for some url."""
        if url in self._doc_id_cache:
            return self._doc_id_cache[url]

        # TODO: just like word id cache, but for documents. if the document
        #       doesn't exist in the db then only insert the url and leave
        #       the rest to their defaults.

        doc_id = self._mock_insert_document(url)
        self._doc_id_cache[url] = doc_id
        return doc_id

    def _fix_url(self, curr_url, rel):
        """Given a url and either something relative to that url or another url,
        get a properly parsed url."""

        rel_l = rel.lower()
        if rel_l.startswith("http://") or rel_l.startswith("https://"):
            curr_url, rel = rel, ""

        # compute the new url based on import
        curr_url = urlparse.urldefrag(curr_url)[0]
        parsed_url = urlparse.urlparse(curr_url)
        return urlparse.urljoin(parsed_url.geturl(), rel)

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

        dest_url = self._fix_url(self._curr_document.url, attr(elem, "href"))

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
        if attr(elem, "name") == "description":
            self._curr_document.description = attr(elem, "content")

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
            self._curr_document.words.append((self.word_id(word), self._font_size))

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

    def get_inverted_index(self):
        """Get a dictionary mapping word_id to doc_id"""

        inv_index = defaultdict(set)

        # Iterate through every document, then iterate though every word in the document,
        # and create a link from the word_id to the doc_id
        for doc_id, doc in self.documents.iteritems():
            for word_id, _ in doc.words:
                inv_index[word_id].add(doc_id)

        return dict(inv_index)

    def get_resolved_inverted_index(self):
        """Get a dictionary mapping words to urls"""

        unresolved_index = self.get_inverted_index()
        resolved_index = defaultdict(set)

        # Go through each word_id, doc_id pair in inverted index
        for word_id, doc_ids in unresolved_index.iteritems():
            # Retrieve word string from the lexicon for this word_id
            word_str = self.lexicon[word_id]
            # For every doc_id this word maps to get the url, and create a mapping from word to url
            for doc_id in doc_ids:
                resolved_index[word_str].add(self.documents[doc_id].url)

        return dict(resolved_index)

    def crawl(self, depth=2, timeout=3):
        """Crawl the web!"""
        seen = set()

        while len(self._url_queue):
            url, depth_ = self._url_queue.pop()

            # skip this url; it's too deep
            if depth_ > depth:
                continue

            self._curr_document = Document()

            doc_id = self.document_id(url)

            # we've already seen this document
            if doc_id in seen:
                continue

            seen.add(doc_id) # mark this document as visited

            socket = None
            file_stream = None
            try:
                if url.startswith("http://"):
                    socket = urllib2.urlopen(url, timeout=timeout)
                    soup = BeautifulSoup(socket.read())
                else:
                    file_stream = open(url, 'r')
                    soup = BeautifulSoup(file_stream)

                self._curr_document.url = url
                self._curr_document.id = doc_id
                self._curr_description_words = []
                self._curr_depth = depth_ + 1
                self._font_size = 0
                self._index_document(soup)

                # If description from meta tag wasn't detected, fallback to the first 25 words detected instead
                if not self._curr_document.description:
                    self._curr_document.description = " ".join(self._curr_description_words[:25])

                print "    url = " + repr(self._curr_document.url)
                print "    num words = " + str(len(self._curr_document.words))

            except Exception as e:
                print e
                pass
            finally:
                if socket:
                    socket.close()
                if file_stream:
                    file_stream.close()


if __name__ == "__main__":
    bot = Crawler(None, "ignored_page_test.txt")
    bot.crawl(10000) # crawl to a big depth

    assert(len(bot.lexicon) == 8) # manually counted 8 unique non-ignored words
    assert(len(bot.documents) == 1) # only 1 document in list, and it has no links
    inverted_index = bot.get_resolved_inverted_index()
    for word in ['this', 'page', 'should', 'include', 'this', 'text']:
        pages = inverted_index[word]

        # All words appear only in 'ignored_test.html'
        assert(len(pages) == 1)
        assert('ignored_test.html' in pages)


    bot = Crawler(None, "pages_crawl_test.txt")
    bot.crawl(10000) # crawl to a big depth
    assert(len(bot.documents) == 5) # total of 5 pages in this crawl
    inverted_index = bot.get_resolved_inverted_index()
    assert (len(inverted_index['crawl']) == 5) # 'crawl' occurs in all 5 pages
    assert (len(inverted_index['fifth']) == 1) # 'fifth' occur in all 1 page
    assert ('second_page.html' in inverted_index['fifth']) # 'fifth' occurs in 'second_page.html'