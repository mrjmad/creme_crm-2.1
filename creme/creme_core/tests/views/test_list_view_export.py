# -*- coding: utf-8 -*-

try:
    from datetime import date
    from functools import partial
    from unittest import skipIf

#    from django.apps import apps
    from django.conf import settings
    from django.contrib.contenttypes.models import ContentType
    from django.utils.encoding import force_unicode
    from django.utils.formats import date_format
    from django.utils.timezone import localtime
    from django.utils.translation import ugettext as _

    from .base import ViewsTestCase
    from ..fake_constants import FAKE_PERCENT_UNIT, FAKE_AMOUNT_UNIT
    from ..fake_models import (FakeContact as Contact,
            FakeOrganisation as Organisation, FakeImage as Image,
            FakeEmailCampaign as EmailCampaign, FakeMailingList as MailingList,
            FakeInvoice, FakeInvoiceLine)
    from creme.creme_core.core.entity_cell import (EntityCellRegularField,
            EntityCellFunctionField, EntityCellRelation)
    from creme.creme_core.models import (RelationType, Relation, FieldsConfig,
            CremePropertyType, CremeProperty, HeaderFilter)
#    from creme.creme_core.tests.base import skipIfNotInstalled

#    from creme.media_managers.models import Image

#    from creme.persons.models import Contact, Organisation
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))

try:
    from creme.creme_core.utils.xlrd_utils import XlrdReader
    from creme.creme_core.registry import export_backend_registry
    XlsMissing = 'xls' not in export_backend_registry.iterkeys()
except Exception:
    XlsMissing = True


class CSVExportViewsTestCase(ViewsTestCase):
    @classmethod
    def setUpClass(cls):
        ViewsTestCase.setUpClass()
#        apps = ['creme_core', 'persons']
#        if 'creme.billing' in settings.INSTALLED_APPS:
#            apps.append('billing')
#
#        cls.populate(*apps)
        cls.populate('creme_core')
        cls.ct = ContentType.objects.get_for_model(Contact)

        cls._hf_backup = list(HeaderFilter.objects.all())
        HeaderFilter.objects.all().delete()

    @classmethod
    def tearDownClass(cls):
        ViewsTestCase.tearDownClass()
        HeaderFilter.objects.all().delete()
        HeaderFilter.objects.bulk_create(cls._hf_backup)

    def _build_hf_n_contacts(self):
        user = self.user

        create_orga = partial(Organisation.objects.create, user=user)
        self.organisations = organisations = {
                name: create_orga(name=name)
                    for name in ('Bebop', 'Swordfish')
            }

        rtype_pilots = RelationType.create(('test-subject_pilots', 'pilots'),
                                           ('test-object_pilots',  'is piloted by')
                                          )[0]

        create_ptype = CremePropertyType.create
        ptype_beautiful = create_ptype(str_pk='test-prop_beautiful', text='is beautiful')
        ptype_girl      = create_ptype(str_pk='test-prop_girl',      text='is a girl')

        create_contact = partial(Contact.objects.create, user=user)
        self.contacts = contacts = {
                first_name: create_contact(first_name=first_name, last_name=last_name)
                        for first_name, last_name in [('Spike', 'Spiegel'),
                                                      ('Jet', 'Black'),
                                                      ('Faye', 'Valentine'),
                                                      ('Edward', 'Wong'),
                                                     ]
            }

        create_rel = partial(Relation.objects.create, user=user, type=rtype_pilots,
                             object_entity=organisations['Bebop']
                            )
        create_rel(subject_entity=contacts['Jet'])
        create_rel(subject_entity=contacts['Spike'])
        create_rel(subject_entity=contacts['Spike'], object_entity=organisations['Swordfish'])

        create_prop = CremeProperty.objects.create
        create_prop(type=ptype_girl,      creme_entity=contacts['Faye'])
        create_prop(type=ptype_girl,      creme_entity=contacts['Edward'])
        create_prop(type=ptype_beautiful, creme_entity=contacts['Faye'])

        cells = [EntityCellRegularField.build(model=Contact, name='civility'),
                 EntityCellRegularField.build(model=Contact, name='last_name'),
                 EntityCellRegularField.build(model=Contact, name='first_name'),
                 EntityCellRelation(rtype=rtype_pilots),
                 #TODO: EntityCellCustomField
                 EntityCellFunctionField(func_field=Contact.function_fields.get('get_pretty_properties')),
                ]
        HeaderFilter.create(pk='test-hf_contact', name='Contact view',
                            model=Contact, cells_desc=cells,
                           )

        return cells

    def _build_url(self, ct, method='download', doc_type='csv'):
        return '/creme_core/list_view/%s/%s/%s' % (method, ct.id, doc_type)

    def _set_listview_state(self, model=Contact):
        lv_url = model.get_lv_absolute_url()
        self.assertGET200(lv_url) #set the current list view state...

        return lv_url

    def test_export_error01(self):
        "Assert doc_type in ('xls', 'csv')"
        self.login()
        lv_url = self._set_listview_state()

        self.assertGET404(self._build_url(self.ct, doc_type='exe'), data={'list_url': lv_url})

    def test_list_view_export_header(self):
        self.login()
        cells = self._build_hf_n_contacts()
        lv_url = self._set_listview_state()
        url = self._build_url(self.ct, method='download_header')
        response = self.assertGET200(url, data={'list_url': lv_url})

        self.assertEqual([u','.join(u'"%s"' % hfi.title for hfi in cells)],
                         [force_unicode(line) for line in response.content.splitlines()]
                        )

    @skipIf(XlsMissing, "Skip tests, couldn't find xlwt or xlrd libs")
    def test_xls_export_header(self):
        self.login()
        cells = self._build_hf_n_contacts()
        lv_url = self._set_listview_state()

        response = self.assertGET200(self._build_url(self.ct, method='download_header', doc_type='xls'),
                                     data={'list_url': lv_url}, follow=True
                                    )

        result = list(XlrdReader(None, file_contents=response.content))
        self.assertEqual(1, len(result))
        self.assertEqual(result[0], [hfi.title for hfi in cells])

    def test_list_view_export01(self):
        "csv"
        self.login()
        cells = self._build_hf_n_contacts()
        lv_url = self._set_listview_state()

        response = self.assertGET200(self._build_url(self.ct), data={'list_url': lv_url})

        #TODO: sort the relations/properties by they verbose_name ??
        it = (force_unicode(line) for line in response.content.splitlines())
        self.assertEqual(it.next(), u','.join(u'"%s"' % hfi.title for hfi in cells))
        self.assertEqual(it.next(), u'"","Black","Jet","Bebop",""')
