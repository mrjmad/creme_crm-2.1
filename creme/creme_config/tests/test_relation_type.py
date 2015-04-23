# -*- coding: utf-8 -*-

try:
    from django.contrib.contenttypes.models import ContentType
    from django.utils.translation import ugettext as _

    from creme.creme_core.models import (RelationType, CremePropertyType,
            SemiFixedRelationType)
    from creme.creme_core.tests.base import CremeTestCase
    from creme.creme_core.tests.fake_models import (FakeContact as Contact,
            FakeOrganisation as Organisation)

    #from creme.persons.models import Contact, Organisation #need CremeEntity
except Exception, e:
    print('Error in <%s>: %s' % (__name__, e))


class RelationTypeTestCase(CremeTestCase):
    ADD_URL = '/creme_config/relation_type/add/'
    DEL_URL = '/creme_config/relation_type/delete'

    @classmethod
    def setUpClass(cls):
        CremeTestCase.setUpClass()
        cls.populate('creme_core')

    def setUp(self): #in CremeConfigTestCase ??
        self.login()

    def _build_edit_url(self, rtype):
        return '/creme_config/relation_type/edit/%s' % rtype.id

    def test_portal(self):
        self.assertGET200('/creme_config/relation_type/portal/')

    def test_create01(self):
        url = self.ADD_URL
        self.assertGET200(url)

        count = RelationType.objects.count()
        subject_pred = 'loves'
        object_pred  = 'is loved by'
        response = self.client.post(url, data={'subject_predicate': subject_pred,
                                               'object_predicate':  object_pred,
                                              }
                                   )
        self.assertNoFormError(response)

        self.assertEqual(count + 2, RelationType.objects.count()) #2 freshly created

        rel_type = self.get_object_or_fail(RelationType, predicate=subject_pred)
        self.assertTrue(rel_type.is_custom)
        self.assertEqual(object_pred, rel_type.symmetric_type.predicate)
        self.assertFalse(rel_type.subject_ctypes.all())
        self.assertFalse(rel_type.object_ctypes.all())
        self.assertFalse(rel_type.subject_properties.all())
        self.assertFalse(rel_type.object_properties.all())

    def test_create02(self):
        create_pt = CremePropertyType.create
        pt_sub = create_pt('test-pt_sub', 'has cash',  [Organisation])
        pt_obj = create_pt('test-pt_obj', 'need cash', [Contact])

        get_ct     = ContentType.objects.get_for_model
        ct_orga    = get_ct(Organisation)
        ct_contact = get_ct(Contact)

        subject_pred = 'employs (test version)'
        self.assertFalse(RelationType.objects.filter(predicate=subject_pred))

        response = self.client.post(self.ADD_URL,
                                    data={'subject_predicate':  subject_pred,
                                          'object_predicate':   'is employed by (test version)',
                                          'subject_ctypes':     [ct_orga.id],
                                          'subject_properties': [pt_sub.id],
                                          'object_ctypes':      [ct_contact.id],
                                          'object_properties':  [pt_obj.id],
                                         }
                                   )
        self.assertNoFormError(response)

        rel_type = self.get_object_or_fail(RelationType, predicate=subject_pred)
        self.assertEqual([ct_orga.id],    [ct.id for ct in rel_type.subject_ctypes.all()])
        self.assertEqual([ct_contact.id], [ct.id for ct in rel_type.object_ctypes.all()])
        self.assertEqual([pt_sub.id],     [pt.id for pt in rel_type.subject_properties.all()])
        self.assertEqual([pt_obj.id],     [pt.id for pt in rel_type.object_properties.all()])

    def test_edit01(self):
        rt = RelationType.create(('test-subfoo', 'subject_predicate'),
                                 ('test-objfoo', 'object_predicate'),
                                 is_custom=False
                                )[0]
        self.assertGET404(self._build_edit_url(rt))

    def test_edit02(self):
        rt = RelationType.create(('test-subfoo', 'subject_predicate'),
                                 ('test-objfoo', 'object_predicate'),
                                 is_custom=True
                                )[0]
        url = self._build_edit_url(rt)
        self.assertGET200(url)

        subject_pred = 'loves'
        object_pred  = 'is loved by'
        response = self.client.post(url, data={'subject_predicate': subject_pred,
                                               'object_predicate':  object_pred,
                                              }
                                   )
        self.assertNoFormError(response)

        rel_type = RelationType.objects.get(pk=rt.id)
        self.assertEqual(subject_pred, rel_type.predicate)
        self.assertEqual(object_pred,  rel_type.symmetric_type.predicate)

    def test_delete01(self):
        rt = RelationType.create(('test-subfoo', 'subject_predicate'),
                                 ('test-subfoo', 'object_predicate'),
                                 is_custom=False
                                )[0]
        self.assertGET404(self.DEL_URL, data={'id': rt.id})

    def test_delete02(self):
        rt, srt = RelationType.create(('test-subfoo', 'subject_predicate'),
                                      ('test-subfoo', 'object_predicate'),
                                      is_custom=True
                                     )
        self.assertPOST200(self.DEL_URL, data={'id': rt.id})
        self.assertDoesNotExist(rt)
        self.assertDoesNotExist(srt)


