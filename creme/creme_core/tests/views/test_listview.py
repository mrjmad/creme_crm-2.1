# -*- coding: utf-8 -*-

try:
    from datetime import date, timedelta
    from functools import partial

    from django.contrib.contenttypes.models import ContentType
    from django.utils.timezone import now

    from .base import ViewsTestCase
    from ..fake_models import (FakeContact as Contact, FakeImage as Image,
            FakeOrganisation as Organisation, FakeAddress as Address,
            FakeActivity as Activity, FakeActivityType as ActivityType,
            FakeEmailCampaign as EmailCampaign,
            FakeCivility as Civility, FakeSector as Sector)
    from creme.creme_core.core.entity_cell import (EntityCellRegularField,
            EntityCellCustomField, EntityCellFunctionField, EntityCellRelation)
    from creme.creme_core.models import (EntityFilter, EntityFilterCondition,
            HeaderFilter, RelationType, Relation, CremePropertyType, CremeProperty,
            CustomField, CustomFieldEnumValue)
    from creme.creme_core.models.header_filter import HeaderFilterList
    from creme.creme_core.models.entity_filter import EntityFilterList
    from creme.creme_core.utils import safe_unicode
#    from creme.creme_core.tests.base import skipIfNotInstalled

#    from creme.persons.models import Organisation, Contact, Civility, Sector, Address

#    from creme.activities.models import Activity, ActivityType
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


class ListViewTestCase(ViewsTestCase):
    @classmethod
    def setUpClass(cls):
        ViewsTestCase.setUpClass()

#        cls.populate('creme_core', 'creme_config', 'billing')
        cls.populate('creme_core')

        cls.url = Organisation.get_lv_absolute_url()
        cls.ctype = ContentType.objects.get_for_model(Organisation)

        cls._civ_backup = list(Civility.objects.all())
        Civility.objects.all().delete()

    @classmethod
    def tearDownClass(cls):
        ViewsTestCase.tearDownClass()
        Civility.objects.bulk_create(cls._civ_backup)

    def setUp(self):
        self._address_ordering = Address._meta.ordering
        Address._meta.ordering = ()

    def tearDown(self):
        Address._meta.ordering = self._address_ordering

    def assertFound(self, x, string): #TODO: in CremeTestCase ??
        idx = string.find(x)
        self.assertNotEqual(-1, idx, '"%s" not found' % x)

        return idx

    def _get_lv_content(self, response): #TODO: slice end too
        content = response.content
        start_idx = content.find('<table id="list"')
        self.assertNotEqual(-1, start_idx)

        return content[start_idx:]

    def _get_entities_set(self, response):
        with self.assertNoException():
            entities_page = response.context['entities']

        return set(entities_page.object_list)

    def _build_hf(self, *args):
        cells = [EntityCellRegularField.build(model=Organisation, name='name')]
        cells.extend(args)
        return HeaderFilter.create(pk='test-hf_orga', name='Orga view',
                                   model=Organisation, cells_desc=cells,
                                  )

    def test_content01(self):
        self.login()
        user = self.user

        create_orga = partial(Organisation.objects.create, user=user)
        bebop     = create_orga(name='Bebop')
        swordfish = create_orga(name='Swordfish')

        create_contact = partial(Contact.objects.create, user=user)
        spike = create_contact(first_name='Spike', last_name='Spiegel')
        faye  = create_contact(first_name='Faye',  last_name='Valentine')

        #Relation
        rtype = RelationType.create(('test-subject_piloted', 'is piloted by'),
                                    ('test-object_piloted',  'pilots'),
                                   )[0]
        Relation.objects.create(user=user, subject_entity=swordfish,
                                type=rtype, object_entity=spike,
                               )

        #Property
        create_ptype = CremePropertyType.create
        ptype1 = create_ptype(str_pk='test-prop_red',  text='is red')
        ptype2 = create_ptype(str_pk='test-prop_fast', text='is fast')
        CremeProperty.objects.create(type=ptype1, creme_entity=swordfish)

        #CustomField
        cfield = CustomField.objects.create(name='size (m)',
                                            content_type=self.ctype,
                                            field_type=CustomField.INT,
                                           )
        cfield_value = 42
        cfield.get_value_class()(custom_field=cfield, entity=bebop).set_value_n_save(cfield_value)

        hf = self._build_hf(EntityCellRelation(rtype=rtype),
                            #EntityCellFunctionField(func_field=Organisation.function_fields.get('get_pretty_properties')),
                            EntityCellFunctionField.build(Organisation, 'get_pretty_properties'),
                            EntityCellCustomField(cfield),
                           )

        #response = self.assertGET200(self.url)
        response = self.assertPOST200(self.url, data={'hfilter': hf.id})

        with self.assertNoException():
            ctxt = response.context
            hfilters = ctxt['header_filters']
            efilters = ctxt['entity_filters']
            orgas_page = ctxt['entities']

        self.assertIsInstance(hfilters, HeaderFilterList)
        self.assertIn(hf, hfilters)

        self.assertIsInstance(efilters, EntityFilterList)

        with self.assertNoException():
            sel_hf = hfilters.selected

        self.assertIsInstance(sel_hf, HeaderFilter)
        self.assertEqual(sel_hf.id, hf.id)

        orgas_set = set(orgas_page.object_list)
        self.assertIn(bebop,     orgas_set)
        self.assertIn(swordfish, orgas_set)

        content = self._get_lv_content(response)
        bebop_idx = self.assertFound(bebop.name, content)
        swordfish_idx = self.assertFound(swordfish.name, content)
        self.assertGreater(swordfish_idx, bebop_idx) #order

        content = safe_unicode(content)

        self.assertIn(rtype.predicate, content)
        self.assertIn(unicode(spike), content)
        self.assertNotIn(faye.last_name, content)

        self.assertIn(u'<ul><li>%s</li></ul>' % ptype1.text, content)
        self.assertNotIn(ptype2.text, content)

        self.assertIn(cfield.name, content)
        self.assertIn(str(cfield_value), content)

    def test_order01(self): #TODO: test with ajax ?
        self.login()

        create_orga = partial(Organisation.objects.create, user=self.user)
        bebop     = create_orga(name='Bebop')
        swordfish = create_orga(name='Swordfish')

        self._build_hf()

        def post(first, second, sort_order='', sort_field='regular_field-name'):
            response = self.assertPOST200(self.url,
                                          data={'sort_field': sort_field,
                                                'sort_order': sort_order,
                                               }
                                         )
            content = self._get_lv_content(response)
            first_idx = self.assertFound(first.name, content)
            second_idx = self.assertFound(second.name, content)
            self.assertLess(first_idx, second_idx)

        post(bebop, swordfish)
        post(swordfish, bebop, '-')
        post(bebop, swordfish, '*') #invalid value
        post(bebop, swordfish, sort_field='unknown') #invalid value

    #TODO: for now there should not be CremeEntity with 'id' as ordering
    #def test_order02_prelude(self):
        #"Sort by ForeignKey"
        ##NB: the DatabaseError cannot be rollbacked here in the test context,
        ##    so we cannot do this test in test_order02, because it cause an error.
        #try:
            #bool(Contact.objects.order_by('image'))
        #except:
            #pass
        #else:
            #self.fail('ORM bug has been fixed ?! => reactivate FK on CremeEntity sorting')

    def assertListViewContentOrder(self, response, key, entries):
            content = safe_unicode(self._get_lv_content(response))
            lines = [(self.assertFound(unicode(getattr(e, key)), content), e)
                        for e in entries
                    ]
            self.assertListEqual(list(entries),
                                 [line[1] for line in sorted(lines, key=lambda e:e[0])])

    def test_order02(self):
        "Sort by ForeignKey"
        self.login()

        create_civ = Civility.objects.create
        mister = create_civ(title='Mister')
        miss   = create_civ(title='Miss')
        self.assertLess(mister.id, miss.id)

        create_contact = partial(Contact.objects.create, user=self.user)
        spike = create_contact(first_name='Spike',  last_name='Spiegel',   civility=mister)
        faye  = create_contact(first_name='Faye',   last_name='Valentine', civility=miss)
        ed    = create_contact(first_name='Edward', last_name='Wong')

        hf = HeaderFilter.create(pk='test-hf_contact', name='Order02 view', model=Contact)

        build_cell = partial(EntityCellRegularField.build, model=Contact)
        cell_image    = build_cell(name='image')
        cell_img_name = build_cell(name='image__name')
        cell_civ      = build_cell(name='civility')
        cell_civ_name = build_cell(name='civility__title')

        self.assertTrue(cell_civ.sortable)
        #self.assertFalse(cell_image.sortable)
        self.assertTrue(cell_image.sortable)
        self.assertTrue(cell_img_name.sortable)
        self.assertTrue(cell_civ_name.sortable)

        hf.cells = [build_cell(name='last_name'),
                    cell_image, cell_img_name, cell_civ, cell_civ_name,
                   ]
        hf.save()

        url = Contact.get_lv_absolute_url()

        #---------------------------------------------------------------------
        response = self.assertPOST200(url, data={'hfilter': hf.id})

        with self.assertNoException():
            selected_hf = response.context['header_filters'].selected

        self.assertEqual(hf, selected_hf)

        #---------------------------------------------------------------------
        #FK on CremeEntity we just check that it does not crash
        self.assertPOST200(url, data={'sort_field': 'regular_field-image'})

        #---------------------------------------------------------------------

        def post(field_name, reverse, *contacts):
            response = self.assertPOST200(url,
                                          data={'sort_field': field_name,
                                                'sort_order': '-' if reverse else '',
                                               }
                                         )
            content = self._get_lv_content(response)
            indices = [self.assertFound(c.last_name, content)
                        for c in contacts
                      ]
            self.assertEqual(indices, sorted(indices))

            return content

        #NB: it seems that NULL are not ordered in the same way on different DB engines
        #post('civility', False, ed, spike, faye) #Beware: sorting is done by id
        #content = post('civility', False, spike, faye) #Beware: sorting is done by id
        content = post('regular_field-civility', False, faye, spike) # sorting is done by 'title'
        self.assertFound(ed.last_name, content)

        #post('civility', True, faye, spike, ed)
        #post('civility', True, faye, spike)
        post('regular_field-civility', True, spike, faye)
        #post('civility__title', False, ed, faye, spike)
        post('regular_field-civility__title', False, faye, spike)
        #post('civility__title', True, spike, faye, ed)
        post('regular_field-civility__title', True, spike, faye)