#        self.assertEqual(it.next(), u'"","Bouquet","Mireille","",""')
#        self.assertEqual(it.next(), u'"","Creme","Fulbert","",""')
        self.assertIn(it.next(), (u'"","Spiegel","Spike","Bebop/Swordfish",""',
                                  u'"","Spiegel","Spike","Swordfish/Bebop",""')
                     )
        self.assertIn(it.next(), (u'"","Valentine","Faye","","is a girl/is beautiful"',
                                  u'"","Valentine","Faye","","is beautiful/is a girl"')
                     )
        self.assertEqual(it.next(), u'"","Wong","Edward","","is a girl"')
#        self.assertEqual(it.next(), u'"","Yumura","Kirika","",""')
        self.assertRaises(StopIteration, it.next)

    def test_list_view_export02(self):
        "scsv"
        self.login()
        cells = self._build_hf_n_contacts()
        lv_url = self._set_listview_state()

        response = self.assertGET200(self._build_url(self.ct, doc_type='scsv'), data={'list_url': lv_url})

        #TODO: sort the relations/properties by they verbose_name ??
        it = (force_unicode(line) for line in response.content.splitlines())
        self.assertEqual(it.next(), u';'.join(u'"%s"' % hfi.title for hfi in cells))
        self.assertEqual(it.next(), u'"";"Black";"Jet";"Bebop";""')
#        self.assertEqual(it.next(), u'"";"Bouquet";"Mireille";"";""')
#        self.assertEqual(it.next(), u'"";"Creme";"Fulbert";"";""')
        self.assertIn(it.next(), (u'"";"Spiegel";"Spike";"Bebop/Swordfish";""',
                                  u'"";"Spiegel";"Spike";"Swordfish/Bebop";""')
                     )
        self.assertIn(it.next(), (u'"";"Valentine";"Faye";"";"is a girl/is beautiful"',
                                  u'"";"Valentine";"Faye";"";"is beautiful/is a girl"')
                     )
        self.assertEqual(it.next(), u'"";"Wong";"Edward";"";"is a girl"')
