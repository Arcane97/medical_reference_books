from django.contrib import admin
from django.db.models import OuterRef, Subquery
from django.forms import BaseInlineFormSet
from django.utils.timezone import localdate

from . import models

admin.site.register(models.ReferenceBookElement)


class ReferenceBookVersionFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = self.queryset.filter(ref_book=self.instance)


class ReferenceBookVersionInline(admin.TabularInline):
    model = models.ReferenceBookVersion
    extra = 0
    formset = ReferenceBookVersionFormSet
    fields = ("version", "date")
    readonly_fields = ("version", "date")
    can_delete = False
    show_change_link = True


@admin.register(models.ReferenceBook)
class ReferenceBookAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "current_version", "version_date")
    list_display_links = ("id", "code", "name")
    inlines = (ReferenceBookVersionInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        current_date = localdate()
        version_queryset = (
            models.ReferenceBookVersion.objects
            .filter(
                ref_book_id=OuterRef('id'),
                date__lte=current_date,
            )
            .order_by('-date')
        )
        current_version = version_queryset.values('version')[:1]
        version_date = version_queryset.values('date')[:1]
        queryset = queryset.annotate(
            current_version=Subquery(current_version),
            version_date=Subquery(version_date),
        )
        return queryset

    @admin.display(description='Текущая версия', empty_value='Нет текущей версии')
    def current_version(self, obj):
        return obj.current_version

    @admin.display(description='Дата начала действия версии', empty_value='Нет текущей версии')
    def version_date(self, obj):
        return obj.version_date


class ReferenceBookElementInline(admin.TabularInline):
    model = models.ReferenceBookElement
    extra = 0


@admin.register(models.ReferenceBookVersion)
class ReferenceBookVersionAdmin(admin.ModelAdmin):
    list_display = ("ref_book__code", "ref_book__name", "version", "date")
    list_display_links = ("version", "date")
    list_select_related = ("ref_book",)
    inlines = (ReferenceBookElementInline,)

    @admin.display(description='Код справочника')
    def ref_book__code(self, obj):
        return obj.ref_book.code

    @admin.display(description='Наименование справочника')
    def ref_book__name(self, obj):
        return obj.ref_book.name
