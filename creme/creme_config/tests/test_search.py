# -*- coding: utf-8 -*-

try:
    from functools import partial

    from django.utils.translation import ugettext as _
    from django.contrib.contenttypes.models import ContentType

    from creme.creme_core.models import SearchConfigItem
    from creme.creme_core.tests.base import CremeTestCase, skipIfNotInstalled
    from creme.creme_core.tests.fake_models import (FakeContact as Contact,
            FakeOrganisation as Organisation, FakeInvoice, FakeInvoiceLine)

    #from creme.persons.models import Contact, Organisation
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


class SearchConfigTestCase(CremeTestCase):
    ADD_URL = '/creme_config/search/add/'

    @classmethod
    def setUpClass(cls):
        CremeTestCase.setUpClass()

        SearchConfigItem.objects.all().delete()
        cls.populate('creme_core')

        get_ct = ContentType.objects.get_for_model
        cls.ct_contact = get_ct(Contact)
        cls.ct_orga    = get_ct(Organisation)

    def setUp(self):
        self.login()

    def _build_edit_url(self, sci):
        return '/creme_config/search/edit/%s' % sci.id

    def test_portal(self):
        self.assertGET200('/creme_config/search/portal/')

    def test_add01(self):
        ct = self.ct_contact
        self.assertEqual(0, SearchConfigItem.objects.filter(content_type=ct).count())

        url = self.ADD_URL
        self.assertGET200(url)
        self.assertNoFormError(self.client.post(url, data={'content_type': ct.id}))

        sc_items = SearchConfigItem.objects.filter(content_type=ct)
        self.assertEqual(1, len(sc_items))

        sc_item = sc_items[0]
        self.assertIsNone(sc_item.user)
        self.assertFalse(sc_item.disabled)

    def test_add02(self):
        "Unique congiguration"
        post = partial(self.client.post, self.ADD_URL,
                       data={'content_type': self.ct_contact.id,
                             'user':         self.other_user.id,
                            },
                      )
        self.assertNoFormError(post())

        sc_items = SearchConfigItem.objects.filter(content_type=self.ct_contact)
        self.assertEqual(1, len(sc_items))
        self.assertEqual(self.other_user, sc_items[0].user)

        self.assertFormError(post(), 'form', None,
                             _(u'The pair search configuration/user(s) already exists !')
                            )

    def test_add03(self):
        "Other CT"
        ct = self.ct_orga
        self.assertEqual(0, SearchConfigItem.objects.filter(content_type=ct).count())
        self.assertNoFormError(self.client.post(self.ADD_URL, data={'content_type': ct.id}))

        SearchConfigItem.objects.filter(content_type=ct)
        self.assertEqual(1, SearchConfigItem.objects.filter(content_type=ct).count())

    def _find_field_index(self, formfield, field_name):
        for i, (f_field_name, f_field_vname) in enumerate(formfield.choices):
            if f_field_name == field_name:
                return i

        self.fail('No "%s" in field' % field_name)

    def assertNoChoice(self, formfield, field_name):
        for i, (f_field_name, f_field_vname) in enumerate(formfield.choices):
            if f_field_name == field_name:
                self.fail(field_name + ' in choices')

    def _edit_config(self, url, sci, names_indexes, disabled=''):
        data = {'disabled': disabled}
        names = []

        for order, (name, index) in enumerate(names_indexes, start=1):
            data['fields_check_%s' % index] = 'on'
            data['fields_value_%s' % index] = name
            data['fields_order_%s' % index] = order

            names.append(name)

        response = self.client.post(url, data=data)
        self.assertNoFormError(response)

        sci = self.refresh(sci)
        self.assertEqual(names, [sf.name for sf in sci.searchfields])

        return sci

    def test_edit01(self):
        sci = SearchConfigItem.objects.create(content_type=self.ct_contact, user=None)
        url = self._build_edit_url(sci)
        response = self.assertGET200(url)

        with self.assertNoException():
            fields = response.context['form'].fields['fields']

        fname1 = 'first_name'
        index1 = self._find_field_index(fields, fname1)

        fname2 = 'last_name'
        index2 = self._find_field_index(fields, fname2)

        self._find_field_index(fields, 'civility__title')
        self.assertNoChoice(fields, 'birthday')

        sci = self._edit_config(url, sci, ((fname1, index1), (fname2, index2)))
        self.assertFalse(sci.disabled)

    def test_edit02(self):
        "Other CT + user + exclude BooleanField"
        sci = SearchConfigItem.objects.create(content_type=self.ct_orga, user=self.user)
        url = self._build_edit_url(sci)
        response = self.assertGET200(url)

        with self.assertNoException():
            fields = response.context['form'].fields['fields']

        fname1 = 'name'
        index1 = self._find_field_index(fields, fname1)

        fname2 = 'description'
        index2 = self._find_field_index(fields, fname2)

        self.assertNoChoice(fields, 'subject_to_vat')

        self._edit_config(url, sci, ((fname1, index1), (fname2, index2)))

    def test_edit03(self):
        "Disabled"
        sci = SearchConfigItem.objects.create(content_type=self.ct_contact, user=None)
        url = self._build_edit_url(sci)
        response = self.assertGET200(url)

        with self.assertNoException():
            fields = response.context['form'].fields['fields']

        fname1 = 'first_name'
        index1 = self._find_field_index(fields, fname1)
        sci = self._edit_config(url, sci, [(fname1, index1)], disabled='on')
        self.assertTrue(sci.disabled)

#    @skipIfNotInstalled('creme.billing')
    def test_edit04(self):
        "Fields with 'choices' are not valid"
#        from creme.billing.models import Line

        fname = 'discount_unit'
#        mfield = Line._meta.get_field(fname)
        mfield = FakeInvoiceLine._meta.get_field(fname)
        self.assertTrue(mfield.choices)

#        sci = SearchConfigItem.objects.create(content_type=ContentType.objects.get_for_model(Line))
        sci = SearchConfigItem.objects.create(content_type=ContentType.objects.get_for_model(FakeInvoiceLine))
        response = self.assertGET200(self._build_edit_url(sci))

        with self.assertNoException():
            fields = response.context['form'].fields['fields']

#        self._find_field_index(fields, 'comment')
        self._find_field_index(fields, 'item')
        self.assertNoChoice(fields, fname)

#    @skipIfNotInstalled('creme.recurrents')
    def test_edit05(self):
        "Exclude DateperiodField"
#        from creme.recurrents.models import RecurrentGenerator

#        sci = SearchConfigItem.objects.create(content_type=ContentType.objects.get_for_model(RecurrentGenerator))
        sci = SearchConfigItem.objects.create(content_type=ContentType.objects.get_for_model(FakeInvoice))
        response = self.assertGET200(self._build_edit_url(sci))

        with self.assertNoException():
            fields = response.context['form'].fields['fields']

        self._find_field_index(fields, 'name')
        self.assertNoChoice(fields, 'periodicity')

    def test_delete(self):
        sci = SearchConfigItem.create_if_needed(Contact, ['first_name', 'last_name'])
        self.assertPOST200('/creme_config/search/delete', data={'id': sci.id})
        self.assertDoesNotExist(sci)