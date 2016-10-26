from django.conf import settings
from django.http import (JsonResponse, HttpResponseBadRequest,
                         HttpResponseForbidden)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate
from django.contrib.staticfiles.finders import find as find_static_file
from django.core.cache import cache
from thaliapp.models import Token
from hashlib import sha256
import base64
import datetime


def get_photo(user):
    if user.member.photo:
        photo = ''.join(['data:image/jpeg;base64,',
                         base64.b64encode(
                             user.member.photo.file.read()).decode()
                         ])
    else:
        filename = find_static_file('members/images/default-avatar.jpg')
        with open(filename, 'rb') as f:
            photo = ''.join(['data:image/jpeg;base64,',
                             base64.b64encode(f.read()).decode()
                             ])
    return photo


@csrf_exempt
@require_POST
def login(request):
    if (sha256(request.POST.get('apikey', '').encode('ascii')).hexdigest() !=
            settings.THALIAPP_API_KEY):
        return HttpResponseForbidden()
    user = request.POST.get('username')
    password = request.POST.get('password')
    if user is None or password is None:
        return HttpResponseBadRequest(
            '{"status":"error","msg":"Missing username or password"}',
            content_type='application/json')
    user = authenticate(username=user, password=password)
    if user is not None:
        token = Token.create_token(user)
        photo = get_photo(user)
        return JsonResponse({'status': 'ok',
                             'username': user.username,
                             'token': token,
                             'profile_image': photo,
                             })
    return JsonResponse({'status': 'error',
                         'msg': 'Authentication Failed'},
                        status_code=403)


@csrf_exempt
@require_POST
def app(request):
    username = request.POST.get('username')
    token = request.POST.get('token')
    if (sha256(request.POST.get('apikey', '').encode('ascii')).hexdigest() !=
            settings.WOLKTM_API_KEY):
        return HttpResponseForbidden()
    if username is None or token is None:
        return HttpResponseBadRequest()
    user = Token.authenticate(username, token)
    if user is None:
        return JsonResponse({'status': 'error',
                            'msg': 'Authentication Failed'},
                            status_code=403)
    today = datetime.date.today()
    eightteen_years_ago = today.replace(year=today.year - 18)
    over18 = str(user.member.birthday <= eightteen_years_ago)
    membership = user.member.current_membership
    if membership:
        membership_type = membership.type
        is_member = 'True'
    else:
        membership_type = 'Expired'
        is_member = 'False'
    return JsonResponse({'status': 'ok',
                         'real_name': user.member.get_full_name(),
                         'display_name': user.member.display_name(),
                         'birthday': str(user.member.birthday),
                         'over18': over18,
                         'membership_type': membership_type,
                         'is_thalia_member': is_member,
                         'profile_image': get_photo(user),
                         })


@csrf_exempt
@require_POST
def scan(request):
    """Not used until wolktm is deprecated"""
    username = request.POST.get('username')
    token = request.POST.get('token')
    qrtoken = request.POST.get('qrToken')
    if username is None or token is None or qrtoken is None:
        return HttpResponseBadRequest()
    user = Token.authenticate(username, token)
    if user is None:
        return JsonResponse({'status': 'error',
                            'msg': 'Authentication Failed'},
                            status_code=403)
    cache.set(''.join([qrtoken]), user, 300)
    return JsonResponse({'status': 'ok'})
