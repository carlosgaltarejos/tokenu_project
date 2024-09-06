from django.urls import path
from .views import home, TokenizeFileView, upload_file_form, view_token_form, show_wallet, view_token, verify_contract

urlpatterns = [
    path('', home, name='home'),
    path('upload/', upload_file_form, name='upload-file-form'),
    path('tokenize/', TokenizeFileView.as_view(), name='tokenize-file'),
    path('view-token-form/', view_token_form, name='view-token-form'),
    path('show-wallet/', show_wallet, name='show-wallet'),
    path('view-token/', view_token, name='view-token'),
    path('verify-contract/', verify_contract, name='verify_contract'),
]