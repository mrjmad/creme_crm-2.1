# -*- coding: utf-8 -*-

try:
    from os import path as os_path
    from tempfile import NamedTemporaryFile

    from django.utils.encoding import force_unicode
    from django.utils.translation import ugettext as _
    from django.conf import settings
    from django.contrib.contenttypes.models import ContentType

    from creme_core.tests.base import CremeTestCase
    from creme_core.models import Relation, RelationType
    from creme_core.models import Relation, RelationType, SetCredentials

    from media_managers.models import Image

    from persons.models import Contact, Organisation, Address, Civility
    from persons.constants import *

    from vcfs import vcf_lib
    from vcfs.forms import vcf
except Exception as e:
    print 'Error in <%s>: %s' % (__name__, e)


class VcfsTestCase(CremeTestCase):
    def _build_filedata(self, content_str):
        tmpfile = NamedTemporaryFile()
        tmpfile.write(content_str)
        tmpfile.flush()

        filedata = tmpfile.file
        filedata.seek(0)

        return tmpfile

    def _post_form_step_0(self, url, file):
        return self.client.post(url, follow=True,
                                data={'user':     self.user,
                                      'vcf_step': 0,
                                      'vcf_file': file,
                                     }
                                )

class VcfTestCase(VcfsTestCase):
    @classmethod
    def setUpClass(cls):
        cls.populate('creme_core', 'creme_config')
    #def setUp(self):
        #self.populate('creme_core', 'creme_config')

    def test_add_vcf(self):
        self.login()

        url = '/vcfs/vcf'
        self.assertEqual(200, self.client.get(url).status_code)

        content  = """BEGIN:VCARD\nFN:Test\nEND:VCARD"""
        filedata = self._build_filedata(content)
        response = self._post_form_step_0(url, filedata.file)

        self.assertNoFormError(response)
        self.assertEqual(200, response.status_code)

        #try:
        with self.assertNoException():
            form = response.context['form']
        #except Exception as e:
            #self.fail(str(e))

        self.assertIn('value="1"', unicode(form['vcf_step']))

    def test_parsing_vcf00(self):
        self.login()

        content  = """BEGIN:VCARD\nFN:Prénom Nom\nEND:VCARD"""
        filedata = self._build_filedata(content)
        response = self._post_form_step_0('/vcfs/vcf', filedata.file)

        #try:
        with self.assertNoException():
            form = response.context['form']
        #except Exception as e:
            #self.fail(str(e))

        self.assertIn('value="1"', unicode(form['vcf_step']))

        firt_name, sep, last_name = vcf_lib.readOne(content).fn.value.partition(' ')
        self.assertEqual(form['first_name'].field.initial, firt_name)
        self.assertEqual(form['last_name'].field.initial,  last_name)

    def test_parsing_vcf01(self):
        self.login()

        content  = """BEGIN:VCARD\nN:Nom;Prénom;;Civilité;\nTITLE:Directeur adjoint\nADR;TYPE=HOME:Numéro de rue;;Nom de rue;Ville;Région;Code postal;Pays\nTEL;TYPE=HOME:00 00 00 00 00\nTEL;TYPE=CELL:11 11 11 11 11\nTEL;TYPE=FAX:22 22 22 22 22\nEMAIL;TYPE=HOME:email@email.com\nURL;TYPE=HOME:www.my-website.com\nEND:VCARD"""
        filedata = self._build_filedata(content)
        response = self._post_form_step_0('/vcfs/vcf', filedata.file)

        #try:
        with self.assertNoException():
            form = response.context['form']
        #except Exception as e:
            #self.fail(str(e))

        vobj = vcf_lib.readOne(content)
        n_value = vobj.n.value

        self.assertEqual(form['civility'].field.help_text, ''.join([_(u'Read in VCF File : '), n_value.prefix]))
        self.assertEqual(form['first_name'].field.initial, n_value.given)
        self.assertEqual(form['last_name'].field.initial,  n_value.family)

        tel = vobj.contents['tel']
        self.assertEqual(form['phone'].field.initial,  tel[0].value)
        self.assertEqual(form['mobile'].field.initial, tel[1].value)
        self.assertEqual(form['fax'].field.initial,    tel[2].value)

        self.assertEqual(form['position'].field.help_text, ''.join([_(u'Read in VCF File : '), vobj.title.value]))
        self.assertEqual(form['email'].field.initial,       vobj.email.value)
        self.assertEqual(form['url_site'].field.initial,    vobj.url.value)

        adr_value = vobj.adr.value
        self.assertEqual(form['adr_last_name'].field.initial, n_value.family)
        self.assertEqual(form['address'].field.initial,       ' '.join([adr_value.box, adr_value.street]))
        self.assertEqual(form['city'].field.initial,          adr_value.city)
        self.assertEqual(form['country'].field.initial,       adr_value.country)
        self.assertEqual(form['code'].field.initial,          adr_value.code)
        self.assertEqual(form['region'].field.initial,        adr_value.region)

    def test_parsing_vcf02(self):
        self.login()

        content  = """BEGIN:VCARD\nFN:Prénom Nom\nORG:Corporate\nADR;TYPE=WORK:Numéro de rue;;Nom de la rue;Ville;Region;Code Postal;Pays\nTEL;TYPE=WORK:00 00 00 00 00\nEMAIL;TYPE=WORK:corp@corp.com\nURL;TYPE=WORK:www.corp.com\nEND:VCARD"""
        filedata = self._build_filedata(content)
        response = self._post_form_step_0('/vcfs/vcf', filedata.file)

        #try:
        with self.assertNoException():
            form = response.context['form']
        #except Exception as e:
            #self.fail(str(e))

        vobj = vcf_lib.readOne(content)
        self.assertEqual(form['work_name'].field.initial,     vobj.org.value[0])
        self.assertEqual(form['work_phone'].field.initial,    vobj.tel.value)
        self.assertEqual(form['work_email'].field.initial,    vobj.email.value)
        self.assertEqual(form['work_url_site'].field.initial, vobj.url.value)
        self.assertEqual(form['work_adr_name'].field.initial, vobj.org.value[0])
        self.assertEqual(form['work_address'].field.initial,  ' '.join([vobj.adr.value.box, vobj.adr.value.street]))
        self.assertEqual(form['work_city'].field.initial,     vobj.adr.value.city)
        self.assertEqual(form['work_region'].field.initial,   vobj.adr.value.region)
        self.assertEqual(form['work_code'].field.initial,     vobj.adr.value.code)
        self.assertEqual(form['work_country'].field.initial,  vobj.adr.value.country)

    def test_parsing_vcf03(self):
        self.login()

        content  = """BEGIN:VCARD\nFN:Prénom Nom\nADR:Numéro de rue;;Nom de la rue;Ville;Région;Code Postal;Pays\nTEL:00 00 00 00 00\nEMAIL:email@email.com\nURL:www.url.com\nEND:VCARD"""
        filedata = self._build_filedata(content)
        response = self._post_form_step_0('/vcfs/vcf', filedata.file)

        #try:
        with self.assertNoException():
            form = response.context['form']
        #except Exception as e:
            #self.fail(str(e))

        vobj = vcf_lib.readOne(content)
        help_prefix = _(u'Read in VCF File without type : ')
        adr_value = vobj.adr.value
        adr = ', '.join([adr_value.box, adr_value.street, adr_value.city, adr_value.region, adr_value.code, adr_value.country])
        self.assertEqual(form['address'].field.help_text,  ''.join([help_prefix, adr]))
        self.assertEqual(form['phone'].field.help_text,    ''.join([help_prefix, vobj.tel.value]))
        self.assertEqual(form['email'].field.help_text,    ''.join([help_prefix, vobj.email.value]))
        self.assertEqual(form['url_site'].field.help_text, ''.join([help_prefix, vobj.url.value]))

    def test_parsing_vcf04(self):
        self.login()

        orga = Organisation.objects.create(user=self.user, name='Corporate')
        content  = """BEGIN:VCARD\nN:Prénom Nom\nORG:Corporate\nADR;TYPE=WORK:Numéro de rue;;Nom de la rue;Ville;Region;Code Postal;Pays\nTEL;TYPE=WORK:11 11 11 11 11\nEMAIL;TYPE=WORK:email@email.com\nURL;TYPE=WORK:www.web-site.com\nEND:VCARD"""
        filedata = self._build_filedata(content)
        response = self._post_form_step_0('/vcfs/vcf', filedata.file)

        #try:
        with self.assertNoException():
            form = response.context['form']
        #except Exception as e:
            #self.fail(str(e))

        self.assertEqual(form['organisation'].field.initial, orga.id)


