__author__ = 'Amandeep Grewal'

from django.contrib import admin
from ding.models import Word, Document, WordOccurrence, DocumentLink


class WordOccurrenceInline(admin.TabularInline):
    model = WordOccurrence
    extra = 1
    raw_id_fields = ("word", "document")


class OutgoingLinksInline(admin.TabularInline):
    model = DocumentLink
    extra = 1
    fk_name = "outgoing_link"
    raw_id_fields = ("incoming_link", "outgoing_link")
    verbose_name = "Outgoing link"
    verbose_name_plural = "Outgoing links"


class IncomingLinksInline(admin.TabularInline):
    model = DocumentLink
    extra = 1
    fk_name = "incoming_link"
    raw_id_fields = ("outgoing_link", "incoming_link")
    verbose_name = "Incoming link"
    verbose_name_plural = "Incoming links"


class DocumentAdmin(admin.ModelAdmin):
    inlines = (WordOccurrenceInline, OutgoingLinksInline, IncomingLinksInline)
    list_display = ('url', 'id', 'title', 'description', 'visited')


class WordAdmin(admin.ModelAdmin):
    inlines = (WordOccurrenceInline,)
    list_display = ('text',)


admin.site.register(WordOccurrence)
admin.site.register(DocumentLink)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Word, WordAdmin)
