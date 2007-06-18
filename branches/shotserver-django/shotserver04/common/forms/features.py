from django import newforms as forms
from shotserver04.browsers.models import Browser
from shotserver04.features.models import Javascript, Java, Flash
from shotserver04.common import last_poll_timeout
from shotserver04.common import lazy_gettext_capfirst as _


def feature_choices(model):
    """
    Get choices for a feature from the database.
    """
    yield ('dontcare', _("don't care"))
    timeout = last_poll_timeout()
    for version in model.objects.all():
        filters = {'factory__last_poll__gt': timeout}
        if version.version == 'enabled':
            filters[model._meta.module_name + '__id__gte'] = 2
        else:
            filters[model._meta.module_name + '__id'] = version.id
        if not Browser.objects.filter(**filters).count():
            continue
        if version.version == 'disabled':
            yield (version.version, _("disabled"))
        elif version.version == 'enabled':
            yield (version.version, _("enabled"))
        else:
            yield (version.version, version.version)


def feature_or_none(model, value):
    """
    Find feature instance by post value.
    """
    if value == 'dontcare':
        return None
    return model.objects.get(version=value)


class FeaturesForm(forms.Form):
    """
    Request features input form.
    """
    javascript = forms.ChoiceField(
        label=_("Javascript"),
        initial='dontcare',
        choices=feature_choices(Javascript))
    java = forms.ChoiceField(
        label=_("Java"),
        initial='dontcare',
        choices=feature_choices(Java))
    flash = forms.ChoiceField(
        label=_("Flash"),
        initial='dontcare',
        choices=feature_choices(Flash))

    def cleaned_dict(self):
        """
        Get features from their tables.
        """
        return {
            'javascript': feature_or_none(
                Javascript, self.cleaned_data['javascript']),
            'java': feature_or_none(
                Java, self.cleaned_data['java']),
            'flash': feature_or_none(
                Flash, self.cleaned_data['flash']),
            }