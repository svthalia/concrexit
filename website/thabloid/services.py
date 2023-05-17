from thabloid.models import ThabloidUser


def update_thabloid_blacklist_for_user(form, instance, commit, *args, **kwargs):
    if form.cleaned_data["receive_thabloid"]:
        ThabloidUser.objects.get(pk=instance.user.pk).allow_thabloid()
    else:
        ThabloidUser.objects.get(pk=instance.user.pk).disallow_thabloid()
