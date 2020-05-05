from traceback import format_exc

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db import models
from django.core.mail import send_mail
from django.conf import settings


class CoreModel(models.Model):
    created = models.DateTimeField(
        'Created',
        editable=False,
        null=False,
        blank=False,
    )

    updated = models.DateTimeField(
        'Updated',
        editable=False,
        null=False,
        blank=False,
    )

    def save(self, *args, **kwargs):
        if self.created is None:
            self.created = timezone.now()
        self.updated = timezone.now()
        return super(CoreModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True
        ordering = ['updated']


class Mail(CoreModel):
    subject = models.CharField(_('Subject'), max_length=250, blank=True)
    to_address = models.TextField(_('To'))
    cc_address = models.TextField(_('CC'), blank=True)
    bcc_address = models.TextField(_('BCC'), blank=True)
    from_address = models.EmailField(_('From'), max_length=250)
    content = models.TextField(_('Content'), blank=True)
    html_content = models.TextField(_('HTML Content'), blank=True)

    errors = models.TextField(_('Errors'), blank=True, default='')
    sent = models.DateTimeField(blank=True, null=True)

    def send(self):
        try:
            send_mail(
                self.subject,
                self.content,
                self.from_address,
                [self.to_address],
                fail_silently=False,
            )
            self.sent = timezone.now()
        except: # noqa
            self.errors = format_exc()

        self.save()


class Event(CoreModel):
    type = models.CharField(_('Type'), max_length=256, blank=False, null=False)
    related_user = models.ForeignKey(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        null=True,
        blank=True,
        related_name='events',
        on_delete=models.CASCADE,
    )
    meta = models.TextField(blank=True, null=False, default='')
