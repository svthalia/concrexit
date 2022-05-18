# Not registered, cannot register
STATUS_CLOSED = "registration-closed"

# Not registered, can register
STATUS_OPEN = "registration-open"

# Not registered, can put self on waiting list
STATUS_FULL = "registration-full"

# Registered, on waiting list
STATUS_WAITINGLIST = "registration-waitinglist"

# Registered
STATUS_REGISTERED = "registration-registered"

# Registered, cannot cancel without fine
STATUS_REGISTERED_NO_CANCEL = "registration-registered-nocancel"

# Registered, cannot re-register if canceled
STATUS_REGISTERED_NO_REREG = "registration-registered-norereg"

# Registered, cannot re-register if canceled, nor cancel without paying a fine
STATUS_REGISTERED_NO_CANCEL_REREG = "registration-registered-nocancelnorereg"

# TODO: Not registered, registration is optional
# TODO: Registered, registration is optional
# TODO: Cannot register; register elsewhere


def is_registered(status):
    if (
        status == STATUS_REGISTERED
        or status == STATUS_REGISTERED_NO_CANCEL
        or status == STATUS_REGISTERED_NO_REREG
        or status == STATUS_REGISTERED_NO_CANCEL_REREG
    ):
        return True
    else:
        return False
