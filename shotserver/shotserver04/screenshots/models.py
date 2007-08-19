# browsershots.org - Test your web design in different browsers
# Copyright (C) 2007 Johann C. Rocholl <johann@browsershots.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA.

"""
Screenshot models.
"""

__revision__ = "$Rev$"
__date__ = "$Date$"
__author__ = "$Author$"

import os
from django.db import models, backend
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from shotserver04.websites.models import Website
from shotserver04.factories.models import Factory
from shotserver04.browsers.models import Browser
from shotserver04.screenshots import storage

PROBLEM_CHOICES = {
    101: _("This is not the requested browser."),
    102: _("This is not the requested operating system."),

    201: _("This is not the requested Javascript version."),
    202: _("This is not the requested Java version."),
    203: _("This is not the requested Flash version."),
    204: _("A language pack needs to be installed."),

    601: _("There is a dialog box in front of the browser window."),
    602: _("The browser window is not maximized."),
    603: _("The page is not finished loading."),
    }

PROBLEM_CHOICES_EXPLICIT = {
    101: _("This is not %(browser)s."),
    102: _("This is not %(operating_system)s."),

    201: _("Javascript is not %(javascript)s."),
    202: _("Java is not %(java)s."),
    203: _("Flash is not %(flash)s."),
    }


class ScreenshotManager(models.Manager):
    """
    Extended database manager for Screenshot model.
    """

    def _quote(self, name):
        """Quote column name, with table name."""
        return '%s.%s' % (
            backend.quote_name(self.model._meta.db_table),
            backend.quote_name(name))

    def recent(self):
        """
        Get recent screenshots, but only one per website.
        """
        from django.db import connection
        cursor = connection.cursor()
        fields = ','.join(
            [self._quote(field.column) for field in self.model._meta.fields])
        cursor.execute("""
            SELECT """ + fields + """
            FROM """ + backend.quote_name(self.model._meta.db_table) + """
            WHERE """ + self._quote('id') + """ IN (
                SELECT MAX(""" + self._quote('id') + """)
                AS """ + backend.quote_name('maximum') + """
                FROM  """ + backend.quote_name(self.model._meta.db_table) + """
                GROUP BY """ + self._quote('website_id') + """
                ORDER BY """ + backend.quote_name('maximum') + """ DESC
                LIMIT 60)
            ORDER BY """ + self._quote('id') + """ DESC
            """)
        for row in cursor.fetchall():
            yield self.model(*row)


