from django.db import models

class SearchWord (models.Model):
	word_text = models.CharField(max_length=200)
	word_freq = models.IntegerField(default=0)

	def __unicode__(self):
    		return self.word_text + " count:" + str(self.word_freq)