#    @skipIfNotInstalled('creme.emails')
    def test_order03(self):
        "Unsortable fields: ManyToMany, FunctionFields"
#        from creme.emails.models import EmailCampaign
        self.login()

        #bug on ORM with M2M happens only if there is at least one entity
        EmailCampaign.objects.create(user=self.user, name='Camp01')

        fname = 'mailing_lists'
        func_field_name = 'get_pretty_properties'
        HeaderFilter.create(pk='test-hf_camp', name='Campaign view', model=EmailCampaign,
                            cells_desc=[(EntityCellRegularField, {'name': 'name'}),
                                        (EntityCellRegularField, {'name': fname}),
                                        (EntityCellFunctionField, {'func_field_name': func_field_name}),
                                       ]
                           )

        url = EmailCampaign.get_lv_absolute_url()
        #we just check that it does not crash
        self.assertPOST200(url, data={'sort_field': 'regular_field-' + fname})
        self.assertPOST200(url, data={'sort_field': 'function_field-' + func_field_name})

    def test_order04(self):
        "Ordering = '-fieldname'"
        user = self.login()
        self.assertTrue('-start', Activity._meta.ordering[0])

#        act_type = ActivityType.objects.create(pk='creme_core-lvtest1', name='Karate session',
#                                               default_day_duration=1, default_hour_duration="00:15:00",
#                                               is_custom=True,
#                                              )

        act_type = ActivityType.objects.all()[0]
        create_act = partial(Activity.objects.create, user=user, type=act_type)
        act1 = create_act(title='Act#1', start=now())
        act2 = create_act(title='Act#2', start=act1.start + timedelta(hours=1))

#        HeaderFilter.create(pk='test-hf_act', name='Activity view',
#                            model=Activity,
#                            cells_desc=[(EntityCellRegularField, {'name': 'title'}),
#                                        (EntityCellRegularField, {'name': 'start'}),
#                                       ],
#                           )
        hf = self.get_object_or_fail(HeaderFilter, pk='creme_core-hf_fakeactivity') # see fake populate

#        response = self.assertPOST200(Activity.get_lv_absolute_url())
        response = self.assertPOST200(Activity.get_lv_absolute_url(), {'hfilter': hf.pk})
        content = self._get_lv_content(response)
        first_idx  = self.assertFound(act2.title, content)
        second_idx = self.assertFound(act1.title, content)
        self.assertLess(first_idx, second_idx)

        with self.assertNoException():
            lvs = response.context['list_view_state']
            sort_field = lvs.sort_field
            sort_order = lvs.sort_order
            ordering = lvs._ordering

        self.assertEqual('regular_field-start', sort_field)
        self.assertEqual('-',  sort_order)
        self.assertEqual(['-start'], ordering)

    def test_ordering_default(self):
        user = self.login()
        self.assertEqual(('last_name', 'first_name'), Contact._meta.ordering)

        create_contact = partial(Contact.objects.create, user=user)
        create_contact(first_name='Spike',  last_name='Spiegel')
        create_contact(first_name='Faye',   last_name='Valentine')
        create_contact(first_name='Edward', last_name='Wong')

        url = Contact.get_lv_absolute_url()
        # for the filter to prevent an issue when HeaderFiltersTestCase is launched before this test