#        self.assertEqual(it.next(), u'"";"Yumura";"Kirika";"";""')
        self.assertRaises(StopIteration, it.next)

    def test_list_view_export03(self):
        "'export' credential"
#        self.login(is_superuser=False, allowed_apps=['creme_core', 'persons'])
        self.login(is_superuser=False)
        self._build_hf_n_contacts()
        url = self._build_url(self.ct)
        data = {'list_url': self._set_listview_state()}
        self.assertGET403(url, data=data)

        self.role.exportable_ctypes = [self.ct] # set the 'export' credentials
        self.assertGET200(url, data=data)

    def test_list_view_export04(self):
        "Credential"
#        user = self.login(is_superuser=False, allowed_apps=['creme_core', 'persons'])
        user = self.login(is_superuser=False)
        self.role.exportable_ctypes = [self.ct]

        self._build_hf_n_contacts()

        contacts = self.contacts
        faye = contacts['Faye']
        faye.user = self.other_user
        faye.save()
        self.assertFalse(user.has_perm_to_view(faye))
        self.assertTrue(user.has_perm_to_view(contacts['Spike']))

        organisations = self.organisations
        bebop = organisations['Bebop']
        bebop.user = self.other_user
        bebop.save()
        self.assertFalse(user.has_perm_to_view(bebop))
        self.assertTrue(user.has_perm_to_view(organisations['Swordfish']))

        response = self.assertGET200(self._build_url(self.ct),
                                     data={'list_url': self._set_listview_state()}
                                    )
        result = map(force_unicode, response.content.splitlines())
        #self.assertEqual(6, len(result)) #Fulbert & Kirika are not viewable
        self.assertEqual(result[1], '"","Black","Jet","",""')
#        self.assertEqual(result[2], '"","Bouquet","Mireille","",""')
#        self.assertEqual(result[3], '"","Spiegel","Spike","Swordfish",""')
        self.assertEqual(result[2], '"","Spiegel","Spike","Swordfish",""')
        self.assertEqual(result[3], u'"","Wong","Edward","","is a girl"')

    def test_list_view_export05(self):
        "Datetime field"
        user = self.login()

        HeaderFilter.create(pk='test-hf_contact', name='Contact view', model=Contact,
                            cells_desc=[(EntityCellRegularField, {'name': 'last_name'}),
                                        (EntityCellRegularField, {'name': 'created'}),
                                       ],
                           )

        spike = Contact.objects.create(user=user, first_name='Spike', last_name='Spiegel')

        lv_url = self._set_listview_state()
        response = self.assertGET200(self._build_url(self.ct), data={'list_url': lv_url})

        result = [force_unicode(line) for line in response.content.splitlines()]
#        self.assertEqual(4, len(result))
#
#        mireille = self.other_user.linked_contact
#        self.assertEqual(result[1],
#                         u'"%s","%s"' % (mireille.last_name,
#                                         date_format(localtime(mireille.created), 'DATETIME_FORMAT'),
#                                        )
#                        )
        self.assertEqual(2, len(result))
        self.assertEqual(result[1],
                         u'"%s","%s"' % (spike.last_name,
                                         date_format(localtime(spike.created), 'DATETIME_FORMAT'),
                                       )
                        )

    def test_list_view_export06(self):
        "FK field on CremeEntity"
#        user = self.login(is_superuser=False, allowed_apps=['creme_core', 'persons', 'media_managers'])
        user = self.login(is_superuser=False)
        self.role.exportable_ctypes = [self.ct]

        create_img = Image.objects.create
        spike_face = create_img(name='Spike face', user=self.other_user, description="Spike's selfie")
        jet_face   = create_img(name='Jet face',   user=user,            description="Jet's selfie")
        self.assertTrue(user.has_perm_to_view(jet_face))
        self.assertFalse(user.has_perm_to_view(spike_face))

        create_contact = partial(Contact.objects.create, user=user)
        create_contact(first_name='Spike', last_name='Spiegel', image=spike_face)
        create_contact(first_name='Jet',   last_name='Black',   image=jet_face)
        create_contact(first_name='Faye',  last_name='Valentine')

        HeaderFilter.create(pk='test-hf_contact', name='Contact view', model=Contact,
                            cells_desc=[(EntityCellRegularField, {'name': 'last_name'}),
                                        (EntityCellRegularField, {'name': 'image'}),
                                        (EntityCellRegularField, {'name': 'image__description'}),
                                       ],
                           )

        lv_url = self._set_listview_state()
        response = self.assertGET200(self._build_url(self.ct), data={'list_url': lv_url})
        it = (force_unicode(line) for line in response.content.splitlines()); it.next()

        self.assertEqual(it.next(), '"Black","Jet face","Jet\'s selfie"')
