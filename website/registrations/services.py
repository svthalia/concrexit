"""The services defined by the registrations package"""
import string
import unicodedata
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

import members
from members.models import Membership, Profile
from payments.models import Payment
from thaliawebsite import settings
from utils.snippets import datetime_to_lectureyear
from . import emails
from .models import Entry, Registration, Renewal


def _generate_username(registration):
    """
    Create username from first and lastname

    :param registration: Model containing first and last name
    :type registration: Registration
    :return: Created username
    :rtype: str
    """
    username = (registration.first_name[0] +
                registration.last_name).lower()
    username = ''.join(c for c in username if c.isalpha())
    username = ''.join(c for c in unicodedata.normalize('NFKD', username)
                       if c in string.ascii_letters).lower()

    # Limit length to 150 characters since Django doesn't support longer
    if len(username) > 150:
        username = username[:150]

    return username


def check_unique_user(entry):
    """
    Check that the username and email address of the entry are unique.

    :param entry: Registration entry
    :type entry: Entry
    :return: True if unique, False if not unique
    :rtype: boolean
    """
    try:
        registration = entry.registration
        username = _generate_username(registration)
        if (get_user_model().objects.filter(username=username).exists() and
                registration.username is not None):
            username = registration.username

        return not (get_user_model().objects.filter(
            Q(email=registration.email) | Q(username=username)).exists())
    except Registration.DoesNotExist:
        pass
    return True


def confirm_entry(queryset):
    """
    Confirm all entries in the queryset

    :param queryset: queryset of entries
    :type queryset: Queryset[Entry]
    :return: number of updated rows
    :rtype: integer
    """
    queryset = queryset.filter(status=Entry.STATUS_CONFIRM)
    rows_updated = queryset.update(status=Entry.STATUS_REVIEW,
                                   updated_at=timezone.now())
    return rows_updated


def reject_entries(queryset):
    """
    Reject all entries in the queryset

    :param queryset: queryset of entries
    :type queryset: Queryset[Entry]
    :return: number of updated rows
    :rtype: integer
    """
    queryset = queryset.filter(status=Entry.STATUS_REVIEW)
    entries = list(queryset.all())
    rows_updated = queryset.update(status=Entry.STATUS_REJECTED,
                                   updated_at=timezone.now())

    for entry in entries:
        try:
            emails.send_registration_rejected_message(entry.registration)
        except Registration.DoesNotExist:
            try:
                emails.send_renewal_rejected_message(entry.renewal)
            except Renewal.DoesNotExist:
                pass

    return rows_updated


def accept_entries(queryset):
    """
    Accept all entries in the queryset

    :param queryset: queryset of entries
    :type queryset: Queryset[Entry]
    :return: number of updated rows
    :rtype: integer
    """
    queryset = queryset.filter(status=Entry.STATUS_REVIEW)
    entries = queryset.all()
    updated_entries = []

    for entry in entries:
        # Check if the user is unique
        if not check_unique_user(entry):
            # User is not unique, do not proceed
            continue

        payment = _create_payment_for_entry(entry)
        try:
            if entry.registration.username is None:
                entry.registration.username = _generate_username(
                    entry.registration)
                entry.registration.save()
            emails.send_registration_accepted_message(entry.registration,
                                                      payment)
        except Registration.DoesNotExist:
            try:
                emails.send_renewal_accepted_message(entry.renewal, payment)
            except Renewal.DoesNotExist:
                pass

        updated_entries.append(entry.pk)

    return Entry.objects.filter(
        pk__in=updated_entries).update(status=Entry.STATUS_ACCEPTED,
                                       updated_at=timezone.now())


def _create_payment_for_entry(entry):
    """
    Create payment model for entry

    :param entry: Registration or Renewal model
    :type entry: Entry
    :return: Payment connected to the entry with the right price
    :rtype: Payment
    """
    amount = settings.MEMBERSHIP_PRICES[entry.length]

    try:
        renewal = entry.renewal
        membership = renewal.member.latest_membership
        # Having a latest membership which has an until date implies that this
        # membership lasts/lasted till the end of the lecture year
        # This means it's possible to renew the 'year' membership
        # to a 'study' membership and the price should be adjusted since
        # it is considered an upgrade without paying twice
        # The rules for this behaviour are taken from the HR

        # Since it is possible for people to renew their membership
        # but processing to occur _after_ the membership ended
        # we're checking if that is the case so that these members
        # still get the discount price
        if (membership is not None and membership.until is not None and
                entry.created_at.date() < membership.until and
                renewal.length == Entry.MEMBERSHIP_STUDY):
            amount = (settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY] -
                      settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR])
    except Renewal.DoesNotExist:
        pass

    payment = Payment.objects.create(
        amount=amount,
    )
    entry.payment = payment
    entry.save()

    return payment


