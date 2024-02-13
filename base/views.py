from django.http import JsonResponse
from django.shortcuts import render
# Import custom logic functions
from .logic import answer_query, build_database, database_exists
import threading


def index(request):
    """
    The main view that handles user queries and displays the chat interface.

    - If the request method is POST, it means the user has submitted a query.
      We then process this query through our chatbot logic and return the answer as JSON.
    - If the request method is not POST (e.g., GET), we simply render the chat interface
      without any initial chatbot response.
    """
    if request.method == 'POST':
        # Extract the user's query from the POST data.
        query = request.POST.get('query')
        # Process the query using the chatbot logic defined in `logic.py`.
        result = answer_query(query)
        # Return the chatbot's response as JSON.
        return JsonResponse(result)
    # For non-POST requests, render the chat interface template.
    return render(request, 'base/index.html')


def db_status(request):
    """
    A view to check the status of the database.

    Returns a JSON response indicating whether the database exists and is ready to be queried.
    This is useful for the frontend to decide whether to allow the user to submit queries
    or to show a loading/wait message while the database is being prepared.
    """
    # Check if the database exists using the `database_exists` function from `logic.py`.
    exists = database_exists()
    # Prepare the status message based on the existence of the database.
    status = {
        'exists': exists,
        'message': 'Database exists' if exists else 'Database is being built'
    }
    # Return the status as a JSON response.
    return JsonResponse(status)


def build_db(request):
    """
    A view to initiate the asynchronous building of the database.

    This view starts a new thread to build the database using the `build_database` function
    from `logic.py`, allowing the web server to continue handling other requests.
    This is particularly useful for initial setup or updating the database without downtime.
    """
    # Start a new thread to build the database asynchronously.
    thread = threading.Thread(target=build_database)
    thread.start()
    # Inform the requester that the database building process has started.
    return JsonResponse({'status': 'Building database...'})
