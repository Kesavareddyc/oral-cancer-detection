# OralCancerDetectionBackend/detector_api/urls.py
from django.urls import path
from . import views # Import views from the current app (detector_api)

urlpatterns = [
    path('predict/', views.predict_image, name='predict'),
    path('signup/', views.signup, name='signup'), 
    path('login/', views.login_view, name='login'),#
    # This path maps 'predict/' to the predict_image function in views.py
    # So, the full URL will be something like http://127.0.0.1:8000/api/predict/
    # path('predict/', views.predict_image, name='predict_image'),
]