class ContactTestCase(VcfsTestCase):
    @classmethod
    def setUpClass(cls):
        cls.populate('creme_core', 'creme_config', 'persons')
    #def setUp(self):
        #self.populate('creme_core', 'creme_config', 'persons')

    def _assertFormOK(self, response):
        self.assertNoFormError(response)
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.redirect_chain)
        self.assertEqual(1, len(response.redirect_chain))

    def test_add_contact_vcf00(self):
        self.login()

        contact_count = Contact.objects.count()
        orga_count    = Organisation.objects.count()
        address_count = Address.objects.count()

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nTEL;TYPE=HOME:00 00 00 00 00\nTEL;TYPE=CELL:11 11 11 11 11\nTEL;TYPE=FAX:22 22 22 22 22\nEMAIL;TYPE=HOME:email@email.com\nURL;TYPE=HOME:http://www.url.com/\nEND:VCARD"""
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial
        phone      = form['phone'].field.initial
        mobile     = form['mobile'].field.initial
        fax        = form['fax'].field.initial
        email      = form['email'].field.initial
        url_site   = form['url_site'].field.initial
        self.assertIn('value="1"', unicode(form['vcf_step']))

        response = self.client.post(url, follow=True,
                                    data={'user':        user,
                                          'vcf_step':    1,
                                          'first_name':  first_name,
                                          'last_name':   last_name,
                                          'phone':       phone,
                                          'mobile':      mobile,
                                          'fax':         fax,
                                          'email':       email,
                                          'url_site':    url_site,
                                          'create_or_attach_orga': False,
                                         }
                                    )
        self._assertFormOK(response)
        self.assertEqual(contact_count + 1, Contact.objects.count())
        self.assertEqual(orga_count,        Organisation.objects.count())
        self.assertEqual(address_count,     Address.objects.count())

        try:
            Contact.objects.get(first_name=first_name, last_name=last_name, phone=phone,
                                mobile=mobile, fax=fax, email=email, url_site=url_site
                               )
        except Exception as e:
            self.fail(str(e) + str(Contact.objects.all()))

    def test_add_contact_vcf01(self):
        self.login()

        contact_count = Contact.objects.count()
        orga_count    = Organisation.objects.count()

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nTEL;TYPE=HOME:00 00 00 00 00\nTEL;TYPE=CELL:11 11 11 11 11\nTEL;TYPE=FAX:22 22 22 22 22\nEMAIL;TYPE=HOME:email@email.com\nURL;TYPE=HOME:www.url.com\nEND:VCARD"""
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial
        phone      = form['phone'].field.initial
        mobile     = form['mobile'].field.initial
        fax        = form['fax'].field.initial
        email      = form['email'].field.initial
        url_site   = form['url_site'].field.initial
        response = self.client.post(url, follow=True,
                                    data={'user':        user,
                                          'vcf_step':    1,
                                          'first_name':  first_name,
                                          'last_name':   last_name,
                                          'phone':       phone,
                                          'mobile':      mobile,
                                          'fax':         fax,
                                          'email':       email,
                                          'url_site':    url_site,
                                          'create_or_attach_orga': True,
                                         }
                                    )
        validation_text = _(u'Required, if you want to create organisation')
        self.assertFormError(response, 'form', 'work_name', validation_text)
        self.assertFormError(response, 'form', 'relation',  validation_text)
        self.assertEqual(contact_count, Contact.objects.count())
        self.assertEqual(orga_count,    Organisation.objects.count())

    def test_add_contact_vcf02(self):
        self.login()

        contact_count = Contact.objects.count()
        orga_count    = Organisation.objects.count()

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nTEL;TYPE=HOME:00 00 00 00 00\nTEL;TYPE=CELL:11 11 11 11 11\nTEL;TYPE=FAX:22 22 22 22 22\nTEL;TYPE=WORK:33 33 33 33 33\nEMAIL;TYPE=HOME:email@email.com\nEMAIL;TYPE=WORK:work@work.com\nURL;TYPE=HOME:http://www.url.com/\nURL;TYPE=WORK:www.work.com\nORG:Corporate\nEND:VCARD"""
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial
        phone      = form['phone'].field.initial
        mobile     = form['mobile'].field.initial
        fax        = form['fax'].field.initial
        email      = form['email'].field.initial
        url_site   = form['url_site'].field.initial

        work_name     = form['work_name'].field.initial
        work_phone    = form['work_phone'].field.initial
        work_email    = form['work_email'].field.initial
        work_url_site = form['work_url_site'].field.initial
        response = self.client.post(url, follow=True,
                                    data={'user':          user,
                                          'vcf_step':      1,
                                          'first_name':    first_name,
                                          'last_name':     last_name,
                                          'phone':         phone,
                                          'mobile':        mobile,
                                          'fax':           fax,
                                          'email':         email,
                                          'url_site':      url_site,
                                          'create_or_attach_orga': False,
                                          'work_name':     work_name,
                                          'work_phone':    work_phone,
                                          'work_email':    work_email,
                                          'work_url_site': work_url_site,
                                         }
                                    )
        self._assertFormOK(response)
        self.assertEqual(contact_count + 1, Contact.objects.count())
        self.assertEqual(orga_count,        Organisation.objects.count())

        self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name, phone=phone,
                                mobile=mobile, fax=fax, email=email, url_site=url_site
                               )

    def test_add_contact_vcf03(self):
        self.login()

        contact_count = Contact.objects.count()
        orga_count    = Organisation.objects.count()

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nTEL;TYPE=HOME:00 00 00 00 00\nTEL;TYPE=CELL:11 11 11 11 11\nTEL;TYPE=FAX:22 22 22 22 22\nTEL;TYPE=WORK:33 33 33 33 33\nEMAIL;TYPE=HOME:email@email.com\nEMAIL;TYPE=WORK:work@work.com\nURL;TYPE=HOME:www.url.com\nURL;TYPE=WORK:http://www.work.com/\nORG:Corporate\nEND:VCARD"""
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial
        phone      = form['phone'].field.initial
        mobile     = form['mobile'].field.initial
        fax        = form['fax'].field.initial
        email      = form['email'].field.initial
        url_site   = form['url_site'].field.initial

        work_name     = form['work_name'].field.initial
        work_phone    = form['work_phone'].field.initial
        work_email    = form['work_email'].field.initial
        work_url_site = form['work_url_site'].field.initial

        response = self.client.post(url, follow=True,
                                    data={'user':          user,
                                          'vcf_step':      1,
                                          'first_name':    first_name,
                                          'last_name':     last_name,
                                          'phone':         phone,
                                          'mobile':        mobile,
                                          'fax':           fax,
                                          'email':         email,
                                          'url_site':      url_site,
                                          'create_or_attach_orga': True,
                                          'relation':      REL_SUB_EMPLOYED_BY,
                                          'work_name':     work_name,
                                          'work_phone':    work_phone,
                                          'work_email':    work_email,
                                          'work_url_site': work_url_site,
                                         }
                                    )
        self._assertFormOK(response)

        self.assertEqual(contact_count + 1, Contact.objects.count())
        self.assertEqual(orga_count + 1,    Organisation.objects.count())

        orga = self.get_object_or_fail(Organisation, name=work_name, phone=work_phone, email=work_email, url_site=work_url_site)
        contact = self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name, phone=phone, mobile=mobile, fax=fax, email=email)
        self.assertRelationCount(1, contact, REL_SUB_EMPLOYED_BY, orga)

    def test_add_contact_vcf04(self):
        self.login()

        contact_count = Contact.objects.count()
        orga_count = Organisation.objects.count()
        orga = Organisation.objects.create(user=self.user, name='Corporate', phone='33 33 33 33 33', email='work@work.com', url_site='www.work.com')
        self.assertEqual(orga_count + 1, Organisation.objects.count())

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nTEL;TYPE=HOME:00 00 00 00 00\nTEL;TYPE=CELL:11 11 11 11 11\nTEL;TYPE=FAX:22 22 22 22 22\nTEL;TYPE=WORK:33 33 33 33 33\nEMAIL;TYPE=HOME:email@email.com\nEMAIL;TYPE=WORK:work@work.com\nURL;TYPE=HOME:www.url.com\nURL;TYPE=WORK:www.work.com\nORG:Corporate\nEND:VCARD"""
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial
        phone      = form['phone'].field.initial
        mobile     = form['mobile'].field.initial
        fax        = form['fax'].field.initial
        email      = form['email'].field.initial
        url_site   = form['url_site'].field.initial

        orga_id       = form['organisation'].field.initial
        work_name     = form['work_name'].field.initial
        work_phone    = form['work_phone'].field.initial
        work_email    = form['work_email'].field.initial
        work_url_site = form['work_url_site'].field.initial

        response = self.client.post(url, follow=True,
                                    data={'user':          user,
                                          'vcf_step':      1,
                                          'first_name':    first_name,
                                          'last_name':     last_name,
                                          'phone':         phone,
                                          'mobile':        mobile,
                                          'fax':           fax,
                                          'email':         email,
                                          'url_site':      url_site,
                                          'create_or_attach_orga': True,
                                          'organisation':  orga_id,
                                          'relation':      REL_SUB_EMPLOYED_BY,
                                          'work_name':     work_name,
                                          'work_phone':    work_phone,
                                          'work_email':    work_email,
                                          'work_url_site': work_url_site,
                                         }
                                    )
        self._assertFormOK(response)
        self.assertEqual(contact_count + 1, Contact.objects.count())
        self.assertEqual(orga_count + 1,    Organisation.objects.count())

        contact = self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name, phone=phone, mobile=mobile, fax=fax, email=email)
        self.assertRelationCount(1, contact, REL_SUB_EMPLOYED_BY, orga)

    def test_add_contact_vcf05(self):
        self.login()

        contact_count = Contact.objects.count()
        address_count = Address.objects.count()

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nADR;TYPE=HOME:Numéro de rue;;Nom de rue;Ville;Région;Code postal;Pays\nTEL;TYPE=HOME:00 00 00 00 00\nTEL;TYPE=CELL:11 11 11 11 11\nTEL;TYPE=FAX:22 22 22 22 22\nEMAIL;TYPE=HOME:email@email.com\nURL;TYPE=HOME:www.url.com\nEND:VCARD"""
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial
        phone      = form['phone'].field.initial
        mobile     = form['mobile'].field.initial
        fax        = form['fax'].field.initial
        email      = form['email'].field.initial
        url_site   = form['url_site'].field.initial

        adr_last_name = form['adr_last_name'].field.initial
        address       = form['address'].field.initial
        city          = form['city'].field.initial
        country       = form['country'].field.initial
        code          = form['code'].field.initial
        region        = form['region'].field.initial

        response = self.client.post(url, follow=True,
                                    data={'user':          user,
                                          'vcf_step':      1,
                                          'first_name':    first_name,
                                          'last_name':     last_name,
                                          'phone':         phone,
                                          'mobile':        mobile,
                                          'fax':           fax,
                                          'email':         email,
                                          'url_site':      url_site,
                                          'adr_last_name': adr_last_name,
                                          'address':       address,
                                          'city':          city,
                                          'country':       country,
                                          'code':          code,
                                          'region':        region,
                                          'create_or_attach_orga': False,
                                         }
                                    )
        self._assertFormOK(response)

        self.assertEqual(contact_count + 1, Contact.objects.count())
        self.assertEqual(address_count + 1, Address.objects.count())

        contact = self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name, phone=phone, mobile=mobile, fax=fax, email=email)
        address = self.get_object_or_fail(Address, name=adr_last_name, address=address, city=city, zipcode=code, country=country, department=region)

        self.assertEqual(contact.billing_address, address)

    def test_add_contact_vcf06(self):
        self.login()

        contact_count = Contact.objects.count()
        address_count = Address.objects.count()
        orga_count    = Organisation.objects.count()

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nADR;TYPE=HOME:Numéro de rue;;Nom de rue;Ville;Région;Code postal;Pays\nADR;TYPE=WORK:Orga Numéro de rue;;Orga Nom de rue;Orga Ville;Orga Région;Orga Code postal;Orga Pays\nTEL;TYPE=HOME:00 00 00 00 00\nTEL;TYPE=CELL:11 11 11 11 11\nTEL;TYPE=FAX:22 22 22 22 22\nTEL;TYPE=WORK:33 33 33 33 33\nEMAIL;TYPE=HOME:email@email.com\nEMAIL;TYPE=WORK:work@work.com\nURL;TYPE=HOME:www.url.com\nURL;TYPE=WORK:www.work.com\nORG:Corporate\nEND:VCARD"""
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial
        phone      = form['phone'].field.initial
        mobile     = form['mobile'].field.initial
        fax        = form['fax'].field.initial
        email      = form['email'].field.initial
        url_site   = form['url_site'].field.initial

        adr_last_name = form['adr_last_name'].field.initial
        address       = form['address'].field.initial
        city          = form['city'].field.initial
        country       = form['country'].field.initial
        code          = form['code'].field.initial
        region        = form['region'].field.initial

        work_name      = form['work_name'].field.initial
        work_adr_name  = form['work_adr_name'].field.initial
        work_address   = form['work_address'].field.initial
        work_city      = form['work_city'].field.initial
        work_country   = form['work_country'].field.initial
        work_code      = form['work_code'].field.initial
        work_region    = form['work_region'].field.initial

        response = self.client.post(url, follow=True,
                                    data={'user':          user,
                                          'vcf_step':      1,
                                          'first_name':    first_name,
                                          'last_name':     last_name,
                                          'phone':         phone,
                                          'mobile':        mobile,
                                          'fax':           fax,
                                          'email':         email,
                                          'url_site':      url_site,
                                          'adr_last_name': adr_last_name,
                                          'address':       address,
                                          'city':          city,
                                          'country':       country,
                                          'code':          code,
                                          'region':        region,
                                          'create_or_attach_orga': True,
                                          'relation':      REL_SUB_EMPLOYED_BY,
                                          'work_name':     work_name,
                                          'work_adr_name': work_adr_name,
                                          'work_address':  work_address,
                                          'work_city':     work_city,
                                          'work_country':  work_country,
                                          'work_code':     work_code,
                                          'work_region':   work_region,
                                         }
                                    )
        self._assertFormOK(response)

        self.assertEqual(contact_count + 1, Contact.objects.count())
        self.assertEqual(orga_count + 1,    Organisation.objects.count())
        self.assertEqual(address_count + 2, Address.objects.count())

        contact         = self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name, phone=phone, mobile=mobile, fax=fax, email=email)
        orga            = self.get_object_or_fail(Organisation, name=work_name)
        address_contact = self.get_object_or_fail(Address, name=adr_last_name, address=address, city=city, zipcode=code, country=country, department=region)
        address_orga    = self.get_object_or_fail(Address, name=work_adr_name, address=work_address, city=work_city, zipcode=work_code, country=work_country, department=work_region)

        self.assertEqual(contact.billing_address, address_contact)
        self.assertEqual(orga.billing_address,    address_orga)

    def test_add_contact_vcf07(self):
        self.login()

        contact_count = Contact.objects.count()

        Organisation.objects.create(user=self.user, name='Corporate', phone='00 00 00 00 00', email='corp@corp.com', url_site='www.corp.com')
        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nADR;TYPE=WORK:Orga Numéro de rue;;Orga Nom de rue;Orga Ville;Orga Région;Orga Code postal;Orga Pays\nTEL;TYPE=WORK:11 11 11 11 11\nEMAIL;TYPE=WORK:work@work.com\nURL;TYPE=WORK:www.work.com\nORG:Corporate\nEND:VCARD"""
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial

        orga_id       = form['organisation'].field.initial
        work_name     = form['work_name'].field.initial
        work_phone    = form['work_phone'].field.initial
        work_email    = form['work_email'].field.initial
        work_url_site = form['work_url_site'].field.initial

        work_adr_name  = form['work_adr_name'].field.initial
        work_address   = form['work_address'].field.initial
        work_city      = form['work_city'].field.initial
        work_country   = form['work_country'].field.initial
        work_code      = form['work_code'].field.initial
        work_region    = form['work_region'].field.initial

        response = self.client.post(url,
                                    follow=True,
                                    data={'user':                 user,
                                          'vcf_step':             1,
                                          'first_name':           first_name,
                                          'last_name':            last_name,
                                          'create_or_attach_orga': False,
                                          'organisation':         orga_id,
                                          'relation':             REL_SUB_EMPLOYED_BY,
                                          'work_name':            work_name,
                                          'work_phone':           work_phone,
                                          'work_email':           work_email,
                                          'work_url_site':        work_url_site,
                                          'work_adr_name':        work_adr_name,
                                          'work_address':         work_address,
                                          'work_city':            work_city,
                                          'work_country':         work_country,
                                          'work_code':            work_code,
                                          'work_region':          work_region,
                                          'update_orga_name':     True,
                                          'update_orga_phone':    True,
                                          'update_orga_email':    True,
                                          'update_orga_fax':      True,
                                          'update_orga_url_site': True,
                                          'update_orga_address':  True,
                                         }
                                    )
        validation_text = _(u'Create organisation not checked')
        self.assertFormError(response, 'form', 'update_orga_name',     validation_text)
        self.assertFormError(response, 'form', 'update_orga_phone',    validation_text)
        self.assertFormError(response, 'form', 'update_orga_email',    validation_text)
        self.assertFormError(response, 'form', 'update_orga_fax',      validation_text)
        self.assertFormError(response, 'form', 'update_orga_url_site', validation_text)

        self.assertEqual(contact_count, Contact.objects.count())

    def test_add_contact_vcf08(self):
        self.login()

        contact_count = Contact.objects.count()

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nADR;TYPE=WORK:Orga Numéro de rue;;Orga Nom de rue;Orga Ville;Orga Région;Orga Code postal;Orga Pays\nTEL;TYPE=WORK:11 11 11 11 11\nEMAIL;TYPE=WORK:work@work.com\nURL;TYPE=WORK:www.work.com\nORG:Corporate\nEND:VCARD"""
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial

        work_name     = form['work_name'].field.initial
        work_phone    = form['work_phone'].field.initial
        work_email    = form['work_email'].field.initial
        work_url_site = form['work_url_site'].field.initial

        work_adr_name  = form['work_adr_name'].field.initial
        work_address   = form['work_address'].field.initial
        work_city      = form['work_city'].field.initial
        work_country   = form['work_country'].field.initial
        work_code      = form['work_code'].field.initial
        work_region    = form['work_region'].field.initial

        response = self.client.post(url, follow=True,
                                    data={'user':                 user,
                                          'vcf_step':             1,
                                          'first_name':           first_name,
                                          'last_name':            last_name,
                                          'create_or_attach_orga': True,
                                          'relation':             REL_SUB_EMPLOYED_BY,
                                          'work_name':            work_name,
                                          'work_phone':           work_phone,
                                          'work_email':           work_email,
                                          'work_url_site':        work_url_site,
                                          'work_adr_name':        work_adr_name,
                                          'work_address':         work_address,
                                          'work_city':            work_city,
                                          'work_country':         work_country,
                                          'work_code':            work_code,
                                          'work_region':          work_region,
                                          'update_orga_name':     True,
                                          'update_orga_phone':    True,
                                          'update_orga_email':    True,
                                          'update_orga_fax':      True,
                                          'update_orga_url_site': True,
                                          'update_orga_address':  True,
                                         }
                                    )
        validation_text = _(u'Organisation not selected')
        self.assertFormError(response, 'form', 'update_orga_name',     validation_text)
        self.assertFormError(response, 'form', 'update_orga_phone',    validation_text)
        self.assertFormError(response, 'form', 'update_orga_email',    validation_text)
        self.assertFormError(response, 'form', 'update_orga_fax',      validation_text)
        self.assertFormError(response, 'form', 'update_orga_url_site', validation_text)
        self.assertFormError(response, 'form', 'update_orga_address',  validation_text)

        self.assertEqual(contact_count, Contact.objects.count())

    def test_add_contact_vcf09(self):
        self.login()

        Organisation.objects.create(user=self.user, name='Corporate', phone='00 00 00 00 00', email='corp@corp.com', url_site='www.corp.com')

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nORG:Corporate\nEND:VCARD"""
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial

        orga_id = form['organisation'].field.initial

        response = self.client.post(url, follow=True,
                                    data={'user':                 user,
                                          'vcf_step':             1,
                                          'first_name':           first_name,
                                          'last_name':            last_name,
                                          'create_or_attach_orga': True,
                                          'organisation':         orga_id,
                                          'relation':             REL_SUB_EMPLOYED_BY,
                                          'update_orga_name':     True,
                                          'update_orga_phone':    True,
                                          'update_orga_fax':      True,
                                          'update_orga_email':    True,
                                          'update_orga_url_site': True,
                                          'update_orga_address':  True,
                                         }
                                    )
        validation_text = _(u'Required, if you want to update organisation')
        self.assertFormError(response, 'form', 'work_phone',    validation_text)
        self.assertFormError(response, 'form', 'work_email',    validation_text)
        self.assertFormError(response, 'form', 'work_fax',      validation_text)
        self.assertFormError(response, 'form', 'work_url_site', validation_text)

    def test_add_contact_vcf10(self):
        self.login()

        orga = Organisation.objects.create(user=self.user, name='Corporate', phone='00 00 00 00 00', email='corp@corp.com', url_site='www.corp.com')
        orga.billing_address = Address.objects.create(name='Org_name',
                                                      address='Org_address',
                                                      city='Org_city',
                                                      country='Org_country',
                                                      zipcode='Org_zipcode',
                                                      department='Org_department',
                                                      content_type_id=ContentType.objects.get_for_model(Organisation).id,
                                                      object_id=orga.id,
                                                     )
        orga.save()

        contact_count = Contact.objects.count()
        orga_count    = Organisation.objects.count()
        address_count = Address.objects.count()

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nADR;TYPE=WORK:Orga Numéro de rue;;Orga Nom de rue;Orga Ville;Orga Région;Orga Code postal;Orga Pays\nTEL;TYPE=WORK:11 11 11 11 11\nEMAIL;TYPE=WORK:work@work.com\nURL;TYPE=WORK:www.work.com\nORG:Corporate\nEND:VCARD"""
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial

        orga_id       = form['organisation'].field.initial
        work_name     = form['work_name'].field.initial
        work_phone    = form['work_phone'].field.initial
        work_email    = form['work_email'].field.initial
        work_url_site = form['work_url_site'].field.initial

        work_adr_name  = form['work_adr_name'].field.initial
        work_address   = form['work_address'].field.initial
        work_city      = form['work_city'].field.initial
        work_country   = form['work_country'].field.initial
        work_code      = form['work_code'].field.initial
        work_region    = form['work_region'].field.initial

        response = self.client.post(url, follow=True,
                                    data={'user':                 user,
                                          'vcf_step':             1,
                                          'first_name':           first_name,
                                          'last_name':            last_name,
                                          'create_or_attach_orga': True,
                                          'organisation':         orga_id,
                                          'relation':             REL_SUB_EMPLOYED_BY,
                                          'work_name':            work_name,
                                          'work_phone':           work_phone,
                                          'work_email':           work_email,
                                          'work_url_site':        work_url_site,
                                          'work_adr_name':        work_adr_name,
                                          'work_address':         work_address,
                                          'work_city':            work_city,
                                          'work_country':         work_country,
                                          'work_code':            work_code,
                                          'work_region':          work_region,
                                          'update_orga_name':     True,
                                          'update_orga_phone':    True,
                                          'update_orga_email':    True,
                                          'update_orga_url_site': True,
                                          'update_orga_address':  True,
                                         }
                                    )
        self._assertFormOK(response)

        self.assertEqual(contact_count + 1, Contact.objects.count())
        self.assertEqual(orga_count,        Organisation.objects.count())
        self.assertEqual(address_count,     Address.objects.count())

        orga = self.refresh(orga)
        billing_address = orga.billing_address

        vobj = vcf_lib.readOne(content)
        adr = vobj.adr.value
        org = vobj.org.value[0]
        self.assertEqual(orga.name,                  org)
        self.assertEqual(orga.phone,                 vobj.tel.value)
        self.assertEqual(orga.email,                 vobj.email.value)
        self.assertEqual(orga.url_site,              'http://www.work.com/')
        self.assertEqual(billing_address.name,       org)
        self.assertEqual(billing_address.address,    ' '.join([adr.box, adr.street]))
        self.assertEqual(billing_address.city,       adr.city)
        self.assertEqual(billing_address.country,    adr.country)
        self.assertEqual(billing_address.zipcode,    adr.code)
        self.assertEqual(billing_address.department, adr.region)

    def test_add_contact_vcf11(self):
        self.login()

        Organisation.objects.create(user=self.user, name='Corporate', phone='00 00 00 00 00', email='corp@corp.com', url_site='www.corp.com')

        contact_count = Contact.objects.count()
        orga_count    = Organisation.objects.count()
        address_count = Address.objects.count()

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nADR;TYPE=WORK:Orga Numéro de rue;;Orga Nom de rue;Orga Ville;Orga Région;Orga Code postal;Orga Pays\nORG:Corporate\nEND:VCARD"""
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial

        orga_id       = form['organisation'].field.initial

        work_name     = form['work_name'].field.initial
        work_adr_name = form['work_adr_name'].field.initial
        work_address  = form['work_address'].field.initial
        work_city     = form['work_city'].field.initial
        work_country  = form['work_country'].field.initial
        work_code     = form['work_code'].field.initial
        work_region   = form['work_region'].field.initial

        response = self.client.post(url, follow=True,
                                    data={'user':                 user,
                                          'vcf_step':             1,
                                          'first_name':           first_name,
                                          'last_name':            last_name,
                                          'create_or_attach_orga': True,
                                          'organisation':         orga_id,
                                          'relation':             REL_SUB_EMPLOYED_BY,
                                          'work_name':            work_name,
                                          'work_adr_name':        work_adr_name,
                                          'work_address':         work_address,
                                          'work_city':            work_city,
                                          'work_country':         work_country,
                                          'work_code':            work_code,
                                          'work_region':          work_region,
                                          'update_orga_address':  True,
                                         }
                                    )
        self._assertFormOK(response)

        self.assertEqual(contact_count + 1, Contact.objects.count())
        self.assertEqual(orga_count,        Organisation.objects.count())
        self.assertEqual(address_count + 1, Address.objects.count())

        address = self.get_object_or_fail(Address, name=work_adr_name, address=work_address, city=work_city, zipcode=work_code, country=work_country, department=work_region)
        orga    = self.get_object_or_fail(Organisation, id=orga_id)

        vobj = vcf_lib.readOne(content)
        adr = vobj.adr.value

        self.assertEqual(address.name,       vobj.org.value[0])
        self.assertEqual(address.address,    ' '.join([adr.box, adr.street]))
        self.assertEqual(address.city,       adr.city)
        self.assertEqual(address.country,    adr.country)
        self.assertEqual(address.zipcode,    adr.code)
        self.assertEqual(address.department, adr.region)

        self.assertEqual(orga.billing_address, address)

    def test_add_contact_vcf12(self):
        self.login()

        contact_count = Contact.objects.count()
        orga_count    = Organisation.objects.count()
        image_count   = Image.objects.count()
        address_count = Address.objects.count()

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nTEL;TYPE=HOME:00 00 00 00 00\nTEL;TYPE=CELL:11 11 11 11 11\nTEL;TYPE=FAX:22 22 22 22 22\nEMAIL;TYPE=HOME:email@email.com\nURL;TYPE=HOME:www.url.com\nPHOTO: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\nEND:VCARD"""
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial
        phone      = form['phone'].field.initial
        mobile     = form['mobile'].field.initial
        fax        = form['fax'].field.initial
        email      = form['email'].field.initial
        url_site   = form['url_site'].field.initial

        response = self.client.post(url, follow=True,
                                    data={'user':          user,
                                          'vcf_step':      1,
                                          'first_name':    first_name,
                                          'last_name':     last_name,
                                          'phone':         phone,
                                          'mobile':        mobile,
                                          'fax':           fax,
                                          'email':         email,
                                          'url_site':      url_site,
                                          'create_or_attach_orga': False,
                                         }
                                    )
        self._assertFormOK(response)

        self.assertEqual(contact_count + 1, Contact.objects.count())
        self.assertEqual(image_count,       Image.objects.count())
        self.assertEqual(orga_count,        Organisation.objects.count())
        self.assertEqual(address_count,     Address.objects.count())

        # url_site='http://www.url.com/' and not url_site=url_site because URLField add 'http://' and '/'
        self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name, phone=phone, mobile=mobile, fax=fax, email=email, url_site='http://www.url.com/')

    def test_add_contact_vcf13(self):
        self.login()

        contact_count = Contact.objects.count()
        content  = 'BEGIN:VCARD\nN;ENCODING=8BIT:HUDARD;Jean;;%(civility)s;\nTITLE:%(position)s\nEND:VCARD' % {
                            'civility': _('Mr.'),
                            'position': _('CEO'),
                        }
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        with self.assertNoException():
            form = response.context['form']
            user_id     = form.fields['user'].initial
            first_name  = form.fields['first_name'].initial
            last_name   = form.fields['last_name'].initial
            civility_id = form.fields['civility'].initial
            position_id = form.fields['position'].initial

        self.assertEqual(self.user.id, user_id)
        self.assertEqual('Jean', first_name)
        self.assertEqual('HUDARD', last_name)
        self.assertEqual(3, civility_id) #pk=3 see persons.populate
        self.assertEqual(1, position_id) #pk=1 idem

        response = self.client.post(url, follow=True,
                                    data={'user':       user_id,
                                          'vcf_step':   1,
                                          'first_name': first_name,
                                          'last_name':  last_name,
                                          'civility':   civility_id,
                                          'position':   position_id,
                                         }
                                    )
        self._assertFormOK(response)
        self.assertEqual(contact_count + 1, Contact.objects.count())
        self.get_object_or_fail(Contact, civility=civility_id, first_name=first_name, last_name=last_name, position=position_id)

    def test_add_contact_vcf14(self):
        self.login()

        contact_count = Contact.objects.count()
        orga_count    = Organisation.objects.count()
        image_count   = Image.objects.count()
        address_count = Address.objects.count()

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nPHOTO;TYPE=JPEG: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\nEND:VCARD"""
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial
        image      = form['image_encoded'].field.initial

        response = self.client.post(url, follow=True,
                                    data={'user':          user,
                                          'vcf_step':      1,
                                          'first_name':    first_name,
                                          'last_name':     last_name,
                                          'create_or_attach_orga': False,
                                          'image_encoded': image,
                                         }
                                    )
        self._assertFormOK(response)

        self.assertEqual(contact_count + 1, Contact.objects.count())
        self.assertEqual(image_count + 1,   Image.objects.count())
        self.assertEqual(orga_count,        Organisation.objects.count())
        self.assertEqual(address_count,     Address.objects.count())


        contact = self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name)
        self.assertTrue(contact.image)
        self.assertEqual(_(u'Image of %s') % contact, contact.image.name)
        contact.image.image.delete()

    def test_add_contact_vcf15(self):
        self.login()

        vcf.URL_START = vcf.URL_START + ('file',)

        path_base = os_path.join(settings.CREME_ROOT, 'static', 'chantilly', 'images', '500.png')
        self.assert_(os_path.exists(path_base))
        path = 'file:///' + os_path.normpath(path_base)

        contact_count = Contact.objects.count()
        #image_count   = Image.objects.count()
        self.assertEqual(0, Image.objects.count())

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nPHOTO;VALUE=URL:%s\nEND:VCARD""" % path
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial
        enc_image  = form['image_encoded'].field.initial

        response = self.client.post(url, follow=True,
                                    data={'user':          user,
                                          'vcf_step':      1,
                                          'first_name':    first_name,
                                          'last_name':     last_name,
                                          'image_encoded': enc_image,
                                         }
                                    )
        self._assertFormOK(response)

        self.assertEqual(contact_count + 1, Contact.objects.count())
        #self.assertEqual(image_count + 1,   Image.objects.count())

        contact = self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name)

        images = Image.objects.all()
        self.assertEqual(1, len(images))

        image = images[0]
        self.assertEqual(image,                       contact.image)
        self.assertEqual(_(u'Image of %s') % contact, image.name)
        image.delete()

    def test_add_contact_vcf16(self):
        self.login()

        contact_count = Contact.objects.count()
        image_count   = Image.objects.count()

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nPHOTO;VALUE=URL:http://wwwwwwwww.wwwwwwwww.wwwwwwww/wwwwwww.jpg\nEND:VCARD"""
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial
        image      = form['image_encoded'].field.initial

        response = self.client.post(url, follow=True,
                                    data={'user':          user,
                                          'vcf_step':      1,
                                          'first_name':    first_name,
                                          'last_name':     last_name,
                                          'image_encoded': image,
                                         }
                                    )
        self._assertFormOK(response)

        self.assertEqual(contact_count + 1, Contact.objects.count())
        self.assertEqual(image_count,       Image.objects.count())

    def test_add_contact_vcf17(self):
        self.login()

        settings.VCF_IMAGE_MAX_SIZE = 10240 #(10 kB)
        vcf.URL_START = vcf.URL_START + ('file',)

        path_base = os_path.join(settings.CREME_ROOT, 'static', 'images', '500.png')
        path = 'file:///' + os_path.normpath(path_base)

        contact_count = Contact.objects.count()
        image_count   = Image.objects.count()

        content  = """BEGIN:VCARD\nFN:Jean HUDARD\nPHOTO;VALUE=URL:%s\nEND:VCARD""" % path
        filedata = self._build_filedata(content)

        url = '/vcfs/vcf'
        response = self._post_form_step_0(url, filedata.file)

        form = response.context['form']
        user       = form['user'].field.initial
        first_name = form['first_name'].field.initial
        last_name  = form['last_name'].field.initial
        image      = form['image_encoded'].field.initial

        response = self.client.post(url, follow=True,
                                    data={'user':          user,
                                          'vcf_step':      1,
                                          'first_name':    first_name,
                                          'last_name':     last_name,
                                          'image_encoded': image,
                                         }
                                    )
        self._assertFormOK(response)

        self.assertEqual(contact_count + 1, Contact.objects.count())
        self.assertEqual(image_count,       Image.objects.count())