#        response = self.assertPOST200(url, {'hfilter': 'persons-hf_contact'})
        hf = self.get_object_or_fail(HeaderFilter, pk='creme_core-hf_fakecontact') # see fake populate
        response = self.assertPOST200(url, {'hfilter': hf.pk})

        #entries = Contact.objects.order_by('last_name', 'first_name')
        entries = Contact.objects.all()
        self.assertListViewContentOrder(response, 'last_name', entries)

        listview_state = response.context['list_view_state']
        self.assertEqual('regular_field-last_name', listview_state.sort_field)
        self.assertEqual('', listview_state.sort_order)
        self.assertListEqual(['last_name', 'first_name'], listview_state._ordering)

    def test_ordering_merge_column_and_default(self):
        self.assertEqual(('last_name', 'first_name'), Contact._meta.ordering)
        self.login()

        create_civ = Civility.objects.create
        mister = create_civ(title='Mister')
        miss   = create_civ(title='Miss')
        self.assertLess(mister.id, miss.id)

        create_contact = partial(Contact.objects.create, user=self.user)
        spike = create_contact(first_name='Spike',  last_name='Spiegel',   civility=mister)
        faye = create_contact(first_name='Faye',   last_name='Valentine', civility=miss)
        ed = create_contact(first_name='Edward', last_name='Wong')

        hf = HeaderFilter.create(pk='test-hf_contact', name='Order02 view', model=Contact,
                                 cells_desc=[(EntityCellRegularField, {'name': 'civility'}),
                                             (EntityCellRegularField, {'name': 'last_name'}),
                                             (EntityCellRegularField, {'name': 'first_name'}),
                                            ],)

        contacts = Contact.objects.filter(pk__in=(spike, faye, ed))
        url = Contact.get_lv_absolute_url()
        response = self.assertPOST200(url, data={'hfilter': hf.id,
                                                 'sort_field': 'regular_field-civility',
                                                 'sort_order': ''})

        entries = contacts.order_by('civility', 'last_name', 'first_name')
        self.assertListViewContentOrder(response, 'last_name', entries)

        response = self.assertPOST200(url, data={'hfilter': hf.id,
                                                 'sort_field': 'regular_field-civility',
                                                 'sort_order': '-'})

        entries = contacts.order_by('-civility', 'last_name', 'first_name')
        self.assertListViewContentOrder(response, 'last_name', entries)

        response = self.assertPOST200(url, data={'hfilter': hf.id,
                                                 'sort_field': 'regular_field-first_name',
                                                 'sort_order': ''})

        entries = contacts.order_by('first_name', 'last_name')
        self.assertListViewContentOrder(response, 'last_name', entries)

        response = self.assertPOST200(url, data={'hfilter': hf.id,
                                                 'sort_field': 'regular_field-first_name',
                                                 'sort_order': '-'})

        entries = contacts.order_by('-first_name', 'last_name')
        self.assertListViewContentOrder(response, 'last_name', entries)

    def test_ordering_related_column(self):
        user = self.login()

        self.assertEqual(('last_name', 'first_name'), Contact._meta.ordering)
        self.assertFalse(bool(Address._meta.ordering))

        def create_contact(first_name, last_name, address):
            contact = Contact.objects.create(user=self.user, first_name=first_name, last_name=last_name)
#            contact.billing_address = Address.objects.create(owner=contact, name=address)
            contact.address = Address.objects.create(entity=contact, value=address)
            contact.save()
            return contact

        create_contact(first_name='Spike',  last_name='Spiegel',   address='C')
        create_contact(first_name='Faye',   last_name='Valentine', address='B')
        create_contact(first_name='Edward', last_name='Wong',      address='A')

        hf = HeaderFilter.create(pk='test-hf_contact', name='Order02 view', model=Contact,
                                 cells_desc=[(EntityCellRegularField, {'name': 'civility'}),
                                             (EntityCellRegularField, {'name': 'last_name'}),
                                             (EntityCellRegularField, {'name': 'first_name'}),
#                                             (EntityCellRegularField, {'name': 'billing_address'}),
                                             (EntityCellRegularField, {'name': 'address'}),
                                         ],
                           )

        url = Contact.get_lv_absolute_url()
        # for the filter to prevent an issue when HeaderFiltersTestCase is launched before this test
        response = self.assertPOST200(url, {'hfilter':     hf.id,
#                                            'sort_field': 'regular_field-billing_address',
                                            'sort_field': 'regular_field-address',
                                            'sort_order': '',
                                           })

#        entries = Contact.objects.order_by('billing_address__pk', 'last_name', 'first_name')
        entries = Contact.objects.order_by('address__pk', 'last_name', 'first_name')
        self.assertListViewContentOrder(response, 'last_name', entries)

        listview_state = response.context['list_view_state']
#        self.assertEqual('regular_field-billing_address', listview_state.sort_field)
        self.assertEqual('regular_field-address', listview_state.sort_field)
        self.assertEqual('', listview_state.sort_order)
#        self.assertListEqual(['billing_address__pk', 'last_name', 'first_name'], listview_state._ordering)
        self.assertListEqual(['address__pk', 'last_name', 'first_name'],
                             listview_state._ordering
                            )

#        Address._meta.ordering = ('name',)
        Address._meta.ordering = ('value',) #TODO: create another test model instead ??

        response = self.assertPOST200(url, {'hfilter': hf.id,
#                                            'sort_field': 'regular_field-billing_address',
                                            'sort_field': 'regular_field-address',
                                            'sort_order': '',
                                           }
                                     )

#        entries = Contact.objects.order_by('billing_address__name', 'last_name', 'first_name')
        entries = Contact.objects.order_by('address__value', 'last_name', 'first_name')
        self.assertListViewContentOrder(response, 'last_name', entries)

        listview_state = response.context['list_view_state']
#        self.assertEqual('regular_field-billing_address', listview_state.sort_field)
        self.assertEqual('regular_field-address', listview_state.sort_field)
        self.assertEqual('', listview_state.sort_order)