def _create_member_from_registration(registration):
    """
    Create User and Member model from Registration

    :param registration: Registration model
    :type registration: Registration
    :return: Created member object
    :rtype: Member
    """

    # Generate random password for user that we can send to the new user
    password = get_user_model().objects.make_random_password(length=15)

    # Make sure the username and email are unique
    if not check_unique_user(registration):
        raise ValueError('Username or email address of the registration '
                         'are not unique')

    # Create user
    user = get_user_model().objects.create_user(
        username=registration.username,
        email=registration.email,
        password=password,
        first_name=registration.first_name,
        last_name=registration.last_name
    )

    # Add profile to created user
    Profile.objects.create(
        user=user,
        programme=registration.programme,
        student_number=registration.student_number,
        starting_year=registration.starting_year,
        address_street=registration.address_street,
        address_street2=registration.address_street2,
        address_postal_code=registration.address_postal_code,
        address_city=registration.address_city,
        phone_number=registration.phone_number,
        birthday=registration.birthday,
        language=registration.language
    )

    # Send welcome message to new member
    members.emails.send_welcome_message(user, password, registration.language)

    return user


def _create_membership_from_entry(entry, member=None):
    """
    Create or update Membership model based on Entry model information

    :param entry: Entry model
    :type entry: Entry
    :return: The created or updated membership
    :rtype: Membership
    """
    lecture_year = datetime_to_lectureyear(timezone.now())
    # If it's August we act as if it's the next
    # lecture year already and we start new memberships in September
    since = timezone.now().date()
    if timezone.now().month == 8:
        lecture_year += 1
        since = since.replace(month=9, day=1)
    until = None

    if entry.length == Entry.MEMBERSHIP_YEAR:
        # If entry is Renewal set since to current membership until + 1 day
        # Unless there is no current membership
        try:
            member = entry.renewal.member
            membership = member.current_membership
            if membership is not None:
                if membership.until is None:
                    raise ValueError('This member already has a never ending '
                                     'membership')
                since = membership.until + timedelta(days=1)
        except Renewal.DoesNotExist:
            pass
        until = timezone.datetime(year=lecture_year + 1,
                                  month=9, day=1).date()
    elif entry.length == Entry.MEMBERSHIP_STUDY:
        try:
            renewal = entry.renewal
            member = renewal.member
            membership = member.latest_membership
            # Having a latest membership which has an until date implies that
            # this membership last(s/ed) till the end of the lecture year
            # This means it's possible to renew the 'year' membership
            # to a 'study' membership thus the until date should now be None
            # and no new membership is needed.
            # The rules for this behaviour are taken from the HR
            if membership is not None:
                if membership.until is None:
                    raise ValueError('This member already has a never ending '
                                     'membership')
                if entry.created_at.date() < membership.until:
                    membership.until = None
                    membership.save()
                    return membership
        except Renewal.DoesNotExist:
            pass
    else:
        return None

    return Membership.objects.create(
        user=member,
        since=since,
        until=until,
        type=entry.membership_type
    )


def process_payment(payment):
    """
    Process the payment for the entry and send the right emails

    :param payment: The payment that should be processed
    :type payment: Payment
    """

    if not payment.processed:
        return

    try:
        entry = payment.registrations_entry
    except Entry.DoesNotExist:
        return

    if entry.status != Entry.STATUS_ACCEPTED:
        return

    member = None

    try:
        registration = entry.registration
        # Create user and member
        member = _create_member_from_registration(registration)
    except Registration.DoesNotExist:
        try:
            # Get member from renewal
            renewal = entry.renewal
            member = renewal.member
            # Send email of payment confirmation for renewal,
            # not needed for registration since a new member already
            # gets the welcome email
            emails.send_renewal_complete_message(entry.renewal)
        except Renewal.DoesNotExist:
            pass

    # If member was retrieved, then create a new membership
    if member is not None:
        membership = _create_membership_from_entry(entry, member)
        entry.membership = membership
        entry.status = Entry.STATUS_COMPLETED
        entry.save()
