from django.db import models
from django.utils.translation import gettext_lazy as _


class Platform(models.Model):
    name = models.CharField(maxlength=30)
    order = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Admin:
        pass

    class Meta:
        verbose_name = _('platform')
        verbose_name_plural = _('platforms')
        ordering = ('order', 'name')


class OperatingSystem(models.Model):
    platform = models.ForeignKey(Platform)
    name = models.CharField(maxlength=30)
    version = models.CharField(maxlength=30, blank=True)
    codename = models.CharField(maxlength=30, blank=True)
    maker = models.CharField(maxlength=30, blank=True)

    def __str__(self):
        return '%s %s (%s)' % (self.name, self.version, self.codename)

    class Admin:
        list_display = ('platform', 'name', 'version', 'codename', 'maker')
        list_filter = ('platform', )

    class Meta:
        verbose_name = _('operating system')
        verbose_name_plural = _('operating systems')
        ordering = ('name', 'version')


class Architecture(models.Model):
    name = models.CharField(maxlength=30)

    def __str__(self):
        return self.name

    class Admin:
        pass

    class Meta:
        verbose_name = _('architecture')
        verbose_name_plural = _('architectures')
        ordering = ('name', )
