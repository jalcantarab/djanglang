from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from .logic import answer_query, build_database  # Import your logic functions here

def index(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        result = answer_query(query)
        # result = {}
        return JsonResponse(result)
    build_database()  # Build the database when the page is first loaded
    return render(request, 'base/index.html')