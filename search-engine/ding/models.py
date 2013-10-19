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
    words = models.ManyToManyField(Word, through='WordOnPage')
    title = models.TextField()
    description = models.TextField()

    def __unicode__(self):
        return self.url


class WordOnPage(models.Model):
    word = models.ForeignKey(Word)
    document = models.ForeignKey(Document)
    font_size = models.IntegerField()
