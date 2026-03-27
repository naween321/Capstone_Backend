from django.urls import path

from apps.aliases.api.views.alias_lookup import AliasLookupView
from apps.aliases.api.views.categorize_all import CategorizeAllView
from apps.aliases.api.views.donation import (
    DonationApproveView,
    DonationListView,
    DonationRejectView,
)
from apps.aliases.api.views.instance_register import RegisterInstanceView
from apps.aliases.api.views.preferences import UserPreferenceView
from apps.aliases.api.views.store_aliases import (
    StoreAliasDetailView,
    StoreAliasListCreateView,
)

urlpatterns = [
    path('instances/register/', RegisterInstanceView.as_view(), name='instance_register'),
    path('lookup/', AliasLookupView.as_view(), name='alias_lookup'),
    path('stores/', StoreAliasListCreateView.as_view(), name='store_alias_list'),
    path('stores/<int:pk>/', StoreAliasDetailView.as_view(), name='store_alias_detail'),
    path('categorize-all/', CategorizeAllView.as_view(), name='categorize_all'),
    path('donations/', DonationListView.as_view(), name='donation_list'),
    path('donations/<int:pk>/approve/', DonationApproveView.as_view(), name='donation_approve'),
    path('donations/<int:pk>/reject/', DonationRejectView.as_view(), name='donation_reject'),
    path('preferences/', UserPreferenceView.as_view(), name='alias_preferences'),
]