#        self.assertListEqual(['billing_address__name', 'last_name', 'first_name'], listview_state._ordering)
        self.assertListEqual(['address__value', 'last_name', 'first_name'],
                             listview_state._ordering
                            )

    def test_ordering_customfield_column(self):
        "Custom field ordering is ignored in current implementation"
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        bebop     = create_orga(name='Bebop')
        swordfish = create_orga(name='Swordfish')
        redtail   = create_orga(name='Redtail')

        cfield = CustomField.objects.create(name='size (m)',
                                            content_type=self.ctype,
                                            field_type=CustomField.INT,
                                           )
        klass = cfield.get_value_class()

        def set_cfvalue(entity, value):
            klass(custom_field=cfield, entity=entity).set_value_n_save(value)

        set_cfvalue(bebop,     42)
        set_cfvalue(swordfish, 12)
        set_cfvalue(redtail,   4)

        cfield_cell = EntityCellCustomField(cfield)
        hf = self._build_hf(cfield_cell)

        url = Organisation.get_lv_absolute_url()
        response = self.assertPOST200(url, {'hfilter': hf.pk,
                                            'sort_field': cfield_cell.key,
                                            'sort_order': '',
                                           }
                                     )

        entries = Organisation.objects.order_by('name')
        self.assertListViewContentOrder(response, 'name', entries)

    def test_efilter01(self):
        self.login()
        user = self.user

        create_orga = partial(Organisation.objects.create, user=user)
        bebop   = create_orga(name='Bebop')
        redtail = create_orga(name='Redtail')
        dragons = create_orga(name='Red Dragons')

        self._build_hf()

        efilter = EntityFilter.create('test-filter01', 'Red', Organisation,
                                      user=user, is_custom=False,
                                      conditions=[EntityFilterCondition.build_4_field(
                                                        model=Organisation,
                                                        operator=EntityFilterCondition.ISTARTSWITH,
                                                        name='name', values=['Red'],
                                                    ),
                                                 ],
                                     )

        response = self.assertPOST200(self.url, data={'filter': efilter.id})

        content = self._get_lv_content(response)
        self.assertNotIn(bebop.name, content)
        self.assertIn(redtail.name,  content)
        self.assertIn(dragons.name,  content)

    def test_search_regularfields01(self):
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        bebop     = create_orga(name='Bebop')
        swordfish = create_orga(name='Swordfish',   phone='668899')
        redtail   = create_orga(name='Redtail',     phone='889977')
        dragons   = create_orga(name='Red Dragons', phone='123')

        self._build_hf(EntityCellRegularField.build(model=Organisation, name='phone'))

        url = self.url
        #data = {'_search': 1}

        def build_data(name='', phone='', search=1):
            return {'_search': 1,
                    'regular_field-name': name,
                    'regular_field-phone': phone,
                   }

        #response = self.assertPOST200(url, data=dict(data, name='Red', phone=''))
        response = self.assertPOST200(url, data=build_data('Red'))
        content = self._get_lv_content(response)
        self.assertNotIn(bebop.name,     content)
        self.assertNotIn(swordfish.name, content)
        self.assertIn(redtail.name,      content)
        self.assertIn(dragons.name,      content)

        #response = self.assertPOST200(url, data=dict(data, name='', phone='88'))
        response = self.assertPOST200(url, data=build_data('', '88'))
        content = self._get_lv_content(response)
        self.assertNotIn(bebop.name,   content)
        self.assertIn(swordfish.name,  content)
        self.assertIn(redtail.name,    content)
        self.assertNotIn(dragons.name, content)

        #response = self.assertPOST200(url, data=dict(data, name='Red', phone='88'))
        response = self.assertPOST200(url, data=build_data('Red', '88'))
        content = self._get_lv_content(response)
        self.assertNotIn(bebop.name,     content)
        self.assertNotIn(swordfish.name, content)
        self.assertIn(redtail.name,      content)
        self.assertNotIn(dragons.name,   content)

        #response = self.assertPOST200(url, data={'_search': 0, 'name': '', 'phone': ''})
        response = self.assertPOST200(url, data=build_data(search=0))
        content = self._get_lv_content(response)
        self.assertIn(bebop.name,     content)
        self.assertIn(swordfish.name, content)
        self.assertIn(redtail.name,   content)
        self.assertIn(dragons.name,   content)

    def test_search_regularfields02(self):
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        bebop = create_orga(name='Bebop inc', subject_to_vat=False)
        nerv  = create_orga(name='NERV',      subject_to_vat=True)
        seele = create_orga(name='Seele',     subject_to_vat=True)

        hf = self._build_hf(EntityCellRegularField.build(model=Organisation, name='subject_to_vat'))
        url = self.url
        data = {'hfilter': hf.id, '_search': 1}
        #response = self.assertPOST200(url, data=dict(data, subject_to_vat='1'))
        response = self.assertPOST200(url, data=dict(data, **{'regular_field-subject_to_vat': '1'}))
        orgas_set = self._get_entities_set(response)
        self.assertNotIn(bebop, orgas_set)
        self.assertIn(nerv,     orgas_set)
        self.assertIn(seele,    orgas_set)

        #response = self.assertPOST200(url, data=dict(data, subject_to_vat='0'))
        response = self.assertPOST200(url, data=dict(data, **{'regular_field-subject_to_vat': '0'}))
        orgas_set = self._get_entities_set(response)
        self.assertIn(bebop,    orgas_set)
        self.assertNotIn(nerv,  orgas_set)
        self.assertNotIn(seele, orgas_set)

    def test_search_regularfields03(self):
        "ForeignKey (NULL or not)"
        user = self.login()

        create_sector = Sector.objects.create
        mercenary = create_sector(title='Mercenary')
        robotics  = create_sector(title='Robotics')

        create_orga = partial(Organisation.objects.create, user=user)
        bebop = create_orga(name='Bebop inc', sector=mercenary)
        nerv  = create_orga(name='NERV',      sector=robotics)
        seele = create_orga(name='Seele')

        hf = self._build_hf(EntityCellRegularField.build(model=Organisation, name='sector'))

        url = self.url
        data = {'hfilter': hf.id, '_search': 1}
        #response = self.assertPOST200(url, data=dict(data, sector=str(mercenary.id)))
        response = self.assertPOST200(url, data=dict(data, **{'regular_field-sector': str(mercenary.id)}))
        orgas_set = self._get_entities_set(response)
        self.assertIn(bebop,    orgas_set)
        self.assertNotIn(nerv,  orgas_set)
        self.assertNotIn(seele, orgas_set)

        #response = self.assertPOST200(url, data=dict(data, sector='NULL'))
        response = self.assertPOST200(url, data=dict(data, **{'regular_field-sector': 'NULL'}))
        orgas_set = self._get_entities_set(response)
        self.assertNotIn(bebop, orgas_set)
        self.assertNotIn(nerv,  orgas_set)
        self.assertIn(seele,    orgas_set)

    def test_search_datefields01(self):
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        bebop     = create_orga(name='Bebop',     creation_date=date(year=2075, month=3, day=26))
        swordfish = create_orga(name='Swordfish', creation_date=date(year=2074, month=6, day=5))
        redtail   = create_orga(name='Redtail',   creation_date=date(year=2076, month=7, day=25))
        dragons   = create_orga(name='Red Dragons')

        hf = self._build_hf(EntityCellRegularField.build(model=Organisation, name='creation_date'))

        url = self.url
        #data = {'_search': 1}

        build_data = lambda cdate: {'hfilter': hf.id, '_search': 1, 'regular_field-creation_date': cdate}

        #response = self.assertPOST200(url, data=dict(data, creation_date=['1-1-2075']))
        response = self.assertPOST200(url, data=build_data(['1-1-2075']))
        content = self._get_lv_content(response)
        self.assertIn(bebop.name,        content)
        self.assertNotIn(swordfish.name, content)
        self.assertIn(redtail.name,      content)
        self.assertNotIn(dragons.name,   content)

        #response = self.assertPOST200(url, data=dict(data, creation_date=['', '1-1-2075']))
        response = self.assertPOST200(url, data=build_data(['', '1-1-2075']))
        content = self._get_lv_content(response)
        self.assertNotIn(bebop.name,   content)
        self.assertIn(swordfish.name,  content)
        self.assertNotIn(redtail.name, content)
        self.assertNotIn(dragons.name, content)

        #response = self.assertPOST200(url, data=dict(data, creation_date=['1-1-2074', '31-12-2074']))
        response = self.assertPOST200(url, data=build_data(['1-1-2074', '31-12-2074']))
        content = self._get_lv_content(response)
        self.assertNotIn(bebop.name,   content)
        self.assertIn(swordfish.name,  content)
        self.assertNotIn(redtail.name, content)
        self.assertNotIn(dragons.name, content)

    def test_search_datetimefields01(self):
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        bebop      = create_orga(name='Bebop')
        swordfish  = create_orga(name='Swordfish')
        swordfish2 = create_orga(name='Swordfish II')
        sf_alpha   = create_orga(name='Swordfish Alpha')
        redtail    = create_orga(name='Redtail')

        def set_created(orga, dt):
            Organisation.objects.filter(pk=orga.id).update(created=dt)

        #create_dt = partial(self.create_datetime, utc=True)
        create_dt = self.create_datetime
        set_created(bebop,      create_dt(year=2075, month=3, day=26))
        set_created(swordfish,  create_dt(year=2074, month=6, day=5, hour=12))
        set_created(swordfish2, create_dt(year=2074, month=6, day=6, hour=0))  #next day
        set_created(sf_alpha,   create_dt(year=2074, month=6, day=4, hour=23, minute=59)) #previous day
        set_created(redtail,    create_dt(year=2076, month=7, day=25))

        hf = self._build_hf(EntityCellRegularField.build(model=Organisation, name='created'))

        url = self.url
        #data = {'_search': 1}
        def post(created):
            response = self.assertPOST200(url, data={'hfilter': hf.id,
                                                     '_search': 1,
                                                     'regular_field-created': created,
                                                    }
                                         )
            return  self._get_lv_content(response)

        #response = self.assertPOST200(url, data=dict(data, created=['1-1-2075']))
        #content = self._get_lv_content(response)
        content = post(['1-1-2075'])
        self.assertIn(bebop.name,        content)
        self.assertNotIn(swordfish.name, content)
        self.assertIn(redtail.name,      content)

        #response = self.assertPOST200(url, data=dict(data, created=['', '1-1-2075']))
        #content = self._get_lv_content(response)
        content = post(['', '1-1-2075'])
        self.assertNotIn(bebop.name,   content)
        self.assertIn(swordfish.name,  content)
        self.assertNotIn(redtail.name, content)

        #response = self.assertPOST200(url, data=dict(data, created=['1-1-2074', '31-12-2074']))
        #content = self._get_lv_content(response)
        content = post(['1-1-2074', '31-12-2074'])
        self.assertNotIn(bebop.name,   content)
        self.assertIn(swordfish.name,  content)
        self.assertNotIn(redtail.name, content)

        #response = self.assertPOST200(url, data=dict(data, created=['5-6-2074', '5-6-2074']))
        #content = self._get_lv_content(response)
        content = post(['5-6-2074', '5-6-2074'])
        self.assertNotIn(bebop.name,      content)
        self.assertIn(swordfish.name,     content)
        self.assertNotIn(swordfish2.name, content)
        self.assertNotIn(sf_alpha.name,   content)
        self.assertNotIn(redtail.name,    content)

    def test_search_fk(self):
        user = self.login()

        create_civ = Civility.objects.create
        mister = create_civ(title='Mister')
        miss   = create_civ(title='Miss')
        self.assertLess(mister.id, miss.id)

