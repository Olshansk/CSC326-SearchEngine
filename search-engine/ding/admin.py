__author__ = 'Amandeep Grewal'

from django.contrib import admin
from ding.models import Word, Document, WordOccurrence


class WordOccurrenceInline(admin.TabularInline):
    model = WordOccurrence
    extra = 1
    raw_id_fields = ("word",)


class DocumentAdmin(admin.ModelAdmin):
    inlines = (WordOccurrenceInline,)
    list_display = ('url', 'title', 'description')


class WordAdmin(admin.ModelAdmin):
    inlines = (WordOccurrenceInline,)
    list_display = ('text',)


admin.site.register(WordOccurrence)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Word, WordAdmin)