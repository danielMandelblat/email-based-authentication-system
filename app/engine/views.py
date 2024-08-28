from django.shortcuts import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Email, Log, Authentication


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def home(request):
    interfaces = {
        'start/': {
            'description': 'start authentication process by sending email',
            'method': 'POST',
            'parameters:': 'email=<email address>'
        },
        'auth/': {
            'description': 'Check if the sent code is successfully authenticated with the email',
            'method': 'POST',
            'parameters:': 'email=<email address>, code=<sent code>'
        },
    }

    return JsonResponse(
        interfaces
    )

@csrf_exempt
def start(request):
    if request.method == "POST":
        status = False

        # Make validations
        if 'email' not in request.POST:
            message = 'Please send <email> inside the POST request!'
        elif "@" not in request.POST['email']:
            message = f"Email ({request.POST['email']}) is not valid email!"
        else:
            try:
                # Get email object
                email, created = Email.objects.get_or_create(email=request.POST['email'])

                # Create new auth object
                auth = Authentication.objects.create(email=email, ip_address=get_client_ip(request))
                auth.generate()
                auth.send_email()

                status = True
                message = f"Authentication code will be send to ({request.POST['email']}) email address."
            except Exception as e:
                message = str(e)

        Log.objects.create(
            message=f"status: {status}, {message}",
            ip_address=get_client_ip(request)
        )

        return JsonResponse({
            "status": status,
            'message': message
        })

    return HttpResponse("Only Post request is valid!")

@csrf_exempt
def auth(request):
    if request.method != 'POST':
        return HttpResponse("Only Post requests are valid!")

    email = request.POST.get('email')
    code = request.POST.get('code')

    status = False

    try:
        Email.auth(email=email, code=code)
        message = f"Authentication for email ({email}) completed successfully!"
        status = True
    except Exception as e:
        message = str(e)

    Log.objects.create(
        message=f"status: {status}, {message}",
        ip_address=get_client_ip(request)
    )

    return JsonResponse({
        'status': status,
        'message': message
    })