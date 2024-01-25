"""The services defined by the registrations package."""

import secrets

from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Value
from django.utils import timezone

from members.emails import send_welcome_message
from members.models import Member, Membership, Profile
from payments.models import BankAccount, Payment, PaymentUser
from payments.services import create_payment
from registrations import emails
from registrations.models import Entry, Registration, Renewal
from utils.snippets import datetime_to_lectureyear


def confirm_registration(registration: Registration) -> None:
    """Confirm a registration.

    This happens when the user has verified their email address.
    """
    registration.refresh_from_db()
    if registration.status != registration.STATUS_CONFIRM:
        raise ValueError("Registration is already confirmed.")

    registration.status = registration.STATUS_REVIEW
    registration.save()

    if (
        registration.membership_type == Membership.BENEFACTOR
        and not registration.no_references
    ):
        emails.send_references_information_message(registration)

    emails.send_new_registration_board_message(registration)


def reject_registration(registration: Registration, actor: Member) -> None:
    """Reject a registration."""
    registration.refresh_from_db()
    if registration.status != registration.STATUS_REVIEW:
        raise ValueError("Registration is not in review.")

    registration.status = registration.STATUS_REJECTED
    registration.save()

    # Log that the `actor` changed the status.
    LogEntry.objects.log_action(
        user_id=actor.id,
        content_type_id=get_content_type_for_model(registration).pk,
        object_id=registration.pk,
        object_repr=str(registration),
        action_flag=CHANGE,
        change_message="Changed status to rejected",
    )

    emails.send_registration_rejected_message(registration)


def revert_registration(
    registration: Registration, actor: Member | None = None
) -> None:
    """Undo the review of a registration."""
    registration.refresh_from_db()
    if registration.status not in (
        registration.STATUS_ACCEPTED,
        registration.STATUS_REJECTED,
    ):
        raise ValueError("Registration is not accepted or rejected.")

    with transaction.atomic():
        if registration.payment:
            registration.payment.delete()

        registration.payment = None
        registration.status = registration.STATUS_REVIEW
        registration.save()

    if actor is not None:  # pragma: no cover
        # Log that the `actor` changed the status.
        LogEntry.objects.log_action(
            user_id=actor.id,
            content_type_id=get_content_type_for_model(registration).pk,
            object_id=registration.pk,
            object_repr=str(registration),
            action_flag=CHANGE,
            change_message="Reverted status to review",
        )


def accept_registration(registration: Registration, actor: Member) -> None:
    """Accept a registration.

    If the registration wants to pay with direct debit, this will also
    complete the registration, and then pay for it with Thalia Pay.

    Otherwise, an email will be sent informing the user that they need to pay.
    """
    registration.refresh_from_db()
    if registration.status != registration.STATUS_REVIEW:
        raise ValueError("Registration is not in review.")

    with transaction.atomic():
        if not registration.check_user_is_unique():
            raise ValueError("Username or email is not unique")

        registration.status = registration.STATUS_ACCEPTED
        registration.save()

        # Log that the `actor` changed the status.
        LogEntry.objects.log_action(
            user_id=actor.id,
            content_type_id=get_content_type_for_model(registration).pk,
            object_id=registration.pk,
            object_repr=str(registration),
            action_flag=CHANGE,
            change_message="Changed status to approved",
        )

        # Complete and pay the registration with Thalia Pay if possible.
        if registration.direct_debit:
            # If this raises, propagate the exception and roll back the transaction.
            # The 'accepting' of the registration will be rolled back as well.
            complete_registration(registration)

    if not registration.direct_debit:
        # Inform the user that they need to pay.
        emails.send_registration_accepted_message(registration)


def revert_renewal(renewal: Renewal, actor: Member | None = None) -> None:
    """Undo the review of a registration."""
    renewal.refresh_from_db()
    if renewal.status not in (
        renewal.STATUS_ACCEPTED,
        renewal.STATUS_REJECTED,
    ):
        raise ValueError("Registration is not accepted or rejected.")

    if renewal.payment:
        renewal.payment.delete()

    renewal.payment = None
    renewal.status = renewal.STATUS_REVIEW
    renewal.save()

    if actor is not None:  # pragma: no cover
        # Log that the `actor` changed the status.
        LogEntry.objects.log_action(
            user_id=actor.id,
            content_type_id=get_content_type_for_model(renewal).pk,
            object_id=renewal.pk,
            object_repr=str(renewal),
            action_flag=CHANGE,
            change_message="Reverted status to review",
        )


