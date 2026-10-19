from django.contrib import admin
from django.contrib.auth import logout
from django.shortcuts import render
from django.urls import include, path

from juegos.views import GameListView, home


def websocket_test_view(request):
    return render(request, 'websocket_test.html')


def logout_view(request):
    logout(request)
    return render(request, 'accounts/logged_out.html')


def custom_404(request, exception):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)


handler404 = 'ludix.urls.custom_404'
handler500 = 'ludix.urls.custom_500'


urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('logout/', logout_view, name='logout'),
    path('api/games/', GameListView.as_view(), name='game_list'),
    path('api/juegos/', GameListView.as_view()),
    path('accounts/', include('accounts.urls')),
    path('library/', include('library.urls')),
    path('wishlist/', include('wishlist.urls')),
    path('orders/', include('orders.urls')),
    path('recommendations/', include('recommendations.urls')),
    path('websocket-test/', websocket_test_view, name='websocket_test'),
]
