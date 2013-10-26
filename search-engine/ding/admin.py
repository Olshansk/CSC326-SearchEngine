__author__ = 'Amandeep Grewal'

from django.contrib import admin
from ding.models import Word, Document, WordOccurrence


class WordOccurrenceInline(admin.TabularInline):
    model = WordOccurrence
    extra = 1
    raw_id_fields = ("word",)


class OutgoingLinksInline(admin.TabularInline):
    model = Document.outgoing_links.through
    extra = 1
    fk_name = "from_document"
    raw_id_fields = ("to_document",)
    verbose_name = "Outgoing link"
    verbose_name_plural = "Outgoing links"


class IncomingLinksInline(admin.TabularInline):
    model = Document.outgoing_links.through
    extra = 1
    fk_name = "to_document"
    raw_id_fields = ("from_document",)
    verbose_name = "Incoming link"
    verbose_name_plural = "Incoming links"


class DocumentAdmin(admin.ModelAdmin):
    inlines = (WordOccurrenceInline, OutgoingLinksInline, IncomingLinksInline)
    list_display = ('url', 'id', 'title', 'description', 'visited')
    exclude = ("outgoing_links",)


class WordAdmin(admin.ModelAdmin):
    inlines = (WordOccurrenceInline,)
    list_display = ('text',)


admin.site.register(WordOccurrence)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Word, WordAdmin)