# -*- coding: utf-8 -*-

# from django.conf.urls import url, include
from django.urls import re_path, include

from creme.creme_core.conf.urls import Swappable, swap_manager

from .. import billing
from .views import (
    convert, credit_note, invoice, export, line,
    payment_information, quote, sales_order, templatebase,
)


urlpatterns = [
    re_path(r'^generate_pdf/(?P<base_id>\d+)[/]?$', export.export_as_pdf, name='billing__export'),

    re_path(r'^payment_information/', include([
        re_path(
            r'^add/(?P<orga_id>\d+)[/]?$',
            payment_information.PaymentInformationCreation.as_view(),
            name='billing__create_payment_info',
        ),
        re_path(
            r'^add_related/(?P<entity_id>\d+)[/]?$',
            payment_information.PaymentInformationRelatedCreation.as_view(),
            name='billing__create_related_payment_info',
        ),
        re_path(
            r'^edit/(?P<pinfo_id>\d+)[/]?$',
            payment_information.PaymentInformationEdition.as_view(),
            name='billing__edit_payment_info',
        ),
        re_path(
            # r'^set_default/(?P<payment_information_id>\d+)/(?P<billing_id>\d+)[/]?$',
            r'^set_default/(?P<pinfo_id>\d+)/(?P<entity_id>\d+)[/]?$',
            # payment_information.set_default,
            payment_information.PaymentInformationAsDefault.as_view(),
            name='billing__set_default_payment_info',
        ),
    ])),

    # re_path(r'^(?P<document_id>\d+)/convert[/]?$', convert.convert, name='billing__convert'),
    re_path(r'^(?P<src_id>\d+)/convert[/]?$', convert.Conversion.as_view(), name='billing__convert'),

    re_path(r'^line/(?P<line_id>\d+)/add_to_catalog[/]*',  line.AddingToCatalog.as_view(), name='billing__add_to_catalog'),
    re_path(r'^(?P<document_id>\d+)/multi_save_lines[/]*', line.multi_save_lines,          name='billing__multi_save_lines'),

    *swap_manager.add_group(
        billing.invoice_model_is_custom,
        # Swappable(url(r'^invoices[/]?$',                                    invoice.listview,                         name='billing__list_invoices')),
        Swappable(re_path(r'^invoices[/]?$',                                    invoice.InvoicesList.as_view(),           name='billing__list_invoices')),
        Swappable(re_path(r'^invoice/add[/]?$',                                 invoice.InvoiceCreation.as_view(),        name='billing__create_invoice')),
        Swappable(re_path(r'^invoice/add/(?P<target_id>\d+)[/]?$',              invoice.RelatedInvoiceCreation.as_view(), name='billing__create_related_invoice'),  check_args=Swappable.INT_ID),
        Swappable(re_path(r'^invoice/edit/(?P<invoice_id>\d+)[/]?$',            invoice.InvoiceEdition.as_view(),         name='billing__edit_invoice'),            check_args=Swappable.INT_ID),
        Swappable(re_path(r'^invoice/generate_number/(?P<invoice_id>\d+)[/]?$', invoice.generate_number,                  name='billing__generate_invoice_number'), check_args=Swappable.INT_ID),
        Swappable(re_path(r'^invoice/(?P<invoice_id>\d+)[/]?$',                 invoice.InvoiceDetail.as_view(),          name='billing__view_invoice'),            check_args=Swappable.INT_ID),
        app_name='billing',
    ).kept_patterns(),

    *swap_manager.add_group(
        billing.quote_model_is_custom,
        # Swappable(url(r'^quotes[/]?$',                       quote.listview,                       name='billing__list_quotes')),
        Swappable(re_path(r'^quotes[/]?$',                       quote.QuotesList.as_view(),           name='billing__list_quotes')),
        Swappable(re_path(r'^quote/add[/]?$',                    quote.QuoteCreation.as_view(),        name='billing__create_quote')),
        Swappable(re_path(r'^quote/add/(?P<target_id>\d+)[/]?$', quote.RelatedQuoteCreation.as_view(), name='billing__create_related_quote'), check_args=Swappable.INT_ID),
        Swappable(re_path(r'^quote/edit/(?P<quote_id>\d+)[/]?$', quote.QuoteEdition.as_view(),         name='billing__edit_quote'),           check_args=Swappable.INT_ID),
        Swappable(re_path(r'^quote/(?P<quote_id>\d+)[/]?$',      quote.QuoteDetail.as_view(),          name='billing__view_quote'),           check_args=Swappable.INT_ID),
        app_name='billing',
    ).kept_patterns(),

    *swap_manager.add_group(
        billing.sales_order_model_is_custom,
        # Swappable(url(r'^sales_orders[/]?$',                       sales_order.listview,                            name='billing__list_orders')),
        Swappable(re_path(r'^sales_orders[/]?$',                       sales_order.SalesOrdersList.as_view(),           name='billing__list_orders')),
        Swappable(re_path(r'^sales_order/add[/]?$',                    sales_order.SalesOrderCreation.as_view(),        name='billing__create_order')),
        Swappable(re_path(r'^sales_order/add/(?P<target_id>\d+)[/]?$', sales_order.RelatedSalesOrderCreation.as_view(), name='billing__create_related_order'), check_args=Swappable.INT_ID),
        Swappable(re_path(r'^sales_order/edit/(?P<order_id>\d+)[/]?$', sales_order.SalesOrderEdition.as_view(),         name='billing__edit_order'),           check_args=Swappable.INT_ID),
        Swappable(re_path(r'^sales_order/(?P<order_id>\d+)[/]?$',      sales_order.SalesOrderDetail.as_view(),          name='billing__view_order'),           check_args=Swappable.INT_ID),
        app_name='billing',
    ).kept_patterns(),

    *swap_manager.add_group(
        billing.credit_note_model_is_custom,
        # Swappable(url(r'^credit_notes[/]?$',                                credit_note.listview,                     name='billing__list_cnotes')),
        Swappable(re_path(r'^credit_notes[/]?$',                                credit_note.CreditNotesList.as_view(),    name='billing__list_cnotes')),
        Swappable(re_path(r'^credit_note/add[/]?$',                             credit_note.CreditNoteCreation.as_view(), name='billing__create_cnote')),
        Swappable(re_path(r'^credit_note/edit/(?P<cnote_id>\d+)[/]?$',          credit_note.CreditNoteEdition.as_view(),  name='billing__edit_cnote'),         check_args=Swappable.INT_ID),
        Swappable(re_path(r'^credit_note/(?P<cnote_id>\d+)[/]?$',               credit_note.CreditNoteDetail.as_view(),   name='billing__view_cnote'),         check_args=Swappable.INT_ID),
        Swappable(re_path(r'^credit_note/editcomment/(?P<cnote_id>\d+)[/]?$',   credit_note.CommentEdition.as_view(),     name='billing__edit_cnote_comment'), check_args=Swappable.INT_ID),
        Swappable(re_path(r'^credit_note/add_related_to/(?P<base_id>\d+)[/]?$', credit_note.CreditNotesLinking.as_view(), name='billing__link_to_cnotes'),     check_args=Swappable.INT_ID),
        Swappable(re_path(r'^credit_note/delete_related/(?P<credit_note_id>\d+)/from/(?P<base_id>\d+)[/]?$',
                          # credit_note.delete_related_credit_note,
                          credit_note.CreditNoteRemoving.as_view(),
                          name='billing__delete_related_cnote',
                         ),
                  check_args=(1, 2),
                 ),
        app_name='billing',
    ).kept_patterns(),

    *swap_manager.add_group(
        billing.template_base_model_is_custom,
        # Swappable(url(r'^templates[/]?$',                          templatebase.listview,                      name='billing__list_templates')),
        Swappable(re_path(r'^templates[/]?$',                          templatebase.TemplateBasesList.as_view(),   name='billing__list_templates')),
        Swappable(re_path(r'^template/edit/(?P<template_id>\d+)[/]?$', templatebase.TemplateBaseEdition.as_view(), name='billing__edit_template'), check_args=Swappable.INT_ID),
        Swappable(re_path(r'^template/(?P<template_id>\d+)[/]?$',      templatebase.TemplateBaseDetail.as_view(),  name='billing__view_template'), check_args=Swappable.INT_ID),
        app_name='billing',
    ).kept_patterns(),

    *swap_manager.add_group(
        billing.product_line_model_is_custom,
        # Swappable(url(r'^product_lines[/]?$',                                line.listview_product_line,          name='billing__list_product_lines')),
        Swappable(re_path(r'^product_lines[/]?$',                                line.ProductLinesList.as_view(),     name='billing__list_product_lines')),
        Swappable(re_path(r'^(?P<entity_id>\d+)/product_line/add_multiple[/]?$', line.ProductLinesCreation.as_view(), name='billing__create_product_lines'), check_args=Swappable.INT_ID),
        app_name='billing',
    ).kept_patterns(),

    *swap_manager.add_group(
        billing.service_line_model_is_custom,
        # Swappable(url(r'^service_lines[/]?$',                                line.listview_service_line,          name='billing__list_service_lines')),
        Swappable(re_path(r'^service_lines[/]?$',                                line.ServiceLinesList.as_view(),     name='billing__list_service_lines')),
        Swappable(re_path(r'^(?P<entity_id>\d+)/service_line/add_multiple[/]?$', line.ServiceLinesCreation.as_view(), name='billing__create_service_lines'), check_args=Swappable.INT_ID),
        app_name='billing',
    ).kept_patterns(),
]
