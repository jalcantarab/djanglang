from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from .logic import answer_query, build_database, database_exists  # Import your logic functions here
import threading

def index(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        result = answer_query(query)
        return JsonResponse(result)
    return render(request, 'base/index.html')

def db_status(request):
    status = {
        'exists': database_exists(),
        'message': 'Database exists' if database_exists() else 'Database is being built'
    }
    return JsonResponse(status)

def build_db(request):
    # Use threading to build the database asynchronously
    thread = threading.Thread(target=build_database)
    thread.start()
    return JsonResponse({'status': 'Building database...'})