#        img_faye = self.create_image(ident=1)
#        img_ed   = self.create_image(ident=2)
        create_img = partial(Image.objects.create, user=user)
        img_faye = create_img(name='Faye selfie')
        img_ed   = create_img(name='Ed selfie')

        create_contact = partial(Contact.objects.create, user=user)
        spike = create_contact(first_name='Spike',  last_name='Spiegel',   civility=mister)
        faye  = create_contact(first_name='Faye',   last_name='Valentine', civility=miss, image=img_faye)
        ed    = create_contact(first_name='Edward', last_name='Wong',                     image=img_ed)

        hf = HeaderFilter.create(pk='test-hf_contact', name='Order02 view', model=Contact)

        build_cell = partial(EntityCellRegularField.build, model=Contact)
        cell_image    = build_cell(name='image')
        cell_img_name = build_cell(name='image__name')
        cell_civ      = build_cell(name='civility')
        cell_civ_name = build_cell(name='civility__title')

        self.assertTrue(cell_civ.has_a_filter)
        self.assertTrue(cell_civ_name.has_a_filter)
        self.assertTrue(cell_img_name.has_a_filter)
        self.assertTrue(cell_image.has_a_filter)
        self.assertEqual('image__name__icontains', cell_img_name.filter_string)
        self.assertEqual('image__header_filter_search_field__icontains',
                         cell_image.filter_string
                        )

        hf.cells = [build_cell(name='last_name'),
                    cell_image, cell_img_name, cell_civ, cell_civ_name,
                   ]
        hf.save()

        url = Contact.get_lv_absolute_url()

        #---------------------------------------------------------------------
        response = self.assertPOST200(url, data={'hfilter': hf.id})

        with self.assertNoException():
            selected_hf = response.context['header_filters'].selected

        self.assertEqual(hf, selected_hf)

        #---------------------------------------------------------------------
        data = {'_search': 1}
        #response = self.assertPOST200(url, data=dict(data, civility=mister.id))
        response = self.assertPOST200(url, data=dict(data, **{'regular_field-civility': mister.id}))
        content = self._get_lv_content(response)
        self.assertIn(spike.last_name,   content)
        self.assertNotIn(faye.last_name, content)
        self.assertNotIn(ed.last_name,   content)

        #---------------------------------------------------------------------
        #response = self.assertPOST200(url, data=dict(data, civility__title='iss'))
        response = self.assertPOST200(url, data=dict(data, **{'regular_field-civility__title': 'iss'}))
        content = self._get_lv_content(response)
        self.assertNotIn(spike.last_name, content)
        self.assertIn(faye.last_name,     content)
        self.assertNotIn(ed.last_name,    content)

        #---------------------------------------------------------------------
        #response = self.assertPOST200(url, data=dict(data, image__name=img_ed.name))*
        response = self.assertPOST200(url, data=dict(data, **{'regular_field-image__name': img_ed.name}))
        content = self._get_lv_content(response)
        self.assertNotIn(spike.last_name, content)
        self.assertNotIn(faye.last_name,  content)
        self.assertIn(ed.last_name,       content)

        #---------------------------------------------------------------------
        #response = self.assertPOST200(url, data=dict(data, image=img_ed.name))
        response = self.assertPOST200(url, data=dict(data, **{'regular_field-image': img_ed.name}))
        content = self._get_lv_content(response)
        self.assertNotIn(spike.last_name, content)
        self.assertNotIn(faye.last_name,  content)
        self.assertIn(ed.last_name,       content)

#    @skipIfNotInstalled('creme.emails')
    def test_search_m2mfields01(self):
