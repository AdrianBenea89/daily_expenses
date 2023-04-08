from django.core.mail import send_mail


def send_email():
    message = 'http://0.0.0.0.8000/statistics/'
    send_mail('Weekly statistics',
              f'Please visit {message}.',
              'tv.home.ap56@gmail.com',
              ['adrian.benea@bytex.ro'], fail_silently=False)