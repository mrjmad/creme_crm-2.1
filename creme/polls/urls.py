# -*- coding: utf-8 -*-

from django.conf.urls import url, include

from creme.creme_core.conf.urls import Swappable, swap_manager

from creme import polls
from .views import campaign, poll_form, poll_reply


urlpatterns = [
    url(r'^poll_form/stats/(?P<pform_id>\d+)[/]?$', poll_form.Statistics.as_view(), name='polls__form_stats'),

    # Form lines
    url(r'^poll_form/(?P<pform_id>\d+)/add/line[/]?$',        poll_form.LineCreation.as_view(),      name='polls__create_form_line'),
    url(r'^pform_line/(?P<line_id>\d+)/edit[/]?$',            poll_form.LineEdition.as_view(),       name='polls__edit_form_line'),
    url(r'^pform_line/(?P<line_id>\d+)/disable[/]?$',         poll_form.disable_line,                name='polls__disable_form_line'),
    url(r'^pform_line/(?P<line_id>\d+)/conditions/edit[/]?$', poll_form.ConditionsEdition.as_view(), name='polls__edit_form_line_conditions'),
    url(r'^pform_line/(?P<line_id>\d+)/choices[/]?$',         poll_form.get_choices,                 name='polls__form_line_choices'),

    # Form section
    url(r'^poll_form/(?P<pform_id>\d+)/add/section[/]?$',     poll_form.SectionCreation.as_view(),      name='polls__create_form_section'),
    url(r'^pform_section/(?P<section_id>\d+)/edit[/]?$',      poll_form.SectionEdition.as_view(),       name='polls__edit_form_section'),
    url(r'^pform_section/(?P<section_id>\d+)/add/child[/]?$', poll_form.ChildSectionCreation.as_view(), name='polls__create_child_form_section'),
    url(r'^pform_section/(?P<section_id>\d+)/add/line[/]?$',  poll_form.AddingLineToSection.as_view(),  name='polls__create_form_line_in_section'),

    # Replies
    url(r'^poll_reply/fill/(?P<preply_id>\d+)[/]?$',           poll_reply.fill,           name='polls__fill_reply'),
    url(r'^poll_reply/clean[/]?$',                             poll_reply.clean,          name='polls__clean_reply'),
    url(r'^poll_reply/link_to_person/(?P<person_id>\d+)[/]?$',
        poll_reply.LinkingRepliesToPerson.as_view(),
        name='polls__link_reply_to_person',
    ),

    url(r'^poll_reply/(?P<preply_id>\d+)/line/(?P<line_id>\d+)/', include([
        url(r'^edit[/]?$',        poll_reply.LineEdition.as_view(), name='polls__edit_reply_line'),
        url(r'^edit_wizard[/]?$', poll_reply.edit_line_wizard,      name='polls__edit_reply_line_wizard'),
    ]))
]

urlpatterns += swap_manager.add_group(
    polls.pollcampaign_model_is_custom,
    # Swappable(url(r'^campaigns[/]?$',                          campaign.listview,                       name='polls__list_campaigns')),
    Swappable(url(r'^campaigns[/]?$',                          campaign.PollCampaignsList.as_view(),    name='polls__list_campaigns')),
    Swappable(url(r'^campaign/add[/]?$',                       campaign.PollCampaignCreation.as_view(), name='polls__create_campaign')),
    Swappable(url(r'^campaign/edit/(?P<campaign_id>\d+)[/]?$', campaign.PollCampaignEdition.as_view(),  name='polls__edit_campaign'), check_args=Swappable.INT_ID),
    Swappable(url(r'^campaign/(?P<campaign_id>\d+)[/]?$',      campaign.PollCampaignDetail.as_view(),   name='polls__view_campaign'), check_args=Swappable.INT_ID),
    app_name='polls',
).kept_patterns()

urlpatterns += swap_manager.add_group(
    polls.pollform_model_is_custom,
    # Swappable(url(r'^poll_forms[/]?$',                       poll_form.listview,                   name='polls__list_forms')),
    Swappable(url(r'^poll_forms[/]?$',                       poll_form.PollFormsList.as_view(),    name='polls__list_forms')),
    Swappable(url(r'^poll_form/add[/]?$',                    poll_form.PollFormCreation.as_view(), name='polls__create_form')),
    Swappable(url(r'^poll_form/edit/(?P<pform_id>\d+)[/]?$', poll_form.PollFormEdition.as_view(),  name='polls__edit_form'), check_args=Swappable.INT_ID),
    Swappable(url(r'^poll_form/(?P<pform_id>\d+)[/]?$',      poll_form.PollFormDetail.as_view(),   name='polls__view_form'), check_args=Swappable.INT_ID),
    app_name='polls',
).kept_patterns()

urlpatterns += swap_manager.add_group(
    polls.pollreply_model_is_custom,
    # Swappable(url(r'^poll_replies[/]?$', poll_reply.listview, name='polls__list_replies')),
    Swappable(url(r'^poll_replies[/]?$', poll_reply.PollRepliesList.as_view(), name='polls__list_replies')),

    # TODO: change url (reply->replies or add_several ??)
    Swappable(url(r'^poll_reply/add[/]?$',
                  poll_reply.PollRepliesCreation.as_view(),
                  name='polls__create_reply')
    ),
    Swappable(url(r'^poll_reply/add_from_pform/(?P<pform_id>\d+)[/]?$',
                  poll_reply.RepliesCreationFromPForm.as_view(),
                  name='polls__create_reply_from_pform',
                 ),
              check_args=Swappable.INT_ID,
             ),
    Swappable(url(r'^poll_reply/add_from_campaign/(?P<campaign_id>\d+)[/]?$',
                  poll_reply.RepliesCreationFromCampaign.as_view(),
                  name='polls__create_reply_from_campaign',
                 ),
              check_args=Swappable.INT_ID,
             ),
    Swappable(url(r'^poll_reply/add_from_person/(?P<person_id>\d+)[/]?$',
                  poll_reply.RepliesCreationFromPerson.as_view(),
                  name='polls__create_reply_from_person',
                 ),
              check_args=Swappable.INT_ID,
             ),

    Swappable(url(r'^poll_reply/edit/(?P<preply_id>\d+)[/]?$', poll_reply.PollReplyEdition.as_view(), name='polls__edit_reply'), check_args=Swappable.INT_ID),
    Swappable(url(r'^poll_reply/(?P<preply_id>\d+)[/]?$',      poll_reply.PollReplyDetail.as_view(), name='polls__view_reply'),  check_args=Swappable.INT_ID),
    app_name='polls',
).kept_patterns()
