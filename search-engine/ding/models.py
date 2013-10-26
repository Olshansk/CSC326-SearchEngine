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
    url = models.URLField()
    words = models.ManyToManyField(Word, through='WordOccurrence')
    title = models.TextField()
    description = models.TextField()
    outgoing_links = models.ManyToManyField('self', through='DocumentLink', symmetrical=False)
    visited = models.BooleanField(default=False)

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
