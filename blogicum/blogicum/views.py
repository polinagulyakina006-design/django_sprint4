from django.shortcuts import render

def custom_404(request, exception=None):
    return render(request, 'pages/404.html', status=404)

def custom_500(request):
    return render(request, 'pages/500.html', status=500)

def custom_403(request, exception=None):
    return render(request, 'pages/403.html', status=403)