class VcfExportTestCase(VcfsTestCase):
    @classmethod
    def setUpClass(cls):
        cls.populate('creme_core', 'creme_config', 'persons')

    def create_contact(self):
        return Contact.objects.create(user=self.user,
                                      last_name='Abitbol',
                                      first_name='George',
                                      phone='0404040404',
                                      mobile='0606060606',
                                      fax='0505050505',
                                      email='a@aa.fr',
                                      url_site='www.aaa.fr',
                                     )

    def create_address(self, contact, prefix):
        return Address.objects.create(address='%s_address' % prefix,
                                      city='%s_city' % prefix,
                                      po_box='%s_po_box' % prefix,
                                      country='%s_country' % prefix,
                                      zipcode='%s_zipcode' % prefix,
                                      department='%s_department' % prefix,
                                      content_type_id=ContentType.objects.get_for_model(Contact).id,
                                      object_id=contact.id,
                                     )

    def test_get_empty_vcf(self):
        self.login()
        contact = Contact.objects.create(user=self.user, last_name='Abitbol')

        response = self.client.get('/vcfs/%s/generate_vcf' % contact.id)
        self.assertEqual(200, response.status_code)
        self.assertEqual("""BEGIN:VCARD\r\nVERSION:3.0\r\nFN: Abitbol\r\nN:Abitbol;;;;\r\nEND:VCARD\r\n""",
                         response.content
                        )

    def test_get_vcf_basic_role(self):
        self.login(is_superuser=False, allowed_apps=('creme_core', 'persons', 'vcfs'), creatable_models=[Contact])
        user = self.user

        SetCredentials.objects.create(role=self.role,
                                      value=SetCredentials.CRED_CHANGE | SetCredentials.CRED_DELETE | \
                                            SetCredentials.CRED_LINK   | SetCredentials.CRED_UNLINK, #  no CRED_VIEW
                                      set_type=SetCredentials.ESET_ALL
                                     )

        contact = Contact.objects.create(user=self.other_user, last_name='Abitbol')
        self.assertTrue(contact.can_change(user))
        self.assertFalse(contact.can_view(user))

        response = self.client.get('/vcfs/%s/generate_vcf' % contact.id)
        self.assertEqual(403, response.status_code)

    def test_get_vcf_civility(self):
        self.login()
        contact = Contact.objects.create(user=self.user,
                                         civility=Civility.objects.create(title='Monsieur'),
                                         last_name='Abitbol'
                                        )

        response = self.client.get('/vcfs/%s/generate_vcf' % contact.id)
        self.assertEqual(200, response.status_code)
        self.assertEqual("""BEGIN:VCARD\r\nVERSION:3.0\r\nFN: Abitbol\r\nN:Abitbol;;;Monsieur;\r\nEND:VCARD\r\n""",
                         response.content
                        )

    def test_get_vcf_org(self):
        self.login()
        contact = Contact.objects.create(user=self.user, last_name='Abitbol')
        orga = Organisation.objects.create(user=self.user, name='ORGNAME')

        rtype = RelationType.objects.get(pk=REL_OBJ_EMPLOYED_BY)
        rel = Relation.objects.create(type=rtype,
                                      subject_entity=orga,
                                      object_entity=contact,
                                      user=self.user,
                                      )

        response = self.client.get('/vcfs/%s/generate_vcf' % contact.id)
        self.assertEqual(200, response.status_code)
        self.assertEqual("""BEGIN:VCARD\r\nVERSION:3.0\r\nFN: Abitbol\r\nN:Abitbol;;;;\r\nORG:ORGNAME\r\nEND:VCARD\r\n""",
                         response.content
                        )

    def test_get_vcf_billing_addr(self):
        self.login()
        contact = self.create_contact()
        contact.civility = Civility.objects.create(title='Mr')
        contact.billing_address = self.create_address(contact, "Org")
        contact.save()

        response = self.client.get('/vcfs/%s/generate_vcf' % contact.id)
        self.assertEqual(200, response.status_code)
        self.assertEqual("""BEGIN:VCARD\r\nVERSION:3.0\r\nADR:Org_po_box;;Org_address;Org_city;Org_department;Org_zipcode;Org_countr\r\n y\r\nTEL;TYPE=CELL:0606060606\r\nEMAIL;TYPE=INTERNET:a@aa.fr\r\nTEL;TYPE=FAX:0505050505\r\nFN:George Abitbol\r\nN:Abitbol;George;;Mr;\r\nTEL;TYPE=WORK:0404040404\r\nURL:www.aaa.fr\r\nEND:VCARD\r\n""",
                         response.content
                        )

    def test_get_vcf_shipping_addr(self):
        self.login()
        contact = self.create_contact()
        contact.civility = Civility.objects.create(title='Mr')
        contact.shipping_address = self.create_address(contact, "Org")
        contact.save()

        response = self.client.get('/vcfs/%s/generate_vcf' % contact.id)
        self.assertEqual(200, response.status_code)
        self.assertEqual("""BEGIN:VCARD\r\nVERSION:3.0\r\nADR:Org_po_box;;Org_address;Org_city;Org_department;Org_zipcode;Org_countr\r\n y\r\nTEL;TYPE=CELL:0606060606\r\nEMAIL;TYPE=INTERNET:a@aa.fr\r\nTEL;TYPE=FAX:0505050505\r\nFN:George Abitbol\r\nN:Abitbol;George;;Mr;\r\nTEL;TYPE=WORK:0404040404\r\nURL:www.aaa.fr\r\nEND:VCARD\r\n""",
                         response.content
                        )

    def test_get_vcf_both_addr(self):
        self.login()
        contact = self.create_contact()
        contact.civility = Civility.objects.create(title='Mr')
        contact.shipping_address = self.create_address(contact, "shipping")
        contact.billing_address = self.create_address(contact, "billing")
        contact.save()

        response = self.client.get('/vcfs/%s/generate_vcf' % contact.id)
        self.assertEqual(200, response.status_code)
        self.assertEqual("""BEGIN:VCARD\r\nVERSION:3.0\r\nADR:shipping_po_box;;shipping_address;shipping_city;shipping_department;sh\r\n ipping_zipcode;shipping_country\r\nADR:billing_po_box;;billing_address;billing_city;billing_department;billin\r\n g_zipcode;billing_country\r\nTEL;TYPE=CELL:0606060606\r\nEMAIL;TYPE=INTERNET:a@aa.fr\r\nTEL;TYPE=FAX:0505050505\r\nFN:George Abitbol\r\nN:Abitbol;George;;Mr;\r\nTEL;TYPE=WORK:0404040404\r\nURL:www.aaa.fr\r\nEND:VCARD\r\n""",
                        response.content)

    def test_get_vcf_addr_eq(self):
        self.login()
        contact = self.create_contact()
        contact.civility = Civility.objects.create(title='Mr')
        contact.shipping_address = self.create_address(contact, "Org")
        contact.billing_address = self.create_address(contact, "Org")
        contact.save()
        other_address = self.create_address(contact, "Org")

        response = self.client.get('/vcfs/%s/generate_vcf' % contact.id)
        self.assertEqual(200, response.status_code)
        self.assertEqual("""BEGIN:VCARD\r\nVERSION:3.0\r\nADR:Org_po_box;;Org_address;Org_city;Org_department;Org_zipcode;Org_countr\r\n y\r\nTEL;TYPE=CELL:0606060606\r\nEMAIL;TYPE=INTERNET:a@aa.fr\r\nTEL;TYPE=FAX:0505050505\r\nFN:George Abitbol\r\nN:Abitbol;George;;Mr;\r\nTEL;TYPE=WORK:0404040404\r\nURL:www.aaa.fr\r\nEND:VCARD\r\n""",
                        response.content
                       )

    def test_person(self):
        self.login()
        contact = self.create_contact()
        contact.civility = Civility.objects.create(title='Mr')
        contact.shipping_address = self.create_address(contact, "shipping")
        contact.billing_address = self.create_address(contact, "billing")
        contact.save()
        other_address = self.create_address(contact, "Org")

        response = self.client.get('/vcfs/%s/generate_vcf' % contact.id)
        self.assertEqual(200, response.status_code)
        self.assertEqual("""BEGIN:VCARD\r\nVERSION:3.0\r\nADR:shipping_po_box;;shipping_address;shipping_city;shipping_department;sh\r\n ipping_zipcode;shipping_country\r\nADR:billing_po_box;;billing_address;billing_city;billing_department;billin\r\n g_zipcode;billing_country\r\nADR:Org_po_box;;Org_address;Org_city;Org_department;Org_zipcode;Org_countr\r\n y\r\nTEL;TYPE=CELL:0606060606\r\nEMAIL;TYPE=INTERNET:a@aa.fr\r\nTEL;TYPE=FAX:0505050505\r\nFN:George Abitbol\r\nN:Abitbol;George;;Mr;\r\nTEL;TYPE=WORK:0404040404\r\nURL:www.aaa.fr\r\nEND:VCARD\r\n""",
                         response.content
                        )
