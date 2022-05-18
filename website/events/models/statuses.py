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
STATUS_CANCELLED_LATE = "registration-cancelled-late"

# Registering is optional; no or yes registration
STATUS_OPTIONAL = "registration-optional"
STATUS_OPTIONAL_REGISTERED = "registration-optional-registered"

# Registrations are disabled
STATUS_NONE = "registration-none"

# User is not logged in so cannot register
STATUS_LOGIN = "registration-login"

# TODO: separate registration status and cancel status (ie NO_CANCEL NO_REREG)
CANCEL_NORMAL = "cancel-normal"
CANCEL_LATE = "cancel-late"
CANCEL_FINAL = "cancel-final"
CANCEL_LATE_FINAL = "cancel-late-final"

def is_registered(status):
    if (
        status == STATUS_REGISTERED
        or status == STATUS_OPTIONAL_REGISTERED
        or status == STATUS_WAITINGLIST
    ):
        return True
    else:
        return False