class SemiFixedRelationTypeTestCase(CremeTestCase):
    ADD_URL = '/creme_config/relation_type/semi_fixed/add/'
    format_str = '{"rtype": "%s", "ctype": %s,"entity": %s}'

    @classmethod
    def setUpClass(cls):
        CremeTestCase.setUpClass()
        cls.populate('creme_core')

    def setUp(self):
        self.login()

        self.loves = RelationType.create(('test-subject_foobar', 'is loving'),
                                         ('test-object_foobar',  'is loved by')
                                        )[0]

        self.iori = Contact.objects.create(user=self.user, first_name='Iori', last_name='Yoshizuki')

    def test_create01(self):
        url = self.ADD_URL
        self.assertGET200(url)

        predicate = 'Is loving Iori'
        response = self.client.post(url, data={'predicate':     predicate,
                                               'semi_relation': self.format_str % (
                                                                    self.loves.id,
                                                                    self.iori.entity_type_id,
                                                                    self.iori.id,
                                                                   ),
                                              }
                                   )
        self.assertNoFormError(response)

        semi_fixed_relations = SemiFixedRelationType.objects.all()
        self.assertEqual(1, len(semi_fixed_relations))

        smr = semi_fixed_relations[0]
        self.assertEqual(predicate,  smr.predicate)
        self.assertEqual(self.loves, smr.relation_type)
        self.assertEqual(self.iori,  smr.object_entity.get_real_entity())

    def test_create02(self):
        "Predicate is unique"
        predicate = 'Is loving Iori'
        SemiFixedRelationType.objects.create(predicate=predicate,
                                             relation_type=self.loves,
                                             object_entity=self.iori,
                                            )

        itsuki = Contact.objects.create(user=self.user, first_name='Itsuki', last_name='Akiba')
        response = self.assertPOST200(self.ADD_URL,
                                      data={'predicate':     predicate,
                                            'semi_relation': self.format_str % (
                                                                    self.loves.id,
                                                                    itsuki.entity_type_id,
                                                                    itsuki.id,
                                                                ),
                                            }
                                     )
        self.assertFormError(response, 'form', 'predicate',
                             _(u"%(model_name)s with this %(field_label)s already exists.") %  {
                                    'model_name': _('Semi-fixed type of relationship'),
                                    'field_label': _('Predicate'),
                                }
                            )

    def test_create03(self):
        "('relation_type', 'object_entity') => unique together"
        predicate = 'Is loving Iori'
        SemiFixedRelationType.objects.create(predicate=predicate,
                                             relation_type=self.loves,
                                             object_entity=self.iori,
                                            )

        url = self.ADD_URL
        predicate += ' (other)'
        response = self.assertPOST200(url, data={'predicate': predicate})
        self.assertFormError(response, 'form', 'semi_relation', [_(u"This field is required.")])

        response = self.assertPOST200(url, data={'predicate':     predicate,
                                                 'semi_relation': self.format_str % (
                                                                        self.loves.id,
                                                                        self.iori.entity_type_id,
                                                                        self.iori.id,
                                                                    ),
                                              }
                                     )
        self.assertFormError(response, 'form', None,
                             _(u"A semi-fixed type of relationship with this type and this object already exists.")
                            )

    def test_delete(self):
        sfrt = SemiFixedRelationType.objects.create(predicate='Is loving Iori',
                                                    relation_type=self.loves,
                                                    object_entity=self.iori,
                                                   )
        self.assertPOST200('/creme_config/relation_type/semi_fixed/delete',
                           data={'id': sfrt.id}
                          )
        self.assertDoesNotExist(sfrt)