from django.urls import path
from . import views

app_name = 'manage'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('site-settings/', views.site_settings_edit, name='site_settings'),

    path('bookings/', views.booking_list, name='bookings'),
    path('bookings/<int:pk>/', views.booking_detail, name='booking_detail'),

    path('orders/', views.order_list, name='orders'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),

    path('inquiries/', views.inquiry_list, name='inquiries'),
    path('inquiries/<int:pk>/toggle/', views.inquiry_toggle_resolved, name='inquiry_toggle'),

    path('reviews/', views.review_list, name='reviews'),
    path('reviews/<int:pk>/delete/', views.review_delete, name='review_delete'),

    path('newsletter/', views.newsletter_list, name='newsletter'),
    path('newsletter/<int:pk>/delete/', views.newsletter_delete, name='newsletter_delete'),

    path('staff-emails/', views.staff_email_list, name='staff_emails'),
    path('staff-emails/add/', views.staff_email_add, name='staff_email_add'),
    path('staff-emails/<str:email>/delete/', views.staff_email_delete, name='staff_email_delete'),
    path('staff-emails/<str:email>/reset-password/', views.staff_email_reset_password, name='staff_email_reset_password'),

    path('account/', views.my_account, name='account'),

    path('staff-users/', views.staff_user_list, name='staff_users'),
    path('staff-users/<int:pk>/permissions/', views.staff_user_permissions, name='staff_user_permissions'),
    path('staff-users/<int:pk>/reset-password/', views.staff_user_reset_password, name='staff_user_reset_password'),

    path('<slug:slug>/', views.list_view, name='list'),
    path('<slug:slug>/add/', views.add_view, name='add'),
    path('<slug:slug>/<int:pk>/edit/', views.edit_view, name='edit'),
    path('<slug:slug>/<int:pk>/delete/', views.delete_view, name='delete'),
]
