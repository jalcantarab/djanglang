from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from .logic import answer_query, build_database, database_exists, initiate_db_creation  # Import your logic functions here
import threading

def index(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        result = answer_query(query)
        return JsonResponse(result)
    return render(request, 'base/index.html')

def new_db(request):
    return render(request, 'base/create_db_form.html')

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

# Addons
def create_db_form(request):
    return render(request, 'base/create_db_form.html')

def create_db(request):
    if request.method == 'POST':
        db_name = request.POST.get('dbName')
        source_url = request.POST.get('sourceUrl')
        
        # Call the function to initiate the database creation process
        success, message = initiate_db_creation(db_name, source_url)
        
        if success:
            return JsonResponse({"status": "success", "message": message})
        else:
            return JsonResponse({"status": "error", "message": message}, status=400)
    else:
        return HttpResponse("Method not allowed", status=405)


