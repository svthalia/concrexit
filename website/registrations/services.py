"""The services defined by the registrations package"""
import string
import unicodedata
from typing import Union

from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet
from django.utils import timezone

import members
from members.models import Membership, Profile, Member
from payments.models import Payment
from registrations import emails
from registrations.models import Entry, Registration, Renewal
from utils.snippets import datetime_to_lectureyear


def _generate_username(registration: Registration) -> str:
    """
    Create username from first and lastname

    :param registration: Model containing first and last name
    :type registration: Registration
    :return: Created username
    :rtype: str
    """
    username = (registration.first_name[0] + registration.last_name).lower()
    username = "".join(c for c in username if c.isalpha())
    username = "".join(
        c for c in unicodedata.normalize("NFKD", username) if c in string.ascii_letters
    ).lower()

    # Limit length to 150 characters since Django doesn't support longer
    if len(username) > 150:
        username = username[:150]

    return username


def check_unique_user(entry: Entry) -> bool:
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
        if (
            get_user_model().objects.filter(username=username).exists()
            and registration.username is not None
        ):
            username = registration.username

        return not (
            get_user_model()
            .objects.filter(Q(email=registration.email) | Q(username=username))
            .exists()
        )
    except Registration.DoesNotExist:
        pass
    return True


def confirm_entry(queryset: QuerySet) -> int:
    """
    Confirm all entries in the queryset

    :param queryset: queryset of entries
    :type queryset: Queryset[Entry]
    :return: number of updated rows
    :rtype: integer
    """
    queryset = queryset.filter(status=Entry.STATUS_CONFIRM)
    rows_updated = queryset.update(
        status=Entry.STATUS_REVIEW, updated_at=timezone.now()
    )
    return rows_updated


def reject_entries(user_id: int, queryset: QuerySet) -> int:
    """
    Reject all entries in the queryset

    :param user_id: Id of the user executing this action
    :param queryset: queryset of entries
    :type queryset: Queryset[Entry]
    :return: number of updated rows
    :rtype: integer
    """
    queryset = queryset.filter(status=Entry.STATUS_REVIEW)
    entries = list(queryset.all())
    rows_updated = queryset.update(
        status=Entry.STATUS_REJECTED, updated_at=timezone.now()
    )

    for entry in entries:
        log_obj = None

        try:
            emails.send_registration_rejected_message(entry.registration)
            log_obj = entry.registration
        except Registration.DoesNotExist:
            try:
                emails.send_renewal_rejected_message(entry.renewal)
                log_obj = entry.renewal
            except Renewal.DoesNotExist:
                pass

        if log_obj:
            LogEntry.objects.log_action(
                user_id=user_id,
                content_type_id=get_content_type_for_model(log_obj).pk,
                object_id=log_obj.pk,
                object_repr=str(log_obj),
                action_flag=CHANGE,
                change_message="Changed status to rejected",
            )

    return rows_updated