#        self.assertEqual(it.next(), '"Bouquet","",""')

        HIDDEN_VALUE = settings.HIDDEN_VALUE
        self.assertEqual(it.next(), '"Spiegel","%s","%s"' % (HIDDEN_VALUE, HIDDEN_VALUE))
        self.assertEqual(it.next(), '"Valentine","",""')

#    @skipIfNotInstalled('creme.emails')
    def test_list_view_export07(self):
        "M2M field on CremeEntities"
#        from creme.emails.models import EmailCampaign, MailingList

        user = self.login()

        create_camp = partial(EmailCampaign.objects.create, user=user)
        camp1 = create_camp(name='Camp#1')
        camp2 = create_camp(name='Camp#2')
        create_camp(name='Camp#3')

        create_ml = partial(MailingList.objects.create, user=user)
        camp1.mailing_lists = [create_ml(name='ML#1'), create_ml(name='ML#2')]
        camp2.mailing_lists = [create_ml(name='ML#3')]

        HeaderFilter.create(pk='test_hf', name='Campaign view', model=EmailCampaign,
                            cells_desc=[(EntityCellRegularField, {'name': 'name'}),
                                        (EntityCellRegularField, {'name': 'mailing_lists__name'}),
                                       ],
                           )

        lv_url = self._set_listview_state(model=EmailCampaign)
        response = self.assertGET200(self._build_url(ContentType.objects.get_for_model(EmailCampaign)),
                                     data={'list_url': lv_url}
                                    )
        result = [force_unicode(line) for line in response.content.splitlines()]
        self.assertEqual(4, len(result))

        self.assertEqual(result[1], '"Camp#1","ML#1/ML#2"')
        self.assertEqual(result[2], '"Camp#2","ML#3"')
        self.assertEqual(result[3], '"Camp#3",""')

    def test_list_view_export08(self):
        "FieldsConfig"
        self.login()
        self._build_hf_n_contacts()
        lv_url = self._set_listview_state()

        FieldsConfig.create(Contact,
                            descriptions=[('first_name', {FieldsConfig.HIDDEN: True})],
                           )

        response = self.assertGET200(self._build_url(self.ct), data={'list_url': lv_url})

        it = (force_unicode(line) for line in response.content.splitlines())
        self.assertEqual(it.next(),
                         u','.join(u'"%s"' % u for u in [_('Civility'),
                                                         _('Last name'),
                                                         #_('First name'),
                                                         'pilots',
                                                         _('Properties'),
                                                        ]
                                  )
                        )

        #self.assertEqual(it.next(), u'"","Black","Jet","Bebop",""')
        self.assertEqual(it.next(), u'"","Black","Bebop",""')

    @skipIf(XlsMissing, "Skip tests, couldn't find xlwt or xlrd libs")
    def test_xls_export01(self):
        self.login()
        cells = self._build_hf_n_contacts()
        lv_url = self._set_listview_state()
        response = self.assertGET200(self._build_url(self.ct, doc_type='xls'),
                                     data={'list_url': lv_url}, follow=True,
                                    )

        it = iter(XlrdReader(None, file_contents=response.content))
        self.assertEqual(it.next(), [hfi.title for hfi in cells])
        self.assertEqual(it.next(), ["", "Black", "Jet", "Bebop", ""])
#        self.assertEqual(it.next(), ["", "Bouquet", "Mireille", "", ""])
#        self.assertEqual(it.next(), ["", "Creme", "Fulbert", "", ""])
        self.assertIn(it.next(), (["", "Spiegel", "Spike", "Bebop/Swordfish", ""],
                                  ["", "Spiegel", "Spike", "Swordfish/Bebop", ""]))
        self.assertIn(it.next(), (["", "Valentine", "Faye", "", "is a girl/is beautiful"],
                                  ["", "Valentine", "Faye", "", "is beautiful/is a girl"]))
        self.assertEqual(it.next(), ["", "Wong", "Edward", "", "is a girl"])
