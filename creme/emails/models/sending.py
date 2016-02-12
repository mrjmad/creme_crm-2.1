# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2016  Hybird
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

import logging
from pickle import loads
from time import sleep
# import warnings

from django.conf import settings
from django.core.mail import send_mail, get_connection
from django.db import IntegrityError
from django.db.models import (ForeignKey, DateTimeField, PositiveSmallIntegerField,
        EmailField, CharField, TextField, ManyToManyField, SET_NULL)
from django.db.transaction import atomic
from django.template import Template, Context
from django.utils.translation import ugettext_lazy as _, ugettext, pgettext_lazy  # activate

from creme.creme_core.models import CremeModel, CremeEntity

from ..constants import MAIL_STATUS_NOTSENT, MAIL_STATUS_SENDINGERROR
from ..utils import generate_id, EMailSender, ImageFromHTMLError
from .mail import _Email, ID_LENGTH
from .signature import EmailSignature


logger = logging.getLogger(__name__)

# TODO: move to constants.py ???
SENDING_TYPE_IMMEDIATE = 1
SENDING_TYPE_DEFERRED  = 2

SENDING_TYPES = {
                    SENDING_TYPE_IMMEDIATE: _(u"Immediate"),
                    SENDING_TYPE_DEFERRED:  pgettext_lazy('emails-sending', u'Deferred'),
                }

SENDING_STATE_DONE       = 1
SENDING_STATE_INPROGRESS = 2
SENDING_STATE_PLANNED    = 3
SENDING_STATE_ERROR      = 4

SENDING_STATES = {
                    SENDING_STATE_DONE:       pgettext_lazy('emails-sending', u'Done'),
                    SENDING_STATE_INPROGRESS: _(u"In progress"),
                    SENDING_STATE_PLANNED:    pgettext_lazy('emails-sending', u'Planned'),
                    SENDING_STATE_ERROR:      _(u"Error during sending"),
                 }


class EmailSending(CremeModel):
    sender        = EmailField(_(u"Sender address"), max_length=100)
    campaign      = ForeignKey(settings.EMAILS_CAMPAIGN_MODEL,
                               verbose_name=pgettext_lazy('emails', u'Related campaign'),
                               related_name='sendings_set', editable=False,
                              )
    type          = PositiveSmallIntegerField(verbose_name=_(u"Sending type"),
                                              choices=SENDING_TYPES.items(),
                                              default=SENDING_TYPE_IMMEDIATE,
                                             )
    sending_date  = DateTimeField(_(u"Sending date of emails"))
    state         = PositiveSmallIntegerField(verbose_name=_(u"Sending state"),
                                              editable=False,
                                              choices=SENDING_STATES.items(),
                                              default=SENDING_STATE_PLANNED,
                                             )

    subject     = CharField(_(u'Subject'), max_length=100, editable=False)
    body        = TextField(_(u"Body"), editable=False)
    body_html   = TextField(_(u"Body (HTML)"), null=True, blank=True, editable=False)
    signature   = ForeignKey(EmailSignature, verbose_name=_(u'Signature'),
                             blank=True, null=True, editable=False, on_delete=SET_NULL,
                            )
    attachments = ManyToManyField(settings.DOCUMENTS_DOCUMENT_MODEL,
                                  verbose_name=_(u'Attachments'), editable=False,
                                 )

    class Meta:
        app_label = "emails"
        verbose_name = _(u'Email campaign sending')
        verbose_name_plural = _(u'Email campaign sendings')

    def __unicode__(self):
        return ugettext(u"Sending of «%(campaign)s» on %(date)s") % {
                            'campaign': self.campaign,
                            'date':     self.sending_date,
                        }

    def get_mails(self):
        return self.mails_set.all()

    def get_unsent_mails_count(self):
        return self.mails_set.filter(status__in=[MAIL_STATUS_NOTSENT, MAIL_STATUS_SENDINGERROR]).count()

    # def get_state_str(self):
    #     warnings.warn("EmailSending.get_state_str() method is deprecated ; use get_state_display() instead.",
    #                   DeprecationWarning
    #                  )
    #
    #     return SENDING_STATES[self.state]

    # def get_type_str(self):
    #     warnings.warn("EmailSending.get_type_str() method is deprecated ; use get_type_display() instead.",
    #                   DeprecationWarning
    #                  )
    #
    #     return SENDING_TYPES[self.type]

    def get_absolute_url(self):
        return self.campaign.get_absolute_url()

    def get_related_entity(self):  # For generic views
        return self.campaign

    def send_mails(self):
        try:
            sender = LightWeightEmailSender(sending=self)
        except ImageFromHTMLError as e:
            # activate(settings.LANGUAGE_CODE)
            send_mail(ugettext('[CremeCRM] Campaign email sending error.'),
                      ugettext("Emails in the sending of the campaign «%(campaign)s» on %(date)s weren't sent "
                               "because the image «%(image)s» is no longer available in the template.") % {
                            'campaign': self.campaign,
                            'date':     self.sending_date,
                            'image':    e.filename,
                        },
                      settings.EMAIL_HOST_USER,
                      [self.campaign.user.email or settings.DEFAULT_USER_EMAIL],
                      fail_silently=False,
                     )

            return SENDING_STATE_ERROR

        connection = get_connection(host=settings.EMAILCAMPAIGN_HOST,
                                    port=settings.EMAILCAMPAIGN_PORT,
                                    username=settings.EMAILCAMPAIGN_HOST_USER,
                                    password=settings.EMAILCAMPAIGN_PASSWORD,
                                    use_tls=settings.EMAILCAMPAIGN_USE_TLS,
                                   )

        mails_count   = 0
        one_mail_sent = False
        SENDING_SIZE  = getattr(settings, 'EMAILCAMPAIGN_SIZE', 40)
        SLEEP_TIME    = getattr(settings, 'EMAILCAMPAIGN_SLEEP_TIME', 2)

        for mail in LightWeightEmail.objects.filter(sending=self):
            if sender.send(mail, connection=connection):
                mails_count += 1
                one_mail_sent = True
                logger.debug("Mail sent to %s", mail.recipient)

            if mails_count > SENDING_SIZE:
                logger.debug('Sending: waiting timeout')

                mails_count = 0
                sleep(SLEEP_TIME)  # Avoiding the mail to be classed as spam

        if not one_mail_sent:
            return SENDING_STATE_ERROR

        # TODO: close the connection ??


