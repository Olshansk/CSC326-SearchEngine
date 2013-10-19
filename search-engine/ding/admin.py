__author__ = 'Amandeep Grewal'

from django.contrib import admin
from ding.models import Word, Document, WordOnPage


class WordOnPageInline(admin.TabularInline):
    model = WordOnPage
    extra = 1


class DocumentAdmin(admin.ModelAdmin):
    inlines = (WordOnPageInline,)


class WordAdmin(admin.ModelAdmin):
    inlines = (WordOnPageInline,)


admin.site.register(WordOnPage)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Word, WordAdmin)