def complete_registration(registration: Registration) -> None:
    """Complete a registration, creating a Member, Profile and Membership.

    This will create a Thalia Pay payment after completing the registration, if
    the registration is not yet paid and direct debit is enabled.

    If anything goes wrong, database changes will be rolled back.

    If direct debit is not enabled, the registration must already be paid for.
    """
    registration.refresh_from_db()
    if registration.status != registration.STATUS_ACCEPTED:
        raise ValueError("Registration is not accepted.")
    elif registration.payment is None and not registration.direct_debit:
        raise ValueError("Registration has not been paid for.")

    # If anything goes wrong, the changes to the database will be rolled back.
    # Specifically, if an exception is raised when creating a Thalia Pay payment,
    # the registration will not be completed, so it can be handled properly.
    with transaction.atomic():
        member = _create_member(registration)
        membership = _create_membership_from_registration(registration, member)
        registration.membership = membership
        registration.status = registration.STATUS_COMPLETED
        registration.save()

        if not registration.payment:
            # Create a Thalia Pay payment.
            create_payment(registration, member, Payment.TPAY)
            registration.refresh_from_db()


def reject_renewal(renewal: Renewal, actor: Member):
    """Reject a renewal."""
    renewal.refresh_from_db()
    if renewal.status != renewal.STATUS_REVIEW:
        raise ValueError("Renewal is not in review.")

    renewal.status = renewal.STATUS_REJECTED
    renewal.save()

    # Log that the `actor` changed the status.
    LogEntry.objects.log_action(
        user_id=actor.id,
        content_type_id=get_content_type_for_model(renewal).pk,
        object_id=renewal.pk,
        object_repr=str(renewal),
        action_flag=CHANGE,
        change_message="Changed status to rejected",
    )

    emails.send_renewal_rejected_message(renewal)


def accept_renewal(renewal: Renewal, actor: Member):
    renewal.refresh_from_db()
    if renewal.status != renewal.STATUS_REVIEW:
        raise ValueError("Renewal is not in review.")

    renewal.status = renewal.STATUS_ACCEPTED
    renewal.save()

    # Log that the `actor` changed the status.
    LogEntry.objects.log_action(
        user_id=actor.id,
        content_type_id=get_content_type_for_model(renewal).pk,
        object_id=renewal.pk,
        object_repr=str(renewal),
        action_flag=CHANGE,
        change_message="Changed status to approved",
    )

    emails.send_renewal_accepted_message(renewal)


def complete_renewal(renewal: Renewal):
    """Complete a renewal, prolonging a Membership or creating a new one."""
    renewal.refresh_from_db()
    if renewal.status != renewal.STATUS_ACCEPTED:
        raise ValueError("Renewal is not accepted.")
    elif renewal.payment is None:
        raise ValueError("Registration has not been paid for.")

    member: Member = renewal.member
    member.refresh_from_db()

    since = calculate_membership_since()
    lecture_year = datetime_to_lectureyear(since)

    latest_membership = member.latest_membership
    # Not that currently, Member. current_membership can be a future membership if a new
    # membership has been created but it's not yet september. This does not matter here,
    # but it is kind of incorrect.
    current_membership = member.current_membership

    with transaction.atomic():
        if renewal.length == Entry.MEMBERSHIP_STUDY:
            # Handle the 'membership upgrade' case.
            if latest_membership is not None:  # pragma: no cover
                if latest_membership.until is None:
                    raise ValueError(
                        "This member already has a never ending membership"
                    )

                if renewal.created_at.date() < latest_membership.until:
                    # If a membership exists that was still valid when the renewal was created, the
                    # original membership can be upgraded. This is defined in the Huishoudelijk
                    # Reglement (article 2.8 in the version of 2022-07-22).
                    latest_membership.until = None
                    latest_membership.save()
                    renewal.membership = latest_membership

            # Handle the 'normal' non-(discounted)-upgrade case.
            if renewal.membership is None:
                renewal.membership = Membership.objects.create(
                    type=renewal.membership_type, user=member, since=since, until=None
                )
        else:
            if current_membership is not None:
                if current_membership.until is None:
                    raise ValueError(
                        "This member already has a never ending membership"
                    )
                since = current_membership.until

            until = timezone.datetime(year=lecture_year + 1, month=9, day=1).date()
            renewal.membership = Membership.objects.create(
                type=renewal.membership_type, user=member, since=since, until=until
            )

        renewal.status = renewal.STATUS_COMPLETED
        renewal.save()

    emails.send_renewal_complete_message(renewal)


