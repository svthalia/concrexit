# Not registered, cannot register yet
STATUS_WILL_OPEN = "registration-will-open"

# Not registered, deadline expired
STATUS_EXPIRED = "registration-expired"

# Not registered, can register
STATUS_OPEN = "registration-open"

# Not registered, can put self on waiting list
STATUS_FULL = "registration-full"

# Registered, on waiting list
STATUS_WAITINGLIST = "registration-waitinglist"

# Registered
# No cancel means cancellation deadline expired; user cannot deregister without paying a fine
# No rereg means registration deadline expired; user cannot re-register if they deregister
STATUS_REGISTERED = "registration-registered"

# User cancelled their registration; if LATE they missed the deadline and need to pay the fine
STATUS_CANCELLED = "registration-cancelled"
STATUS_CANCELLED_FINAL = "registration-cancelled-final"
STATUS_CANCELLED_LATE = "registration-cancelled-late"

# Registering is optional; no or yes registration
STATUS_OPTIONAL = "registration-optional"
STATUS_OPTIONAL_REGISTERED = "registration-optional-registered"

# Registrations are disabled
STATUS_NONE = "registration-none"

# User is not logged in so cannot register
STATUS_LOGIN = "registration-login"

CANCEL_NORMAL = "cancel-normal"  # Cancellation allowed
CANCEL_FINAL = "cancel-final"  # Can cancel, but will not be able to re-register
CANCEL_LATE = "cancel-late"  # Too late, will pay fine
CANCEL_WAITINGLIST = (
    "cancel-waitinglist"  # Too late, but allowed because user is on waitinglist
)


def is_registered(status):
    return status in [STATUS_REGISTERED, STATUS_OPTIONAL_REGISTERED, STATUS_WAITINGLIST]


def calendarjs_class_name(status):
    if status == STATUS_WAITINGLIST:
        return "regular-event-pending-registration"
    if status in [STATUS_OPTIONAL_REGISTERED, STATUS_REGISTERED]:
        return "regular-event-has-registration"
    if status in [
        STATUS_CANCELLED,
        STATUS_OPEN,
        STATUS_FULL,
        STATUS_OPTIONAL,
        STATUS_NONE,
    ]:
        return "regular-event-registration-open"
    return "regular-event-registration-closed"
