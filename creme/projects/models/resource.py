# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2015  Hybird
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

from django.conf import settings
from django.db.models import ForeignKey, PositiveIntegerField
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.models import CremeEntity

#from creme.persons.models import Contact

#from .task import ProjectTask

# NB: no AbstractResource because resource should probably not be a CremeEntity at all...
# NB: CremeEntity and not CremeModel because we use a CreatorEntityField in WorkingPeriods' form
class Resource(CremeEntity):
#    linked_contact  = ForeignKey(Contact, verbose_name=_(u'Contact'))
    linked_contact  = ForeignKey(settings.PERSONS_CONTACT_MODEL, verbose_name=_(u'Contact'), editable=False)
    hourly_cost     = PositiveIntegerField(_(u'Hourly cost (in €)'), default=0)
    #task            = ForeignKey(ProjectTask, verbose_name=_(u'Task'),
    task            = ForeignKey(settings.PROJECTS_TASK_MODEL, verbose_name=_(u'Task'),
                                 related_name='resources_set',  # TODO: rename 'resources'
                                 editable=False,
                                )

    creation_label = _('Add a resource')

    class Meta:
        app_label = 'projects'
        verbose_name = _(u'Resource of project')
        verbose_name_plural = _(u'Resources of project')

    def __unicode__(self):
        return unicode(self.linked_contact)

    def get_absolute_url(self):
        return self.linked_contact.get_absolute_url()

    def get_edit_absolute_url(self):
        return "/projects/resource/edit/%s" % self.id

    def get_related_entity(self):
        return self.task

#    def delete(self):
#        # delete first all working period related to this resource (functionnal constraint)
#        WorkingPeriod.objects.filter(task=self.task, resource=self).delete()
#        super(Resource, self).delete()

    def clone_for_task(self, task):
        new_resource = self.clone()
        new_resource.task = task
        new_resource.save()

#from workingperiod import WorkingPeriod