#        from creme.emails.models import EmailCampaign

        self.login()
        hf = HeaderFilter.create(pk='test-hf_camp', name='Campaign view',
                                 model=EmailCampaign,
                                )
        build_cell = partial(EntityCellRegularField.build, model=EmailCampaign)

        cell_m2m = build_cell(name='mailing_lists')
        self.assertFalse(cell_m2m.has_a_filter)
        self.assertEqual('', cell_m2m.filter_string)

        hf.cells = [build_cell(name='name'), cell_m2m]
        hf.save()

        #we just check that it does not crash
        self.assertPOST200(EmailCampaign.get_lv_absolute_url(),
                           data={'_search':       1,
                                 #'mailing_lists': 'MLname',
                                 'regular_field-mailing_lists': 'MLname',
                                }
                          )

    def test_search_relations01(self):
        self.login()
        user = self.user

        create_orga = partial(Organisation.objects.create, user=user)
        bebop     = create_orga(name='Bebop')
        swordfish = create_orga(name='Swordfish')
        redtail   = create_orga(name='Redtail')
        dragons   = create_orga(name='Red Dragons')

        create_contact = partial(Contact.objects.create, user=user)
        spike = create_contact(first_name='Spike', last_name='Spiegel')
        faye  = create_contact(first_name='Faye',  last_name='Spiegel')
        jet   = create_contact(first_name='Jet',   last_name='Black')

        rtype = RelationType.create(('test-subject_piloted', 'is piloted by'),
                                    ('test-object_piloted',  'pilots'),
                                   )[0]
        create_rel = partial(Relation.objects.create, user=user, type=rtype)
        create_rel(subject_entity=swordfish, object_entity=spike)
        create_rel(subject_entity=redtail,   object_entity=faye)
        create_rel(subject_entity=bebop,     object_entity=jet)

        hf = self._build_hf(EntityCellRelation(rtype=rtype))

        url = self.url
        #data = {'_search': 1, 'name': '', rtype.pk: 'Spiege'}
        data = {'hfilter': hf.id, '_search': 1, 'name': '', 'relation-%s' % rtype.pk: 'Spiege'}
        response = self.assertPOST200(url, data=data)
        content = self._get_lv_content(response)
        self.assertNotIn(bebop.name,   content)
        self.assertIn(swordfish.name,  content)
        self.assertIn(redtail.name,    content)
        self.assertNotIn(dragons.name, content)

        #response = self.assertPOST200(url, data=dict(data, name='Swo'))
        #content = self._get_lv_content(response)
        data['regular_field-name'] = 'Swo'
        content = self._get_lv_content(self.assertPOST200(url, data=data))
        self.assertNotIn(bebop.name,   content)
        self.assertIn(swordfish.name,  content)
        self.assertNotIn(redtail.name, content)
        self.assertNotIn(dragons.name, content)

    def test_search_customfield01(self):
        "INT"
        self.login()

        create_orga = partial(Organisation.objects.create, user=self.user)
        bebop     = create_orga(name='Bebop')
        swordfish = create_orga(name='Swordfish')
        redtail   = create_orga(name='Redtail')
        dragons   = create_orga(name='Red Dragons')

        cfield = CustomField.objects.create(name='size (m)',
                                            content_type=self.ctype,
                                            field_type=CustomField.INT,
                                           )
        klass = cfield.get_value_class()

        def set_cfvalue(entity, value):
            klass(custom_field=cfield, entity=entity).set_value_n_save(value)

        set_cfvalue(bebop,     42)
        set_cfvalue(swordfish, 12)
        set_cfvalue(redtail,   4)

        hf = self._build_hf(EntityCellCustomField(cfield))

        #response = self.assertPOST200(self.url, data={'_search': 1, 'name': '', cfield.pk: '4'})
        response = self.assertPOST200(self.url, data={'hfilter': hf.id,
                                                      '_search': 1,
                                                      'regular_field-name': '',
                                                      'custom_field-%s' % cfield.pk: '4',
                                                     }
                                     )
        content = self._get_lv_content(response)
        self.assertIn(bebop.name,        content)
        self.assertNotIn(swordfish.name, content)
        self.assertIn(redtail.name,      content)
        self.assertNotIn(dragons.name,   content)

    def test_search_customfield02(self):
        "INT & STR"
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        bebop     = create_orga(name='Bebop')
        swordfish = create_orga(name='Swordfish')
        redtail   = create_orga(name='Redtail')
        dragons   = create_orga(name='Red Dragons')

        create_cfield = partial(CustomField.objects.create, content_type=self.ctype)
        cfield1 = create_cfield(name='size (m)',   field_type=CustomField.INT)
        cfield2 = create_cfield(name='color code', field_type=CustomField.STR)

        def set_cfvalue(cfield, entity, value):
            cfield.get_value_class()(custom_field=cfield, entity=entity).set_value_n_save(value)

        set_cfvalue(cfield1, bebop,     42)
        set_cfvalue(cfield1, swordfish, 12)
        set_cfvalue(cfield1, redtail,   4)

        set_cfvalue(cfield2, swordfish, '#ff0000')
        set_cfvalue(cfield2, redtail,   '#050508')

        hf = self._build_hf(EntityCellCustomField(cfield1), EntityCellCustomField(cfield2))

        response = self.assertPOST200(self.url, data={'hfilter': hf.id,
                                                      '_search': 1,
                                                      #'name': '',
                                                      #cfield1.pk: '4',
                                                      #cfield2.pk: '#05',
                                                      'regular_field-name': '',
                                                      'custom_field-%s' % cfield1.pk: '4',
                                                      'custom_field-%s' % cfield2.pk: '#05',
                                                     }
                                     )
        orgas_set = self._get_entities_set(response)
        self.assertNotIn(bebop,     orgas_set)
        self.assertNotIn(swordfish, orgas_set)
        self.assertIn(redtail,      orgas_set)
        self.assertNotIn(dragons,   orgas_set)

    def test_search_customfield03(self):
        "INT & INT"
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        bebop     = create_orga(name='Bebop')
        swordfish = create_orga(name='Swordfish')
        redtail   = create_orga(name='Redtail')
        dragons   = create_orga(name='Red Dragons')

        create_cfield = partial(CustomField.objects.create, content_type=self.ctype,
                                field_type=CustomField.INT,
                               )
        cfield1 = create_cfield(name='size (m)')
        cfield2 = create_cfield(name='weight')

        def set_cfvalue(cfield, entity, value):
            cfield.get_value_class()(custom_field=cfield, entity=entity).set_value_n_save(value)

        set_cfvalue(cfield1, bebop,     42)
        set_cfvalue(cfield1, swordfish, 12)
        set_cfvalue(cfield1, redtail,   4)

        set_cfvalue(cfield2, swordfish, 1000)
        set_cfvalue(cfield2, redtail,   2000)

        hf = self._build_hf(EntityCellCustomField(cfield1),
                            EntityCellCustomField(cfield2),
                           )
        response = self.assertPOST200(self.url, data={'hfilter': hf.id,
                                                      '_search': 1,
                                                      #'name': '',
                                                      #cfield1.pk: '4',
                                                      #cfield2.pk: '2000',
                                                      'regular_field-name': '',
                                                      'custom_field-%s' % cfield1.pk: '4',
                                                      'custom_field-%s' % cfield2.pk: '2000',
                                                     }
                                     )
        orgas_set = self._get_entities_set(response)
        self.assertNotIn(bebop,     orgas_set)
        self.assertNotIn(swordfish, orgas_set)
        self.assertIn(redtail,      orgas_set)
        self.assertNotIn(dragons,   orgas_set)

    def test_search_customfield04(self):
        "ENUM"
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        bebop     = create_orga(name='Bebop')
        swordfish = create_orga(name='Swordfish')
        redtail   = create_orga(name='Redtail')
        dragons   = create_orga(name='Red Dragons')

        cfield = CustomField.objects.create(name='Type',
                                            content_type=self.ctype,
                                            field_type=CustomField.ENUM,
                                           )

        create_evalue = CustomFieldEnumValue.objects.create
        type1 = create_evalue(custom_field=cfield, value='Light')
        type2 = create_evalue(custom_field=cfield, value='Heavy')

        klass = cfield.get_value_class()
        def set_cfvalue(entity, value):
            klass(custom_field=cfield, entity=entity).set_value_n_save(value)

        set_cfvalue(bebop,     type2.id)
        set_cfvalue(swordfish, type1.id)
        set_cfvalue(redtail,   type1.id)

        hf = self._build_hf(EntityCellCustomField(cfield))
        response = self.assertPOST200(self.url, data={'hfilter': hf.id,
                                                      '_search': 1,
                                                      #'name': '',
                                                      #cfield.pk: type1.id,
                                                      'regular_field-name': '',
                                                      'custom_field-%s' % cfield.pk: type1.id,
                                                     }
                                     )
        orgas_set = self._get_entities_set(response)
        self.assertNotIn(bebop,   orgas_set)
        self.assertIn(swordfish,  orgas_set)
        self.assertIn(redtail,    orgas_set)
        self.assertNotIn(dragons, orgas_set)

        response = self.assertPOST200(self.url, data={'hfilter': hf.id,
                                                      '_search': 1,
                                                      'name': '',
                                                      #cfield.pk: 'NULL',
                                                      'custom_field-%s' % cfield.pk: 'NULL',
                                                     }
                                     )
        orgas_set = self._get_entities_set(response)
        self.assertNotIn(bebop,     orgas_set)
        self.assertNotIn(swordfish, orgas_set)
        self.assertNotIn(redtail,   orgas_set)
        self.assertIn(dragons,      orgas_set)

    def test_search_customfield05(self):
        "MULTI_ENUM"
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        bebop    = create_orga(name='Bebop')
        dragons  = create_orga(name='Red Dragons')
        eva01    = create_orga(name='Eva01')
        valkyrie = create_orga(name='Valkyrie')

        cfield = CustomField.objects.create(name='Capabilities',
                                            content_type=self.ctype,
                                            field_type=CustomField.MULTI_ENUM,
                                           )

        create_evalue = CustomFieldEnumValue.objects.create
        can_walk = create_evalue(custom_field=cfield, value='Walk')
        can_fly  = create_evalue(custom_field=cfield, value='Fly')

        klass = cfield.get_value_class()
        def set_cfvalue(entity, value):
            klass(custom_field=cfield, entity=entity).set_value_n_save(value)

        set_cfvalue(bebop,     [can_fly.id])
        set_cfvalue(eva01,     [can_walk.id])
        set_cfvalue(valkyrie,  [can_fly.id, can_walk.id])

        hf = self._build_hf(EntityCellCustomField(cfield))
        response = self.assertPOST200(self.url, data={'hfilter': hf.id,
                                                      '_search': 1,
                                                      #'name':    '',
                                                      #cfield.pk: can_walk.id,
                                                      'regular_field-name':    '',
                                                      'custom_field-%s' % cfield.pk: can_walk.id,
                                                     }
                                     )
        orgas_set = self._get_entities_set(response)
        self.assertNotIn(bebop,   orgas_set)
        self.assertNotIn(dragons, orgas_set)
        self.assertIn(eva01,      orgas_set)
        self.assertIn(valkyrie,   orgas_set)

        response = self.assertPOST200(self.url, data={'hfilter': hf.id,
                                                      '_search': 1,
                                                      #'name':    '',
                                                      #cfield.pk: 'NULL',
                                                      'regular_field-name': '',
                                                      'custom_field-%s' % cfield.pk: 'NULL',
                                                     }
                                     )
        orgas_set = self._get_entities_set(response)
        self.assertNotIn(bebop,    orgas_set)
        self.assertNotIn(eva01,    orgas_set)
        self.assertNotIn(valkyrie, orgas_set)
        self.assertIn(dragons,     orgas_set)

    def test_search_customfield06(self):
        "2 x ENUM"
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        bebop     = create_orga(name='Bebop')
        swordfish = create_orga(name='Swordfish')
        redtail   = create_orga(name='Redtail')
        dragons   = create_orga(name='Red Dragons')

        create_cfield = partial(CustomField.objects.create,
                                content_type=self.ctype, field_type=CustomField.ENUM,
                               )
        cfield_type  = create_cfield(name='Type')
        cfield_color = create_cfield(name='Color')

        create_evalue = CustomFieldEnumValue.objects.create
        type1 = create_evalue(custom_field=cfield_type, value='Light')
        type2 = create_evalue(custom_field=cfield_type, value='Heavy')

        color1 = create_evalue(custom_field=cfield_color, value='Red')
        color2 = create_evalue(custom_field=cfield_color, value='Grey')

        def set_cfvalue(cfield, entity, value):
            cfield.get_value_class()(custom_field=cfield, entity=entity).set_value_n_save(value)

        set_cfvalue(cfield_type,  bebop,     type2.id)
        set_cfvalue(cfield_color, bebop,     color2.id)

        set_cfvalue(cfield_type,  swordfish, type1.id)
        set_cfvalue(cfield_color, swordfish, color1.id)

        set_cfvalue(cfield_type,  redtail,   type1.id)
        set_cfvalue(cfield_color, redtail,   color2.id)

        hf = self._build_hf(EntityCellCustomField(cfield_type),
                            EntityCellCustomField(cfield_color),
                           )
        response = self.assertPOST200(self.url, data={'hfilter': hf.id,
                                                      '_search':       1,
                                                      #'name':          '',
                                                      #cfield_type.pk:  type1.id,
                                                      #cfield_color.pk: color2.id,
                                                      'regular_field-name': '',
                                                      'custom_field-%s' % cfield_type.pk:  type1.id,
                                                      'custom_field-%s' % cfield_color.pk: color2.id,
                                                     }
                                     )
        orgas_set = self._get_entities_set(response)
        self.assertNotIn(bebop,     orgas_set)
        self.assertNotIn(swordfish, orgas_set)
        self.assertIn(redtail,      orgas_set)
        self.assertNotIn(dragons,   orgas_set)

        set_cfvalue(cfield_color, dragons, color1.id) #type is NULL

        response = self.assertPOST200(self.url, data={'hfilter': hf.id,
                                                      '_search':       1,
                                                      #'name':          '',
                                                      #cfield_type.pk:  'NULL',
                                                      #cfield_color.pk: color1.id,
                                                      'regular_field-name': '',
                                                      'custom_field-%s' % cfield_type.pk:  'NULL',
                                                      'custom_field-%s' % cfield_color.pk: color1.id,
                                                     }
                                     )
        orgas_set = self._get_entities_set(response)
        self.assertNotIn(bebop,     orgas_set)
        self.assertNotIn(swordfish, orgas_set)
        self.assertNotIn(redtail,   orgas_set)
        self.assertIn(dragons,      orgas_set)

    def test_search_customfield07(self):
        "2 x MULTI_ENUM"
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        bebop     = create_orga(name='Bebop')
        swordfish = create_orga(name='Swordfish')
        eva02     = create_orga(name='Eva02')
        valkyrie  = create_orga(name='Valkyrie')

        create_cfield = partial(CustomField.objects.create,
                                content_type=self.ctype,
                                field_type=CustomField.MULTI_ENUM,
                               )
        cfield_cap   = create_cfield(name='Capabilities')
        cfield_color = create_cfield(name='Color')

        create_evalue = CustomFieldEnumValue.objects.create
        can_fly  = create_evalue(custom_field=cfield_cap, value='Walk')
        can_walk = create_evalue(custom_field=cfield_cap, value='Fly')

        red    = create_evalue(custom_field=cfield_color, value='Red')
        grey   = create_evalue(custom_field=cfield_color, value='Grey')
        orange = create_evalue(custom_field=cfield_color, value='Orange')

        def set_cfvalue(cfield, entity, value):
            cfield.get_value_class()(custom_field=cfield, entity=entity).set_value_n_save(value)

        set_cfvalue(cfield_cap,   bebop,     [can_fly.id])
        set_cfvalue(cfield_color, bebop,     [grey.id])

        set_cfvalue(cfield_cap,   swordfish, [can_fly.id])
        set_cfvalue(cfield_color, swordfish, [red.id])

        set_cfvalue(cfield_cap,   eva02,     [can_walk.id])
        set_cfvalue(cfield_color, eva02,     [red.id, orange.id])

        set_cfvalue(cfield_cap,   valkyrie,  [can_fly.id, can_walk.id])

        hf = self._build_hf(EntityCellCustomField(cfield_cap),
                            EntityCellCustomField(cfield_color),
                           )
        response = self.assertPOST200(self.url, data={'hfilter': hf.id,
                                                      '_search':       1,
                                                      #'name':          '',
                                                      #cfield_cap.pk:   can_walk.id,
                                                      #cfield_color.pk: red.id,
                                                      'regular_field-name': '',
                                                      'custom_field-%s' % cfield_cap.pk:   can_walk.id,
                                                      'custom_field-%s' % cfield_color.pk: red.id,
                                                     }
                                     )
        orgas_set = self._get_entities_set(response)
        self.assertNotIn(bebop,     orgas_set)
        self.assertNotIn(swordfish, orgas_set)
        self.assertIn(eva02,        orgas_set)
        self.assertNotIn(valkyrie,  orgas_set)

        response = self.assertPOST200(self.url, data={'_search':       1,
                                                      #'name':          '',
                                                      #cfield_cap.pk:   can_walk.id,
                                                      #cfield_color.pk: 'NULL',
                                                      'regular_field-name': '',
                                                      'custom_field-%s' % cfield_cap.pk:   can_walk.id,
                                                      'custom_field-%s' % cfield_color.pk: 'NULL',
                                                     }
                                     )
        orgas_set = self._get_entities_set(response)
        self.assertNotIn(bebop,     orgas_set)
        self.assertNotIn(swordfish, orgas_set)
        self.assertNotIn(eva02,     orgas_set)
        self.assertIn(valkyrie,     orgas_set)

    def test_search_customfield08(self):
        "DATETIME"
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        bebop     = create_orga(name='Bebop')
        swordfish = create_orga(name='Swordfish')
        redtail   = create_orga(name='Redtail')
        dragons   = create_orga(name='Red Dragons')

        cfield = CustomField.objects.create(name='First flight',
                                            content_type=self.ctype,
                                            field_type=CustomField.DATETIME,
                                           )
        create_cf_value = partial(cfield.get_value_class().objects.create, custom_field=cfield)
        create_dt = partial(self.create_datetime, utc=True)
        create_cf_value(entity=bebop,     value=create_dt(year=2075, month=3, day=26))
        create_cf_value(entity=swordfish, value=create_dt(year=2074, month=6, day=5))
        create_cf_value(entity=redtail,   value=create_dt(year=2076, month=7, day=25))

        hf = self._build_hf(EntityCellCustomField(cfield))

        def post(dates):
            #response = self.assertPOST200(self.url, data={'_search': 1, cfield.pk: dates})
            response = self.assertPOST200(self.url, data={'hfilter': hf.id,
                                                          '_search': 1,
                                                          'custom_field-%s' % cfield.pk: dates,
                                                         }
                                         )
            return self._get_lv_content(response)

        content = post(['2075-1-1'])
        self.assertIn(bebop.name,        content)
        self.assertNotIn(swordfish.name, content)
        self.assertIn(redtail.name,      content)
        self.assertNotIn(dragons.name,   content)

        content = post(['', '1-1-2075'])
        self.assertNotIn(bebop.name,   content)
        self.assertIn(swordfish.name,  content)
        self.assertNotIn(redtail.name, content)
        self.assertNotIn(dragons.name, content)

        content = post(['1-1-2074', '31-12-2074'])
        self.assertNotIn(bebop.name,   content)
        self.assertIn(swordfish.name,  content)
        self.assertNotIn(redtail.name, content)
        self.assertNotIn(dragons.name, content)

        content = post(['5-6-2074', '5-6-2074'])
        self.assertNotIn(bebop.name,   content)
        self.assertIn(swordfish.name,  content)
        self.assertNotIn(redtail.name, content)
        self.assertNotIn(dragons.name, content)

    def test_search_customfield09(self):
        "2 x DATETIME"
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        bebop      = create_orga(name='Bebop')
        swordfish  = create_orga(name='Swordfish')
        redtail    = create_orga(name='Redtail')
        hammerhead = create_orga(name='HammerHead')
        dragons    = create_orga(name='Red Dragons')

        create_cfield = partial(CustomField.objects.create, content_type=self.ctype,
                                field_type=CustomField.DATETIME,
                               )
        cfield_flight = create_cfield(name='First flight')
        cfield_blood  = create_cfield(name='First blood')

        create_cf_value = partial(cfield_flight.get_value_class().objects.create)
        create_dt = partial(self.create_datetime, utc=True)
        create_cf_value(entity=bebop,      custom_field=cfield_flight, value=create_dt(year=2075, month=3, day=26))
        create_cf_value(entity=swordfish,  custom_field=cfield_flight, value=create_dt(year=2074, month=6, day=5))
        create_cf_value(entity=redtail,    custom_field=cfield_flight, value=create_dt(year=2076, month=7, day=25))
        create_cf_value(entity=hammerhead, custom_field=cfield_flight, value=create_dt(year=2074, month=7, day=6))

        create_cf_value(entity=swordfish,  custom_field=cfield_blood, value=create_dt(year=2074, month=6, day=8))
        create_cf_value(entity=hammerhead, custom_field=cfield_blood, value=create_dt(year=2075, month=7, day=6))

        hf = self._build_hf(EntityCellCustomField(cfield_flight),
                            EntityCellCustomField(cfield_blood),
                           )
        response = self.assertPOST200(self.url, data={'hfilter': hf.id,
                                                      '_search': 1,
                                                      #cfield_flight.pk: ['1-1-2074', '31-12-2074'],
                                                      #cfield_blood.pk:  ['',         '1-1-2075'],
                                                      'custom_field-%s' % cfield_flight.pk: ['1-1-2074', '31-12-2074'],
                                                      'custom_field-%s' % cfield_blood.pk:  ['',         '1-1-2075'],
                                                     })
        content = self._get_lv_content(response)
        self.assertNotIn(bebop.name,      content)
        self.assertIn(swordfish.name,     content)
        self.assertNotIn(redtail.name,    content)
        self.assertNotIn(hammerhead.name, content)
        self.assertNotIn(dragons.name,    content)

    def test_search_functionfield01(self):
        "_PrettyPropertiesField"
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        bebop     = create_orga(name='Bebop')
        swordfish = create_orga(name='Swordfish')
        eva01     = create_orga(name='Eva01')
        eva02     = create_orga(name='Eva02')

        create_ptype = CremePropertyType.create
        is_red  = create_ptype(str_pk='test-prop_red',  text='is red')
        is_fast = create_ptype(str_pk='test-prop_fast', text='is fast')

        create_prop = CremeProperty.objects.create
        create_prop(type=is_red, creme_entity=swordfish)
        create_prop(type=is_red, creme_entity=eva02)

        create_prop(type=is_fast, creme_entity=swordfish)
        create_prop(type=is_fast, creme_entity=bebop)

        ff_name = 'get_pretty_properties'
        hf = self._build_hf(EntityCellFunctionField.build(Organisation, ff_name))

        response = self.assertPOST200(self.url, data={'hfilter': hf.id,
                                                      '_search': 1,
                                                      'function_field-%s' % ff_name: 'red',
                                                     }
                                     )
        orgas_set = self._get_entities_set(response)
        self.assertIn(swordfish, orgas_set)
        self.assertIn(eva02,     orgas_set)
        self.assertNotIn(bebop,  orgas_set)
        self.assertNotIn(eva01,  orgas_set)

#    @skipIfNotInstalled('creme.assistants')
    def test_search_functionfield02(self):
        "Can not search on this FunctionField"
#        from creme.assistants.models import ToDo

        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        bebop     = create_orga(name='Bebop')
        swordfish = create_orga(name='Swordfish')

#        ToDo.objects.create(user=user, creme_entity=bebop, title='Reparation',
#                            description='To be repaired.',
#                           )

#        func_field = Organisation.function_fields.get('assistants-get_todos')
        func_field = Organisation.function_fields.get('tests-get_fake_todos')
        self._build_hf(EntityCellFunctionField(func_field))

        response = self.assertPOST200(self.url, data={'_search':       1,
                                                      'regular_field-name': '',
#                                                      'function_field-%s' % func_field.name: 'repair',
                                                      'function_field-%s' % func_field.name: bebop.name,
                                                     }
                                     )
        orgas_set = self._get_entities_set(response)
        self.assertIn(bebop,     orgas_set)
        self.assertIn(swordfish, orgas_set)