def calculate_membership_since() -> timezone.datetime:
    """Calculate the start date of a membership.

    If it's August we act as if it's the next lecture year
    already and we start new memberships in September.
    """
    since = timezone.now().date()
    if timezone.now().month == 8:
        since = since.replace(month=9, day=1)
    return since


_PASSWORD_CHARS = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _create_member(registration: Registration) -> Member:
    """Create a member and profile from a Registration."""
    # Generate random password for user that we can send to the new user.
    password = "".join(secrets.choice(_PASSWORD_CHARS) for _ in range(15))

    # Make sure the username and email are unique
    if not registration.check_user_is_unique():
        raise ValueError("Username or email is not unique.")

    # Create user.
    user = get_user_model().objects.create_user(
        username=registration.get_username(),
        email=registration.email,
        password=password,
        first_name=registration.first_name,
        last_name=registration.last_name,
    )

    # Add profile to created user.
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
        receive_oldmembers=registration.membership_type == Membership.MEMBER,
    )

    if registration.direct_debit:
        # Add a bank account.
        payment_user = PaymentUser.objects.get(pk=user.pk)
        payment_user.allow_tpay()
        BankAccount.objects.create(
            owner=payment_user,
            iban=registration.iban,
            bic=registration.bic,
            initials=registration.initials,
            last_name=registration.last_name,
            signature=registration.signature,
            mandate_no=f"{user.pk}-{1}",
            valid_from=registration.created_at,
        )

    # Send welcome message to new member
    send_welcome_message(user, password)

    return Member.objects.get(pk=user.pk)


def _create_membership_from_registration(
    registration: Registration, member: Member
) -> Membership:
    """Create a membership from a Registration."""
    since = calculate_membership_since()
    lecture_year = datetime_to_lectureyear(since)

    if registration.membership_type == Membership.BENEFACTOR:
        until = timezone.datetime(year=lecture_year + 1, month=9, day=1).date()
    elif registration.length == Registration.MEMBERSHIP_YEAR:
        until = timezone.datetime(year=lecture_year + 1, month=9, day=1).date()
    else:
        until = None

    return Membership.objects.create(
        user=member, since=since, until=until, type=registration.membership_type
    )


def execute_data_minimisation(dry_run=False):
    """Delete completed or rejected registrations that were modified at least 31 days ago.

    :param dry_run: does not really remove data if True
    :return: number of removed objects.
    """
    deletion_period = timezone.now() - timezone.timedelta(days=31)
    registrations = Registration.objects.filter(
        Q(status=Entry.STATUS_COMPLETED) | Q(status=Entry.STATUS_REJECTED),
        updated_at__lt=deletion_period,
    )
    renewals = Renewal.objects.filter(
        Q(status=Entry.STATUS_COMPLETED) | Q(status=Entry.STATUS_REJECTED),
        updated_at__lt=deletion_period,
    )

    if dry_run:
        return registrations.count() + renewals.count()  # pragma: no cover

    # Mark that this deletion is for data minimisation so that it can be recognized
    # in any post_delete signal handlers. This is used to prevent the deletion of
    # Moneybird invoices.
    registrations = registrations.annotate(__deleting_for_dataminimisation=Value(True))
    renewals = renewals.annotate(__deleting_for_dataminimisation=Value(True))

    return registrations.delete()[0] + renewals.delete()[0]
