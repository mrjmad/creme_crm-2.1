# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2018  Hybird
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
from functools import partial

from django.apps import apps
from django.utils.translation import ugettext as _, pgettext

from creme.creme_core import bricks as core_bricks
from creme.creme_core.core.entity_cell import EntityCellRegularField, EntityCellRelation
from creme.creme_core.models import (RelationType, SearchConfigItem, SettingValue,
        BrickDetailviewLocation, BrickHomeLocation, ButtonMenuItem,
        HeaderFilter, EntityFilterCondition, EntityFilter)
from creme.creme_core.management.commands.creme_populate import BasePopulator

from creme import persons, products

from . import get_opportunity_model, bricks, constants
from .buttons import LinkedOpportunityButton
from .models import SalesPhase, Origin
from .setting_keys import quote_key


logger = logging.getLogger(__name__)
Opportunity = get_opportunity_model()


class Populator(BasePopulator):
    dependencies = ['creme_core', 'creme_config', 'persons', 'activities', 'products', 'billing']

    def populate(self):
        already_populated = RelationType.objects.filter(pk=constants.REL_SUB_TARGETS).exists()

        Contact = persons.get_contact_model()
        Organisation = persons.get_organisation_model()
        Product = products.get_product_model()
        Service = products.get_service_model()

        # ---------------------------
        create_rtype = RelationType.create
        rt_sub_targets = create_rtype((constants.REL_SUB_TARGETS, _(u'targets the organisation/contact'), [Opportunity]),
                                      (constants.REL_OBJ_TARGETS, _(u'targeted by the opportunity'),      [Organisation, Contact]),
                                      is_internal=True,
                                      minimal_display=(True, True),
                                     )[0]
        rt_obj_emit_orga = create_rtype((constants.REL_SUB_EMIT_ORGA, _(u'has generated the opportunity'), [Organisation]),
                                        (constants.REL_OBJ_EMIT_ORGA, _(u'has been generated by'),         [Opportunity]),
                                        is_internal=True,
                                        minimal_display=(True, True),
                                       )[1]
        create_rtype((constants.REL_SUB_LINKED_PRODUCT, _(u'is linked to the opportunity'), [Product]),
                     (constants.REL_OBJ_LINKED_PRODUCT, _(u'concerns the product'),         [Opportunity]))
        create_rtype((constants.REL_SUB_LINKED_SERVICE, _(u'is linked to the opportunity'), [Service]),
                     (constants.REL_OBJ_LINKED_SERVICE, _(u'concerns the service'),         [Opportunity]))
        create_rtype((constants.REL_SUB_LINKED_CONTACT, _(u'involves in the opportunity'),  [Contact]),
                     (constants.REL_OBJ_LINKED_CONTACT, _(u'stages'),                       [Opportunity]))
        create_rtype((constants.REL_SUB_RESPONSIBLE,    _(u'is responsible for'),           [Contact]),
                     (constants.REL_OBJ_RESPONSIBLE,    _(u'has as responsible contact'),   [Opportunity]))

        if apps.is_installed('creme.activities'):
            logger.info('Activities app is installed => an Opportunity can be the subject of an Activity')

            from creme.activities.constants import REL_SUB_ACTIVITY_SUBJECT

            RelationType.objects.get(pk=REL_SUB_ACTIVITY_SUBJECT).add_subject_ctypes(Opportunity)

        if apps.is_installed('creme.billing'):
            logger.info('Billing app is installed => we create relationships between Opportunities & billing models')

            from creme.billing import get_invoice_model, get_quote_model, get_sales_order_model

            Invoice    = get_invoice_model()
            Quote      = get_quote_model()
            SalesOrder = get_sales_order_model()

            create_rtype((constants.REL_SUB_LINKED_SALESORDER, _(u'is associate with the opportunity'),     [SalesOrder]),
                         (constants.REL_OBJ_LINKED_SALESORDER, _(u'has generated the salesorder'),          [Opportunity]))
            create_rtype((constants.REL_SUB_LINKED_INVOICE,    _(u'generated for the opportunity'),         [Invoice]),
                         (constants.REL_OBJ_LINKED_INVOICE,    _(u'has resulted in the invoice'),           [Opportunity]))
            create_rtype((constants.REL_SUB_LINKED_QUOTE,      _(u'generated for the opportunity'),         [Quote]),
                         (constants.REL_OBJ_LINKED_QUOTE,      _(u'has resulted in the quote'),             [Opportunity]))
            create_rtype((constants.REL_SUB_CURRENT_DOC,       _(u'is the current accounting document of'), [SalesOrder, Invoice, Quote]),
                         (constants.REL_OBJ_CURRENT_DOC,       _(u'has as current accounting document'),    [Opportunity]))

        # ---------------------------
        SettingValue.objects.get_or_create(key_id=quote_key.id, defaults={'value': False})

        # ---------------------------
        create_efilter = partial(EntityFilter.create, model=Opportunity, user='admin')
        create_cond    = partial(EntityFilterCondition.build_4_field, model=Opportunity)
        create_efilter('opportunities-opportunities_won',
                       name=_(u'Opportunities won'),
                       conditions=[create_cond(operator=EntityFilterCondition.EQUALS,
                                               name='sales_phase__won',
                                               values=[True],
                                              ),
                                  ],
                      )
        create_efilter('opportunities-opportunities_lost',
                       name=_(u'Opportunities lost'),
                       conditions=[create_cond(operator=EntityFilterCondition.EQUALS,
                                               name='sales_phase__lost',
                                               values=[True],
                                              ),
                                  ],
                      )
        create_efilter('opportunities-neither_won_nor_lost_opportunities',
                       name=_(u'Neither won nor lost opportunities'),
                       conditions=[create_cond(operator=EntityFilterCondition.EQUALS_NOT,
                                               name='sales_phase__won',
                                               values=[True],
                                              ),
                                   create_cond(operator=EntityFilterCondition.EQUALS_NOT,
                                               name='sales_phase__lost',
                                               values=[True],
                                              )
                                  ],
                      )

        # ---------------------------
        HeaderFilter.create(pk=constants.DEFAULT_HFILTER_OPPORTUNITY, model=Opportunity,
                            name=_(u'Opportunity view'),
                            cells_desc=[(EntityCellRegularField, {'name': 'name'}),
                                        EntityCellRelation(model=Opportunity, rtype=rt_sub_targets),
                                        (EntityCellRegularField, {'name': 'sales_phase'}),
                                        (EntityCellRegularField, {'name': 'estimated_sales'}),
                                        (EntityCellRegularField, {'name': 'made_sales'}),
                                        (EntityCellRegularField, {'name': 'expected_closing_date'}),
                                       ],
                           )

        # ---------------------------
        SearchConfigItem.create_if_needed(Opportunity, ['name', 'made_sales', 'sales_phase__name', 'origin__name'])

        # ---------------------------
        if not already_populated:
            create_sphase = SalesPhase.objects.create
            create_sphase(name=_(u'Forthcoming'),       order=1)
            create_sphase(name=pgettext('opportunities-sales_phase', u'Abandoned'),   order=4)
            # won  =
            create_sphase(name=pgettext('opportunities-sales_phase', u'Won'),  order=5, won=True)
            # lost =
            create_sphase(name=pgettext('opportunities-sales_phase', u'Lost'), order=6, lost=True)
            create_sphase(name=_(u'Under negotiation'), order=3)
            create_sphase(name=_(u'In progress'),       order=2)

            # ---------------------------
            create_origin = Origin.objects.create
            create_origin(name=pgettext('opportunities-origin', u'None'))
            create_origin(name=_(u'Web site'))
            create_origin(name=_(u'Mouth'))
            create_origin(name=_(u'Show'))
            create_origin(name=_(u'Direct email'))
            create_origin(name=_(u'Direct phone call'))
            create_origin(name=_(u'Employee'))
            create_origin(name=_(u'Partner'))
            create_origin(name=pgettext('opportunities-origin', u'Other'))

            # ---------------------------
            create_button = ButtonMenuItem.create_if_needed
            create_button(pk='opportunities-linked_opp_button',         model=Organisation, button=LinkedOpportunityButton, order=30)  # TODO: This pk is kept for compatibility
            create_button(pk='opportunities-linked_opp_button_contact', model=Contact,      button=LinkedOpportunityButton, order=30)

            # ---------------------------
            create_bdl = BrickDetailviewLocation.create_if_needed
            LEFT = BrickDetailviewLocation.LEFT
            RIGHT = BrickDetailviewLocation.RIGHT

            create_bdl(brick_id=bricks.OpportunityCardHatBrick.id_, order=1, zone=BrickDetailviewLocation.HAT, model=Opportunity)
            create_bdl(brick_id=core_bricks.CustomFieldsBrick.id_,  order=40,  zone=LEFT,  model=Opportunity)
            create_bdl(brick_id=bricks.BusinessManagersBrick.id_,   order=60,  zone=LEFT,  model=Opportunity)
            create_bdl(brick_id=bricks.LinkedContactsBrick.id_,     order=62,  zone=LEFT,  model=Opportunity)
            create_bdl(brick_id=bricks.LinkedProductsBrick.id_,     order=64,  zone=LEFT,  model=Opportunity)
            create_bdl(brick_id=bricks.LinkedServicesBrick.id_,     order=66,  zone=LEFT,  model=Opportunity)
            create_bdl(brick_id=core_bricks.PropertiesBrick.id_,    order=450, zone=LEFT,  model=Opportunity)
            create_bdl(brick_id=core_bricks.RelationsBrick.id_,     order=500, zone=LEFT,  model=Opportunity)
            create_bdl(brick_id=bricks.OppTargetBrick.id_,          order=1,   zone=RIGHT, model=Opportunity)
            create_bdl(brick_id=bricks.OppTotalBrick.id_,           order=2,   zone=RIGHT, model=Opportunity)
            create_bdl(brick_id=core_bricks.HistoryBrick.id_,       order=20,  zone=RIGHT, model=Opportunity)

            if apps.is_installed('creme.activities'):
                logger.info('Activities app is installed => we use the "Future activities" & "Past activities" blocks')

                from creme.activities import bricks as act_bricks

                create_bdl(brick_id=act_bricks.FutureActivitiesBrick.id_, order=20, zone=RIGHT, model=Opportunity)
                create_bdl(brick_id=act_bricks.PastActivitiesBrick.id_,   order=21, zone=RIGHT, model=Opportunity)
                # BlockPortalLocation.create_or_update(app_name='opportunities', brick_id=act_bricks.FutureActivitiesBrick.id_, order=20)
                # BlockPortalLocation.create_or_update(app_name='opportunities', brick_id=act_bricks.PastActivitiesBrick.id_,   order=21)

            if apps.is_installed('creme.assistants'):
                logger.info('Assistants app is installed => we use the assistants blocks on detail views and portal')

                from creme.assistants import bricks as assistants_bricks

                create_bdl(brick_id=assistants_bricks.TodosBrick.id_,        order=100, zone=RIGHT, model=Opportunity)
                create_bdl(brick_id=assistants_bricks.MemosBrick.id_,        order=200, zone=RIGHT, model=Opportunity)
                create_bdl(brick_id=assistants_bricks.AlertsBrick.id_,       order=300, zone=RIGHT, model=Opportunity)
                create_bdl(brick_id=assistants_bricks.UserMessagesBrick.id_, order=500, zone=RIGHT, model=Opportunity)

                # BlockPortalLocation.create_or_update(app_name='opportunities', brick_id=assistants_bricks.MemosBrick.id_,        order=100)
                # BlockPortalLocation.create_or_update(app_name='opportunities', brick_id=assistants_bricks.AlertsBrick.id_,       order=200)
                # BlockPortalLocation.create_or_update(app_name='opportunities', brick_id=assistants_bricks.UserMessagesBrick.id_, order=400)

            if apps.is_installed('creme.documents'):
                # logger.info('Documents app is installed => we use the documents block on detail view')

                from creme.documents.bricks import LinkedDocsBrick

                create_bdl(brick_id=LinkedDocsBrick.id_, order=600, zone=RIGHT, model=Opportunity)

            if apps.is_installed('creme.billing'):
                logger.info('Billing app is installed => we use the billing blocks on detail view')

                create_bdl(brick_id=bricks.QuotesBrick.id_,      order=70, zone=LEFT, model=Opportunity)
                create_bdl(brick_id=bricks.SalesOrdersBrick.id_, order=72, zone=LEFT, model=Opportunity)
                create_bdl(brick_id=bricks.InvoicesBrick.id_,    order=74, zone=LEFT, model=Opportunity)

            if apps.is_installed('creme.emails'):
                logger.info('Emails app is installed => we use the emails blocks on detail view')

                from creme.emails.bricks import MailsHistoryBrick

                create_bdl(brick_id=MailsHistoryBrick.id_, order=600, zone=RIGHT, model=Opportunity)

            create_bdl(brick_id=bricks.TargettingOpportunitiesBrick.id_, order=16, zone=RIGHT, model=Organisation)

            # ---------------------------
            if apps.is_installed('creme.reports'):
                logger.info('Reports app is installed => we create an Opportunity report, with 2 graphs, and related blocks')
                self.create_report_n_graphes(rt_obj_emit_orga)

    def create_report_n_graphes(self, rt_obj_emit_orga):
        "Create the report 'Opportunities' and 2 ReportGraphs"
        from django.contrib.auth import get_user_model
        from django.contrib.contenttypes.models import ContentType

        from creme.creme_core.utils.meta import FieldInfo

        from creme.reports import constants as rep_constants
        from creme.reports.models import Report, Field, ReportGraph

        admin = get_user_model().objects.get_admin()

        # Create the report ----------------------------------------------------
        report = Report.objects.create(name=_(u'Opportunities'), user=admin,
                                       ct=ContentType.objects.get_for_model(Opportunity),
                                      )

        # TODO: helper method(s) (see EntityFilterCondition)
        create_field = partial(Field.objects.create, report=report, type=rep_constants.RFT_FIELD)
        create_field(name='name',              order=1)
        create_field(name='estimated_sales',   order=2)
        create_field(name='made_sales',        order=3)
        create_field(name='sales_phase__name', order=4)
        create_field(name=rt_obj_emit_orga.id, order=5, type=rep_constants.RFT_RELATION)

        # Create 2 graphs -----------------------------------------------------
        # TODO: helper method ('sum' => is_count=False, range only on DateFields etc...)
        # create_graph = partial(ReportGraph.objects.create, report=report, user=admin,
        create_graph = partial(ReportGraph.objects.create, linked_report=report, user=admin,
                               is_count=False, ordinate='estimated_sales__sum',
                              )
        esales_vname = FieldInfo(Opportunity, 'estimated_sales').verbose_name
        rgraph1 = create_graph(name=_(u'Sum {estimated_sales} / {sales_phase}').format(
                                    estimated_sales=esales_vname,
                                    sales_phase=FieldInfo(Opportunity, 'sales_phase').verbose_name,
                                ),
                               abscissa='sales_phase', type=rep_constants.RGT_FK,
                              )
        rgraph2 = create_graph(name=_(u'Sum {estimated_sales} / Quarter (90 days on {closing_date})').format(
                                    estimated_sales=esales_vname,
                                    closing_date=FieldInfo(Opportunity, 'closing_date').verbose_name,
                                ),
                               abscissa='closing_date', type=rep_constants.RGT_RANGE, days=90,
                              )

        # Create 2 instance block items for the 2 graphs ----------------------
        # brick_id1 = rgraph1.create_instance_block_config_item().brick_id
        # brick_id2 = rgraph2.create_instance_block_config_item().brick_id
        brick_id1 = rgraph1.create_instance_brick_config_item().brick_id
        brick_id2 = rgraph2.create_instance_brick_config_item().brick_id

        BrickDetailviewLocation.create_if_needed(brick_id=brick_id1, order=4, zone=BrickDetailviewLocation.RIGHT, model=Opportunity)
        BrickDetailviewLocation.create_if_needed(brick_id=brick_id2, order=6, zone=BrickDetailviewLocation.RIGHT, model=Opportunity)
        # BlockPortalLocation.create_or_update(app_name='opportunities', brick_id=brick_id1, order=1)
        # BlockPortalLocation.create_or_update(app_name='opportunities', brick_id=brick_id2, order=2)

        # BlockPortalLocation.create_or_update(app_name='creme_core', brick_id=brick_id1, order=5)
        # BlockPortalLocation.create_or_update(app_name='creme_core', brick_id=brick_id2, order=6)
        BrickHomeLocation.objects.create(brick_id=brick_id1, order=5)
        BrickHomeLocation.objects.create(brick_id=brick_id2, order=6)