class Screenshot(models.Model):
    """
    Uploaded screenshot files.
    """
    hashkey = models.SlugField(
        _('hashkey'), max_length=32, unique=True)
    website = models.ForeignKey(Website,
        verbose_name=_('website'), raw_id_admin=True)
    factory = models.ForeignKey(Factory,
        verbose_name=_('factory'), raw_id_admin=True)
    browser = models.ForeignKey(Browser,
        verbose_name=_('browser'), raw_id_admin=True)
    width = models.IntegerField(
        _('width'))
    height = models.IntegerField(
        _('height'))
    uploaded = models.DateTimeField(
        _('uploaded'), auto_now_add=True)
    objects = ScreenshotManager()

    class Admin:
        fields = (
            (None, {'fields': (
            'hashkey',
            ('website', 'factory', 'browser'),
            ('width', 'height'),
            'uploaded',
            )}),
            )
        list_display = ('hashkey', 'factory', 'browser',
                        'width', 'height', 'uploaded')

    class Meta:
        verbose_name = _('screenshot')
        verbose_name_plural = _('screenshots')
        ordering = ('uploaded', )

    def __unicode__(self):
        return self.hashkey

    def get_absolute_url(self):
        """URL for screenshot detail page."""
        return '/screenshots/%s/' % self.hashkey

    def get_png_url(self, size='original'):
        """URL for screenshot images of different sizes."""
        return '/png/%s/%s/%s.png' % (size, self.hashkey[:2], self.hashkey)

    def get_large_url(self):
        """URL for large preview image."""
        return self.get_png_url(size=512)

    def preview_img(self, width=160, title=None):
        """
        HTML img with screenshot preview.
        """
        height = self.height * width / self.width
        style = 'width:%spx;height:%spx;z-index:0' % (width / 2, height / 2)
        if title is None:
            title = unicode(self.browser)
        return ' '.join((
            u'<img class="preview" style="%s"' % style,
            u'src="%s"' % self.get_png_url(width),
            u'alt="%s" title="%s"' % (title, title),
            u'onmouseover="larger(this,%s,%s)"' % (width, height),
            u'onmouseout="smaller(this,%s,%s)" />' % (width, height),
            ))

    def preview_div(self, width=80, height=None, style="float:left",
                    title=None, caption=None, href=None):
        """
        HTML div with screenshot preview image and link.
        """
        auto_height = self.height * width / self.width
        if height is None:
            height = auto_height
        if caption:
            height += 20
        style = 'width:%dpx;height:%dpx;%s' % (width, height, style)
        href = href or self.get_absolute_url()
        if title is None:
            title = unicode(self.browser)
        lines = ['<div class="preview" style="%s">' % style]
        lines.append(u'<a href="%s">%s</a>' %
            (href, self.preview_img(width=2*width, title=title)))
        if caption is True:
            caption = '<br />'.join((
                unicode(self.browser),
                self.factory.operating_system.
                    __unicode__(show_codename=False)))
        if caption:
            lines.append(
                u'<div class="caption" style="padding-top:%dpx">%s</div>' %
                (auto_height, caption))
        lines.append('</div>')
        return '\n'.join(lines)

    def preview_div_with_browser(self):
        """Shortcut for templates."""
        return self.preview_div(caption=unicode(self.browser))

    def get_file_size(self):
        """Get size in bytes of original screenshot file."""
        return os.path.getsize(storage.png_filename(self.hashkey))

    def arrow(self, screenshot, img, alt):
        """
        HTML link to next or previous screenshot in a group.
        """
        if not screenshot:
            return u'<img src="/static/css/%s-gray.png" alt="%s">' % (img, alt)
        return ''.join((
            u'<a href="%s">' % screenshot.get_absolute_url(),
            u'<img src="/static/css/%s.png" alt="%s">' % (img, alt),
            u'</a>',
            ))

    def get_first(self, **kwargs):
        """Get the first screenshot in a group."""
        return Screenshot.objects.filter(**kwargs).order_by('id')[:1]

    def get_last(self, **kwargs):
        """Get the last screenshot in a group."""
        return Screenshot.objects.filter(**kwargs).order_by('-id')[:1]

    def get_previous(self, **kwargs):
        """Get the previous screenshot in a group."""
        return Screenshot.objects.filter(
            id__lt=self.id, **kwargs).order_by('-id')[:1]

    def get_next(self, **kwargs):
        """Get the next screenshot in a group."""
        return Screenshot.objects.filter(
            id__gt=self.id, **kwargs).order_by('id')[:1]

    def not_me(self, screenshots):
        """
        Try to get the first screenshot from a (possibly empty) list,
        but only if it's different from self.
        """
        if screenshots and screenshots[0] != self:
            return screenshots[0]

    def arrows(self, **kwargs):
        """
        Show links for related screenshots.
        """
        first = self.not_me(self.get_first(**kwargs))
        previous = self.not_me(self.get_previous(**kwargs))
        next = self.not_me(self.get_next(**kwargs))
        last = self.not_me(self.get_last(**kwargs))
        return '\n'.join((
            self.arrow(first, 'first', capfirst(_("first"))),
            self.arrow(previous, 'previous', capfirst(_("previous"))),
            self.arrow(next, 'next', capfirst(_("next"))),
            self.arrow(last, 'last', capfirst(_("last"))),
            ))

    def navigation(self, title, min_count=2, already=0, **kwargs):
        """
        Show arrows to go to first/previous/next/last screenshot.
        """
        total = Screenshot.objects.filter(**kwargs).count()
        if total < min_count or total == already:
            return ''
        index = Screenshot.objects.filter(id__lt=self.id, **kwargs).count() + 1
        index = _(u"%(index)d out of %(total)d") % locals()
        arrows = self.arrows(**kwargs)
        return '\n'.join((
            u'<tr>',
            u'<th>%s</th>' % arrows,
            u'<td>%s %s</td>' % (index, title),
            u'</tr>',
            ))

    def website_navigation(self):
        """
        Navigation links to other screenshots of the same website.
        """
        return self.navigation(
            _("screenshots"),
            min_count=1,
            website=self.website)

    def browser_navigation(self):
        """
        Navigation links for screenshots of the same browser.
        """
        browser_group = self.browser.browser_group
        return self.navigation(
            unicode(_("with %(browser)s")) % {'browser': browser_group.name},
            already=Screenshot.objects.filter(website=self.website).count(),
            website=self.website,
            browser__browser_group=browser_group)

    def platform_navigation(self):
        """
        Navigation links for screenshots of the same platform.
        """
        platform = self.factory.operating_system.platform
        return self.navigation(
            unicode(_("on %(platform)s")) % {'platform': platform.name},
            already=Screenshot.objects.filter(website=self.website).count(),
            website=self.website,
            factory__operating_system__platform=platform)

    def png_filename(self):
        """
        Get user-friendly screenshot filename for use within ZIP files.
        """
        return u' '.join((
            self.uploaded.strftime('%y%m%d-%H%M%S'),
            self.browser.__unicode__(),
            self.factory.operating_system.__unicode__(show_codename=False),
            self.hashkey,
            )).lower().replace(' ', '-') + '.png'


class ProblemReport(models.Model):
    screenshot = models.ForeignKey(Screenshot,
        verbose_name=_("screenshot"), raw_id_admin=True)
    code = models.IntegerField(
        _("error code"))
    message = models.CharField(
        _("error message"), max_length=200)
    reported = models.DateTimeField(
        _("reported"), auto_now_add=True)
    ip = models.IPAddressField(
        _("IP address"))

    class Admin:
        list_display = ('message', 'code', 'reported', 'ip')
        list_filter = ('code', 'ip')
        date_hierarchy = 'reported'

    class Meta:
        verbose_name = _("problem report")
        verbose_name_plural = _("problem reports")
        ordering = ('-reported', )

    def __unicode__(self):
        return unicode(self.get_message_explicit())

    def get_absolute_url(self):
        """Get URL for problem screenshot."""
        return self.screenshot.get_absolute_url()

    def get_message(self):
        """
        Get generic problem message, e.g.
        "This is not the requested browser."
        """
        if self.code in PROBLEM_CHOICES:
            return PROBLEM_CHOICES[self.code]
        else:
            return self.message

    def get_message_explicit(self):
        """
        Get explicit problem message, e.g.
        "This is not Firefox 2.0."
        """
        if self.code in PROBLEM_CHOICES_EXPLICIT:
            message = unicode(PROBLEM_CHOICES_EXPLICIT[self.code])
            if '%(browser)s' in message:
                browser = unicode(self.screenshot.browser)
            if '%(operating_system)s' in message:
                operating_system = unicode(
                    self.screenshot.factory.operating_system)
            if '%(java)s' in message:
                java = unicode(self.screenshot.browser.java)
            if '%(javascript)s' in message:
                javascript = unicode(self.screenshot.browser.javascript)
            if '%(flash)s' in message:
                flash = unicode(self.screenshot.browser.flash)
            return message % locals()
        else:
            return self.get_message()
