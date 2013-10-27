from django.db import models


# This Model is used to store the frequency of all the keywords searched
# so that the top 20 could be extracted and shown on the front page.
class SearchWord(models.Model):
    word_text = models.CharField(max_length=200)
    word_freq = models.IntegerField(default=0)

    def __unicode__(self):
        return self.word_text + " count:" + str(self.word_freq)


class Word(models.Model):
    text = models.TextField()

    def __unicode__(self):
        return self.text


class Document(models.Model):
    url = models.URLField(max_length=1000)
    words = models.ManyToManyField(Word, through='WordOccurrence')
    title = models.TextField(max_length=1000)
    description = models.TextField(max_length=1000)
    outgoing_links = models.ManyToManyField('self',
                                            through='DocumentLink',
                                            related_name="incoming_links",
                                            symmetrical=False)
    visited = models.BooleanField(default=False)
    pagerank = models.FloatField(default=0.15)

    def __unicode__(self):
        return self.url


class WordOccurrence(models.Model):
    word = models.ForeignKey(Word)
    document = models.ForeignKey(Document)
    font_size = models.IntegerField(default=0)


class DocumentLink(models.Model):
    outgoing_link = models.ForeignKey(Document, related_name="outgoing_link")
    incoming_link = models.ForeignKey(Document, related_name="incoming_link")
    count = models.IntegerField(default=1)
