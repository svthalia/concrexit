from django.urls import path, include

from . import views

app_name = "members"

urlpatterns = [
    path('iban-export/', views.iban_export,
         name='iban-export'),
    path('members/', include([
        path('', views.index,
             name='index'),
        path('statistics/', views.statistics,
             name='statistics'),
        path('profile/<int:pk>', views.profile,
             name='profile'),
    ])),
    path('user/', include([
        path('', views.user,
             name='user'),
        path('edit-profile/', views.edit_profile,
             name='edit-profile'),
        path('change-email/', views.EmailChangeFormView.as_view(),
             name='email-change'),
        path('change-email/verify/<uuid:key>/',
             views.EmailChangeVerifyView.as_view(),
             name='email-change-verify'),
        path('change-email/confirm/<uuid:key>/',
             views.EmailChangeConfirmView.as_view(),
             name='email-change-confirm'),
    ])),
]