def accept_entries(user_id: int, queryset: QuerySet) -> int:
    """
    Accept all entries in the queryset

    :param user_id: Id of the user executing this action
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

        entry.status = Entry.STATUS_ACCEPTED
        entry.updated_at = timezone.now()
        entry.payment = _create_payment_for_entry(entry)

        log_obj = None

        try:
            if entry.registration.username is None:
                entry.registration.username = _generate_username(entry.registration)
                entry.registration.save()
            emails.send_registration_accepted_message(entry.registration, entry.payment)
            log_obj = entry.registration
        except Registration.DoesNotExist:
            try:
                emails.send_renewal_accepted_message(entry.renewal, entry.payment)
                log_obj = entry.renewal
            except Renewal.DoesNotExist:
                pass

        if log_obj:
            LogEntry.objects.log_action(
                user_id=user_id,
                content_type_id=get_content_type_for_model(log_obj).pk,
                object_id=log_obj.pk,
                object_repr=str(log_obj),
                action_flag=CHANGE,
                change_message="Change status to approved",
            )

        entry.save()
        updated_entries.append(entry.pk)

    return len(updated_entries)


def revert_entry(user_id: int, entry: Entry) -> None:
    """
    Revert status of entry to review so that it can be corrected

    :param user_id: Id of the user executing this action
    :param entry: Entry that should be reverted
    """
    if not (entry.status in [Entry.STATUS_ACCEPTED, Entry.STATUS_REJECTED]):
        return

    payment = entry.payment
    entry.status = Entry.STATUS_REVIEW
    entry.updated_at = timezone.now()
    entry.payment = None
    entry.save()
    if payment is not None:
        payment.delete()

    log_obj = None

    try:
        log_obj = entry.registration
    except Registration.DoesNotExist:
        try:
            log_obj = entry.renewal
        except Renewal.DoesNotExist:
            pass

    if log_obj:
        LogEntry.objects.log_action(
            user_id=user_id,
            content_type_id=get_content_type_for_model(log_obj).pk,
            object_id=log_obj.pk,
            object_repr=str(log_obj),
            action_flag=CHANGE,
            change_message="Revert status to review",
        )


def _create_payment_for_entry(entry: Entry) -> Payment:
    """
    Create payment model for entry

    :param entry: Registration or Renewal model
    :type entry: Entry
    :return: Payment connected to the entry with the right price
    :rtype: Payment
    """
    amount = settings.MEMBERSHIP_PRICES[entry.length]
    if entry.contribution and entry.membership_type == Membership.BENEFACTOR:
        amount = entry.contribution
    notes = f"Membership registration. {entry.get_membership_type_display()}."
    topic = f"Member registration [{entry.membership_type.upper()}]"

    try:
        renewal = entry.renewal
        membership = renewal.member.latest_membership
        notes = f"Membership renewal. {entry.get_membership_type_display()}."
        topic = f"Member renewal [{entry.membership_type.upper()}]"
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
        if (
            membership is not None
            and membership.until is not None
            and entry.created_at.date() < membership.until
            and renewal.length == Entry.MEMBERSHIP_STUDY
        ):
            amount = (
                settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY]
                - settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR]
            )
    except Renewal.DoesNotExist:
        pass

    return Payment.objects.create(amount=amount, notes=notes, topic=topic)


def _create_member_from_registration(registration: Registration) -> Member:
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
        raise ValueError("Username or email address of the registration are not unique")

    # Create user
    user = get_user_model().objects.create_user(
        username=registration.username.lower(),
        email=registration.email,
        password=password,
        first_name=registration.first_name,
        last_name=registration.last_name,
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
        address_country=registration.address_country,
        phone_number=registration.phone_number,
        birthday=registration.birthday,
        show_birthday=registration.optin_birthday,
        receive_optin=registration.optin_mailinglist,
    )

    # Send welcome message to new member
    members.emails.send_welcome_message(user, password, registration.language)

    return Member.objects.get(pk=user.pk)


def calculate_membership_since() -> timezone.datetime:
    """
    Calculate the start date of a membership

    If it's August we act as if it's the next
    lecture year already and we start new memberships in September
    :return:
    """
    since = timezone.now().date()
    if timezone.now().month == 8:
        since = since.replace(month=9, day=1)
    return since


def _create_membership_from_entry(
    entry: Entry, member: Member = None
) -> Union[Membership, None]:
    """
    Create or update Membership model based on Entry model information

    :param entry: Entry model
    :type entry: Entry
    :return: The created or updated membership
    :rtype: Membership
    """
    lecture_year = datetime_to_lectureyear(timezone.now())
    since = calculate_membership_since()
    until = None
    if timezone.now().month == 8:
        lecture_year += 1

    if entry.length == Entry.MEMBERSHIP_YEAR:
        # If entry is Renewal set since to current membership until + 1 day
        # Unless there is no current membership
        try:
            member = entry.renewal.member
            membership = member.current_membership
            if membership is not None:
                if membership.until is None:
                    raise ValueError(
                        "This member already has a never ending membership"
                    )
                since = membership.until
        except Renewal.DoesNotExist:
            pass
        until = timezone.datetime(year=lecture_year + 1, month=9, day=1).date()
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
                    raise ValueError(
                        "This member already has a never ending membership"
                    )
                if entry.created_at.date() < membership.until:
                    membership.until = None
                    membership.save()
                    return membership
        except Renewal.DoesNotExist:
            pass
    else:
        return None

    return Membership.objects.create(
        user=member, since=since, until=until, type=entry.membership_type
    )


def process_payment(payment: Payment) -> None:
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
        Payment.objects.filter(pk=payment.pk).update(paid_by=member)
        membership = _create_membership_from_entry(entry, member)
        entry.membership = membership
        entry.status = Entry.STATUS_COMPLETED
        entry.save()


def execute_data_minimisation(dry_run=False):
    """
    Delete completed or rejected registrations that were modified
    at least 31 days ago

    :param dry_run: does not really remove data if True
    :return: number of removed registrations
    """
    deletion_period = timezone.now() - timezone.timedelta(days=31)
    objects = Entry.objects.filter(
        (Q(status=Entry.STATUS_COMPLETED) | Q(status=Entry.STATUS_REJECTED))
        & Q(updated_at__lt=deletion_period)
    )

    if dry_run:
        return objects.count()
    return objects.delete()[0]