class LightWeightEmail(_Email):
    """Used by campaigns.
    id is a unique generated string in order to avoid stats hacking.
    """
    id               = CharField(_(u'Email ID'), primary_key=True, max_length=ID_LENGTH, editable=False)
    sending          = ForeignKey(EmailSending, verbose_name=_(u"Related sending"),
                                  related_name='mails_set', editable=False,
                                 )
    recipient_entity = ForeignKey(CremeEntity, null=True, related_name='received_lw_mails', editable=False)

    class Meta:
        app_label = "emails"
        verbose_name = _(u'Email of campaign')
        verbose_name_plural = _(u'Emails of campaign')

    def _render_body(self, sending_body):
        body = self.body

        try:
            return Template(sending_body).render(Context(loads(body.encode('utf-8')) if body else {}))
        except Exception as e:  # Pickle raises too much different exceptions... Catch'em all ?
            logger.debug('Error in LightWeightEmail._render_body(): %s', e)
            return ""

    # def get_body(self):
    #     warnings.warn("LightWeightEmail.get_body() method is deprecated ; use 'rendered_body' instead",
    #                   DeprecationWarning
    #                  )
    #
    #     # return self._render_body(self.sending.body)
    #     return self.rendered_body

    # def get_body_html(self):
    #     warnings.warn("LightWeightEmail.get_body_html() method is deprecated ; use 'rendered_body_html' instead",
    #                   DeprecationWarning
    #                  )
    #
    #     # return self._render_body(self.sending.body_html)
    #     return self.rendered_body_html

    @property
    def rendered_body(self):
        return self._render_body(self.sending.body)

    @property
    def rendered_body_html(self):
        return self._render_body(self.sending.body_html)

    def get_related_entity(self):  # For generic views
        return self.sending.campaign

    def genid_n_save(self):
        while True:
            self.id = generate_id()

            try:
                with atomic():
                    self.save(force_insert=True)
            except IntegrityError:  # A mail with this id already exists
                logger.debug('Mail id already exists: %s', self.id)
                self.pk = None
            else:
                return


class LightWeightEmailSender(EMailSender):
    def __init__(self, sending):
        super(LightWeightEmailSender, self).__init__(body=sending.body,
                                                     body_html=sending.body_html,
                                                     signature=sending.signature,
                                                     attachments=sending.attachments.all(),
                                                    )
        self._sending = sending
        self._body_template = Template(self._body)
        self._body_html_template = Template(self._body_html)

    def get_subject(self, mail):
        return self._sending.subject

    def _process_bodies(self, mail):
        body = mail.body
        context = Context(loads(body.encode('utf-8')) if body else {})

        return self._body_template.render(context), self._body_html_template.render(context)