#        self.assertEqual(it.next(), ["", "Yumura", "Kirika", "", ""])
        self.assertRaises(StopIteration, it.next)

    def test_print_integer01(self):
        "No choices"
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        for name, capital in (('Bebop', 1000), ('Swordfish', 20000), ('Redtail', None)):
            create_orga(name=name, capital=capital)

        build = partial(EntityCellRegularField.build, model=Organisation)
        HeaderFilter.create(pk='test-hf_orga', name='Organisation view',
                            model=Organisation,
                            cells_desc=[build(name='name'), build(name='capital')],
                           )

        lv_url = self._set_listview_state(model=Organisation)
        response = self.assertGET200(self._build_url(ContentType.objects.get_for_model(Organisation)),
                                     data={'list_url': lv_url}, follow=True,
                                    )

        lines = {force_unicode(line) for line in response.content.splitlines()}
        self.assertIn(u'"Bebop","1000"', lines)
        self.assertIn(u'"Swordfish","20000"', lines)
        self.assertIn(u'"Redtail",""', lines)

#    @skipIfNotInstalled('creme.billing')
    def test_print_integer02(self):
        "Field with choices"
        user = self.login()

#        from creme.billing.models import Invoice, InvoiceStatus, Line, ProductLine
#        from creme.billing.constants import DISCOUNT_PERCENT, DISCOUNT_LINE_AMOUNT
#
#        invoice = Invoice.objects.create(user=user, name='Invoice',
#                                         expiration_date=date(year=2012, month=12, day=15),
#                                         status=InvoiceStatus.objects.all()[0]
#                                        )
#
#        create_pline = partial(ProductLine.objects.create, user=user, related_document=invoice)
#        create_pline(on_the_fly_item='Fly1', discount_unit=DISCOUNT_PERCENT)
#        create_pline(on_the_fly_item='Fly2', discount_unit=DISCOUNT_LINE_AMOUNT)
#
#        build = partial(EntityCellRegularField.build, model=Line)
#        HeaderFilter.create(pk='test-hf_pline', name='ProductLine view',
#                            model=ProductLine,
#                            cells_desc=[build(name='on_the_fly_item'),
#                                        build(name='discount_unit'),
#                                       ],
#                           )
#
#        lv_url = self._set_listview_state(model=ProductLine)
#        response = self.assertGET200(self._build_url(ContentType.objects.get_for_model(ProductLine)),
#                                     data={'list_url': lv_url}, follow=True,
#                                    )
#
#        lines = {force_unicode(line) for line in response.content.splitlines()}
#        self.assertIn(u'"Fly1","%s"' % _(u'Percent'), lines)
#        self.assertIn(u'"Fly2","%s"' % _(u'Amount'), lines)
        invoice = FakeInvoice.objects.create(user=user, name='Invoice',
                                             expiration_date=date(year=2012, month=12, day=15),
                                            )

        create_pline = partial(FakeInvoiceLine.objects.create, user=user, invoice=invoice)
        create_pline(item='Bebop',     discount_unit=FAKE_PERCENT_UNIT)
        create_pline(item='Swordfish', discount_unit=FAKE_AMOUNT_UNIT)

        build = partial(EntityCellRegularField.build, model=FakeInvoiceLine)
        HeaderFilter.create(pk='test-hf_fakeinvoiceline', name='InvoiceLine view',
                            model=FakeInvoiceLine,
                            cells_desc=[build(name='item'),
                                        build(name='discount_unit'),
                                       ],
                           )

        lv_url = self._set_listview_state(model=FakeInvoiceLine)
        response = self.assertGET200(self._build_url(ContentType.objects.get_for_model(FakeInvoiceLine)),
                                     data={'list_url': lv_url}, follow=True,
                                    )

        lines = {force_unicode(line) for line in response.content.splitlines()}
        self.assertIn(u'"Bebop","%s"' % _(u'Percent'), lines)
        self.assertIn(u'"Swordfish","%s"' % _(u'Amount'), lines)
