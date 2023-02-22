from enum import Enum


class WebhookEvent(Enum):
    ADMINISTRATION = "administration"

    ADMINISTRATION_ACTIVATED = "administration_activated"  # Administration activated
    ADMINISTRATION_ADDED = "administration_added"  # Administration added
    ADMINISTRATION_CANCELLED = (
        "administration_cancelled"  # Removal of administration requested
    )
    ADMINISTRATION_CHANGED = "administration_changed"  # Administration updated
    ADMINISTRATION_DELETED = (
        "administration_deleted"  # Removal of administration requested
    )
    ADMINISTRATION_REACTIVATED = (
        "administration_reactivated"  # Administration reactivated
    )
    ADMINISTRATION_REMOVED = "administration_removed"  # Administration deleted
    ADMINISTRATION_SUSPENDED = "administration_suspended"  # Administration suspended
    ADMINISTRATION_AUTOMATIC_BOOKERS_ACTIVATED = "administration_automatic_bookers_activated"  # Activated automatic linking of transactions
    ADMINISTRATION_AUTOMATIC_BOOKERS_DEACTIVATED = "administration_automatic_bookers_deactivated"  # Deactivated automatic linking of transactions
    ADMINISTRATION_DATA_ANALYSIS_PERMISSION_UNSET = "administration_data_analysis_permission_unset"  # Data analysis permission withdrawn
    ADMINISTRATION_DATA_ANALYSIS_PERMISSION_SET = (
        "administration_data_analysis_permission_set"  # Data analysis permission given
    )
    ADMINISTRATION_DETAILS_EDITED = (
        "administration_details_edited"  # Administration changed
    )
    ADMINISTRATION_MONEYBIRD_PAYMENTS_ACTIVATED = (
        "administration_moneybird_payments_activated"  # Moneybird Payments activated
    )
    ADMINISTRATION_PAYMENTS_WITHOUT_PROOF_ACTIVATED = "administration_payments_without_proof_activated"  # Activated payments without proof
    ADMINISTRATION_PAYMENTS_WITHOUT_PROOF_DEACTIVATED = "administration_payments_without_proof_deactivated"  # Deactivated payments without proof
    ADMINISTRATION_UPDATE_PERIOD_LOCKED_UNTIL = (
        "administration_update_period_locked_until"  # Locked period updated
    )

    ADVISER = "adviser"

    ADVISER_UPDATED = "adviser_updated"  # Adviser updated
    ADVISER_CREATED = "adviser_created"  # Adviser created
    ADVISER_DELETED = "adviser_deleted"  # Adviser deleted
    ADVISER_UPDATED_PHOTO = "adviser_updated_photo"  # Profile image added
    ADVISER_EMAIL_CONCEPT_STATE_SENT = (
        "adviser_email_concept_state_sent"  # E-mail about concept state sent
    )
    ADVISER_EMAIL_PUBLISHED_STATE_SENT = (
        "adviser_email_published_state_sent"  # E-mail about published state sent
    )
    ADVISER_EXPERIENCE_CREATED = "adviser_experience_created"  # Experience created
    ADVISER_EXPERIENCE_UPDATED = "adviser_experience_updated"  # Experience updated
    ADVISER_EXPERIENCE_DELETED = "adviser_experience_deleted"  # Experience deleted
    ADVISER_EDUCATION_CREATED = "adviser_education_created"  # Education created
    ADVISER_EDUCATION_UPDATED = "adviser_education_updated"  # Education updated
    ADVISER_EDUCATION_DELETED = "adviser_education_deleted"  # Education deleted
    ADVISER_COMPANY_CREATED = "adviser_company_created"  # Company created
    ADVISER_COMPANY_UPDATED = "adviser_company_updated"  # Company updated
    ADVISER_COMPANY_PHOTO = "adviser_company_photo"  # Company image added
    ADVISER_COMPANY_LOCATION_CREATED = (
        "adviser_company_location_created"  # Location created
    )
    ADVISER_COMPANY_LOCATION_DELETED = (
        "adviser_company_location_deleted"  # Location deleted
    )
    ADVISERS_LOCATION_CREATED = "advisers_location_created"  # Location created
    ADVISERS_LOCATION_DELETED = "advisers_location_deleted"  # Location deleted

    ADYEN = "adyen"

    ADYEN_PAYMENT_INSTRUMENT_CREATED = (
        "adyen_payment_instrument_created"  # Moneybird card created
    )
    ADYEN_PAYMENT_INSTRUMENT_UPDATED = (
        "adyen_payment_instrument_updated"  # Moneybird card updated
    )

    BOOKING_RULE = "booking_rule"

    BOOKING_RULE_CREATED = "booking_rule_created"  # Booking rule created
    BOOKING_RULE_UPDATED = "booking_rule_updated"  # Booking rule updated
    BOOKING_RULE_DESTROYED = "booking_rule_destroyed"  # Booking rule deleted

    CONTACT = "contact"

    CONTACT_ARCHIVED = "contact_archived"  # Contact archived
    CONTACT_ACTIVATED = "contact_activated"  # Contact activated
    CONTACT_CHANGED = "contact_changed"  # Contact updated
    CONTACT_CREATED = "contact_created"  # Contact created
    CONTACT_CREATED_FROM_CHECKOUT_ORDER = (
        "contact_created_from_checkout_order"  # Contact created through checkout
    )
    CONTACT_DESTROYED = "contact_destroyed"  # Contact deleted
    CONTACT_MANDATE_REQUEST_FAILED = (
        "contact_mandate_request_failed"  # Mandate request failed
    )
    CONTACT_MANDATE_REQUEST_INITIATED = (
        "contact_mandate_request_initiated"  # Mandate request sent
    )
    CONTACT_MANDATE_REQUEST_SUCCEEDED = (
        "contact_mandate_request_succeeded"  # Mandate request succeeded
    )
    CONTACT_MERGED = "contact_merged"  # Contact was merged
    CONTACT_PERSON_CREATED = "contact_person_created"  # Contact person created
    CONTACT_PERSON_DESTROYED = "contact_person_destroyed"  # Contact person deleted
    CONTACT_PERSON_UPDATED = "contact_person_updated"  # Contact person updated

    CREDIT_INVOICE_CREATED_FROM_ORIGINAL = (
        "credit_invoice_created_from_original"  # Credit note created based on invoice
    )
    DEFAULT_IDENTITY_UPDATED = (
        "default_identity_updated"  # Default sender address updated
    )
    DEFAULT_TAX_RATE_CREATED = "default_tax_rate_created"  # Default VAT rate added
    DIRECT_BANK_LINK_ACTIVATED = "direct_bank_link_activated"  # Bank link activated

    DIRECT_DEBIT_TRANSACTION_CREATED = (
        "direct_debit_transaction_created"  # Direct debit batch created
    )
    DIRECT_DEBIT_TRANSACTION_DELETED = (
        "direct_debit_transaction_deleted"  # Direct debit batch deleted
    )
    DOCUMENT_ATTACHMENT_SKIPPED = (
        "document_attachment_skipped"  # Attachment couldn't be saved from email
    )

    DOCUMENT = "document"

    DOCUMENT_CREATED_FROM_ORIGINAL = "document_created_from_original"  # Document created based on an original document
    DOCUMENT_DESTROYED = "document_destroyed"  # Document deleted
    DOCUMENT_EXPIRED = "document_expired"  # Document expired
    DOCUMENT_RECURRED = "document_recurred"  # Recurring document created
    DOCUMENT_SAVED = "document_saved"  # Document saved
    DOCUMENT_SAVED_FROM_EMAIL = (
        "document_saved_from_email"  # Document received by email
    )
    DOCUMENT_SAVED_FROM_SI = "document_saved_from_si"  # Document received via Peppol
    DOCUMENT_UPDATED = "document_updated"  # Document updated

    DOCUMENT_STYLE = "document_style"

    DOCUMENT_STYLE_CREATED = "document_style_created"  # Layout added
    DOCUMENT_STYLE_DESTROYED = "document_style_destroyed"  # Layout deleted
    DOCUMENT_STYLE_UPDATED = "document_style_updated"  # Layout updated

    EMAIL_DOMAIN_DEACTIVATED = (
        "email_domain_deactivated"  # Sending from your own domain has been disabled.
    )
    EMAIL_DOMAIN_VALIDATED = "email_domain_validated"  # Your domain is verified.

    ESTIMATE = "estimate"

    ESTIMATE_ACCEPTED_CONTACT = "estimate_accepted_contact"  # Quote accepted online
    ESTIMATE_BILLED = "estimate_billed"  # Quote billed
    ESTIMATE_CREATED = "estimate_created"  # Quote created
    ESTIMATE_CREATED_FROM_ORIGINAL = (
        "estimate_created_from_original"  # Quote created based on the original quote
    )
    ESTIMATE_DESTROYED = "estimate_destroyed"  # Quote deleted
    ESTIMATE_MARK_ACCEPTED = "estimate_mark_accepted"  # Quote marked as accepted
    ESTIMATE_MARK_ARCHIVED = "estimate_mark_archived"  # Quote archived
    ESTIMATE_MARK_BILLED = "estimate_mark_billed"  # Quote billed
    ESTIMATE_MARK_LATE = "estimate_mark_late"  # Quote marked as expired
    ESTIMATE_MARK_OPEN = "estimate_mark_open"  # Quote marked as open
    ESTIMATE_MARK_REJECTED = "estimate_mark_rejected"  # Quote marked as rejected
    ESTIMATE_SEND_EMAIL = "estimate_send_email"  # Quote sent by email
    ESTIMATE_SEND_MANUALLY = "estimate_send_manually"  # Quote marked as sent manually
    ESTIMATE_SEND_POST = "estimate_send_post"  # Quote sent to %{address}
    ESTIMATE_SEND_POST_CANCELLED = (
        "estimate_send_post_cancelled"  # Sending by mail cancelled
    )
    ESTIMATE_SEND_POST_CONFIRMATION = (
        "estimate_send_post_confirmation"  # Sent by mail by Moneybird
    )
    ESTIMATE_SIGNED_SENDER = "estimate_signed_sender"  # Quote signed by sender
    ESTIMATE_STATE_CHANGED_TO_LATE = (
        "estimate_state_changed_to_late"  # Quote has expired
    )
    ESTIMATE_UPDATED = "estimate_updated"  # Quote updated

    EXTERNAL_SALES_INVOICE = "external_sales_invoice"

    EXTERNAL_SALES_INVOICE_CREATED = (
        "external_sales_invoice_created"  # External invoice created
    )
    EXTERNAL_SALES_INVOICE_DESTROYED = (
        "external_sales_invoice_destroyed"  # External invoice deleted
    )
    EXTERNAL_SALES_INVOICE_MARKED_AS_DUBIOUS = (
        "external_sales_invoice_marked_as_dubious"  # Marked external invoice as dubious
    )
    EXTERNAL_SALES_INVOICE_MARKED_AS_UNCOLLECTIBLE = "external_sales_invoice_marked_as_uncollectible"  # External invoice marked as uncollectible
    EXTERNAL_SALES_INVOICE_UPDATED = (
        "external_sales_invoice_updated"  # External invoice updated
    )
    EXTERNAL_SALES_INVOICE_STATE_CHANGED_TO_LATE = (
        "external_sales_invoice_state_changed_to_late"  # External invoice has expired
    )
    EXTERNAL_SALES_INVOICE_STATE_CHANGED_TO_OPEN = "external_sales_invoice_state_changed_to_open"  # State of external invoice changed to open
    EXTERNAL_SALES_INVOICE_STATE_CHANGED_TO_PAID = (
        "external_sales_invoice_state_changed_to_paid"  # External invoice has been paid
    )
    EXTERNAL_SALES_INVOICE_STATE_CHANGED_TO_UNCOLLECTIBLE = "external_sales_invoice_state_changed_to_uncollectible"  # External invoice changed to uncollectible

    FEATURE_PREFERENCE_OPT_IN = "feature_preference_opt_in"  # Beta feature turned on
    FEATURE_PREFERENCE_OPT_OUT = "feature_preference_opt_out"  # Beta feature turned off

    FEED_ENTRY_SNOOZED = "feed_entry_snoozed"  # Feed entry snoozed
    FEED_ENTRY_UNSNOOZED = "feed_entry_unsnoozed"  # Feed entry unsnoozed

    FINANCIAL_ACCOUNT = "financial_account"

    FINANCIAL_ACCOUNT_ACTIVATED = "financial_account_activated"  # Account activated
    FINANCIAL_ACCOUNT_CREATED = "financial_account_created"  # Account added
    FINANCIAL_ACCOUNT_DEACTIVATED = (
        "financial_account_deactivated"  # Account deactivated
    )
    FINANCIAL_ACCOUNT_DESTROYED = "financial_account_destroyed"  # Account deleted
    FINANCIAL_ACCOUNT_BANK_LINK_CREATED = (
        "financial_account_bank_link_created"  # Bank link created
    )
    FINANCIAL_ACCOUNT_BANK_LINK_DESTROYED = (
        "financial_account_bank_link_destroyed"  # Bank link removed
    )
    FINANCIAL_ACCOUNT_BANK_LINK_UPDATED = (
        "financial_account_bank_link_updated"  # Bank link updated
    )
    FINANCIAL_ACCOUNT_RENAMED = "financial_account_renamed"  # Account name changed

    FINANCIAL_STATEMENT = "financial_statement"

    FINANCIAL_STATEMENT_CREATED = (
        "financial_statement_created"  # Financial statement added
    )
    FINANCIAL_STATEMENT_DESTROYED = (
        "financial_statement_destroyed"  # Financial statement deleted
    )
    FINANCIAL_STATEMENT_UPDATED = (
        "financial_statement_updated"  # Financial statement updated
    )

    GOAL = "goal"

    GOAL_COMPLETED = "goal_completed"  # Goal completed
    GOAL_UNCOMPLETED = "goal_uncompleted"  # Goal not completed

    IDENTITY = "identity"

    IDENTITY_CREATED = "identity_created"  # Sender address added
    IDENTITY_DESTROYED = "identity_destroyed"  # Sender address deleted
    IDENTITY_UPDATED = "identity_updated"  # Sender address updated

    LEDGER_ACCOUNT = "ledger_account"

    LEDGER_ACCOUNT_ACTIVATED = "ledger_account_activated"  # Category activated
    LEDGER_ACCOUNT_BOOKING_CREATED = (
        "ledger_account_booking_created"  # Transaction booked on category
    )
    LEDGER_ACCOUNT_BOOKING_DESTROYED = "ledger_account_booking_destroyed"  # Link between transaction and category deleted
    LEDGER_ACCOUNT_CREATED = "ledger_account_created"  # Category added
    LEDGER_ACCOUNT_DEACTIVATED = "ledger_account_deactivated"  # Category deactivated
    LEDGER_ACCOUNT_DESTROYED = "ledger_account_destroyed"  # Category deleted
    LEDGER_ACCOUNT_UPDATED = "ledger_account_updated"  # Category updated

    MOLLIE = "mollie"

    MOLLIE_CREDENTIAL_CREATED = "mollie_credential_created"  # Link with Mollie created
    MOLLIE_CREDENTIAL_DESTROYED = (
        "mollie_credential_destroyed"  # Link with Mollie removed
    )

    NOTE = "note"

    NOTE_CREATED = "note_created"  # Note created
    NOTE_DESTROYED = "note_destroyed"  # Note deleted

    ORDER_CREATED = "order_created"  # Order placed

    PAYMENT = "payment"

    PAYMENT_DESTROYED = "payment_destroyed"  # Payment deleted
    PAYMENT_LINKED_TO_FINANCIAL_MUTATION = "payment_linked_to_financial_mutation"  # Transaction linked to a financial mutation
    PAYMENT_REGISTERED = "payment_registered"  # Payment registered for invoice
    PAYMENT_SEND_EMAIL = "payment_send_email"  # Thank You email was sent for payment
    PAYMENT_METHOD_EDITED = "payment_method_edited"  # Payment method updated
    PAYMENT_TRANSACTION_AUTHORIZED = (
        "payment_transaction_authorized"  # Direct debit transaction approved by bank
    )
    PAYMENT_TRANSACTION_AWAITING_AUTHORIZATION = "payment_transaction_awaiting_authorization"  # Direct debit transaction waiting for approval by bank
    PAYMENT_TRANSACTION_BATCH_CANCELLED = (
        "payment_transaction_batch_cancelled"  # Payment batch cancelled
    )
    PAYMENT_TRANSACTION_BATCH_CREATED = (
        "payment_transaction_batch_created"  # Payment batch created
    )
    PAYMENT_TRANSACTION_EXECUTING = (
        "payment_transaction_executing"  # Direct debit transaction being executing
    )
    PAYMENT_TRANSACTION_PAID = (
        "payment_transaction_paid"  # Direct debit transaction accepted
    )
    PAYMENT_TRANSACTION_PENDING = (
        "payment_transaction_pending"  # Direct debit transaction pending
    )
    PAYMENT_TRANSACTION_REJECTED = (
        "payment_transaction_rejected"  # Direct debit transaction rejected
    )
    PAYMENT_TRANSACTION_TECHNICALLY_VALIDATED = "payment_transaction_technically_validated"  # Direct debit payment is technically approved by the bank

    PONTO = "ponto"

    PONTO_CONNECTED = "ponto_connected"  # Ponto is connected
    PONTO_DISCONNECTED = "ponto_disconnected"  # Ponto connection deleted
    PONTO_DIRECT_BANK_LINK_ACTIVATED = (
        "ponto_direct_bank_link_activated"  # Ponto bank link activated
    )
    PONTO_DIRECT_BANK_LINK_EXPIRED = (
        "ponto_direct_bank_link_expired"  # Ponto bank link expired
    )

    PRODUCT = "product"

    PRODUCT_ACTIVATED = "product_activated"  # Product activated
    PRODUCT_CREATED = "product_created"  # Product created
    PRODUCT_DEACTIVATED = "product_deactivated"  # Product deactivated
    PRODUCT_DESTROYED = "product_destroyed"  # Product deleted
    PRODUCT_UPDATED = "product_updated"  # Product updated

    PROJECT = "project"

    PROJECT_ACTIVATED = "project_activated"  # Project activated
    PROJECT_CREATED = "project_created"  # Project added
    PROJECT_ARCHIVED = "project_archived"  # Project deactivated
    PROJECT_DESTROYED = "project_destroyed"  # Project deleted
    PROJECT_UPDATED = "project_updated"  # Project updated

    PURCHASE_TRANSACTION = "purchase_transaction"

    PURCHASE_TRANSACTION_ADDED_TO_BATCH = "purchase_transaction_added_to_batch"  # Transaction added to credit transfer batch
    PURCHASE_TRANSACTION_AUTHORIZED = (
        "purchase_transaction_authorized"  # Payment authorized at bank
    )
    PURCHASE_TRANSACTION_AWAITING_AUTHORIZATION = "purchase_transaction_awaiting_authorization"  # Payment awaiting authorization at bank
    PURCHASE_TRANSACTION_BATCH_CANCELLED = (
        "purchase_transaction_batch_cancelled"  # Credit transfer batch cancelled
    )
    PURCHASE_TRANSACTION_BATCH_CREATED = (
        "purchase_transaction_batch_created"  # Purchase transaction batch created
    )
    PURCHASE_TRANSACTION_CREATED = "purchase_transaction_created"  # Transaction created
    PURCHASE_TRANSACTION_DELETED = "purchase_transaction_deleted"  # Transaction deleted
    PURCHASE_TRANSACTION_EXECUTING = (
        "purchase_transaction_executing"  # Payment in execution
    )
    PURCHASE_TRANSACTION_PAID = "purchase_transaction_paid"  # Payment succeeded
    PURCHASE_TRANSACTION_PENDING = "purchase_transaction_pending"  # Payment pending
    PURCHASE_TRANSACTION_REJECTED = "purchase_transaction_rejected"  # Payment rejected
    PURCHASE_TRANSACTION_TECHNICALLY_VALIDATED = "purchase_transaction_technically_validated"  # Payment technically approved by the bank

    RECURRING_SALES_INVOICE = "recurring_sales_invoice"

    RECURRING_SALES_INVOICE_AUTO_SEND_FORCEFULLY_DISABLED = "recurring_sales_invoice_auto_send_forcefully_disabled"  # The invoice could not be sent automatically, sending automatically is disabled
    RECURRING_SALES_INVOICE_CREATED = (
        "recurring_sales_invoice_created"  # Recurring invoice created
    )
    RECURRING_SALES_INVOICE_CREATED_FROM_ORIGINAL = "recurring_sales_invoice_created_from_original"  # Recurring sales invoice created based on original invoice
    RECURRING_SALES_INVOICE_CREATED_FROM_ORIGINAL_RECURRING = "recurring_sales_invoice_created_from_original_recurring"  # Recurring invoices created based on the original recurring invoice
    RECURRING_SALES_INVOICE_CREATING_SKIPPED_DUE_TO_LIMITS = "recurring_sales_invoice_creating_skipped_due_to_limits"  # You have reached the maximum amount of invoices for this month. The recurring invoice is not created.
    RECURRING_SALES_INVOICE_DEACTIVATED = (
        "recurring_sales_invoice_deactivated"  # Recurring invoice deactivated
    )
    RECURRING_SALES_INVOICE_DESTROYED = (
        "recurring_sales_invoice_destroyed"  # Recurring invoice deleted
    )
    RECURRING_SALES_INVOICE_INVOICE_CREATED = (
        "recurring_sales_invoice_invoice_created"  # Sales invoice created
    )
    RECURRING_SALES_INVOICE_STARTED_AUTO_SEND = (
        "recurring_sales_invoice_started_auto_send"  # Sending automatically enabled
    )
    RECURRING_SALES_INVOICE_STOPPED_AUTO_SEND = (
        "recurring_sales_invoice_stopped_auto_send"  # Sending automatically disabled
    )
    RECURRING_SALES_INVOICE_UPDATED = (
        "recurring_sales_invoice_updated"  # Recurring invoice updated
    )

    SALES_INVOICE = "sales_invoice"

    SALES_INVOICE_CREATED = "sales_invoice_created"  # Invoice created
    SALES_INVOICE_CREATED_BASED_ON_ESTIMATE = (
        "sales_invoice_created_based_on_estimate"  # Invoice created based on quote
    )
    SALES_INVOICE_CREATED_BASED_ON_RECURRING = "sales_invoice_created_based_on_recurring"  # Invoice created based on recurring invoice
    SALES_INVOICE_CREATED_BASED_ON_SUBSCRIPTION = "sales_invoice_created_based_on_subscription"  # Invoice created based on subscription
    SALES_INVOICE_CREATED_FROM_CHECKOUT_ORDER = "sales_invoice_created_from_checkout_order"  # Sales invoice created through checkout
    SALES_INVOICE_CREATED_FROM_ORIGINAL = "sales_invoice_created_from_original"  # Invoice created based on original invoice
    SALES_INVOICE_DESTROYED = "sales_invoice_destroyed"  # Invoice deleted
    SALES_INVOICE_MARKED_AS_DUBIOUS = (
        "sales_invoice_marked_as_dubious"  # Invoice marked as dubious
    )
    SALES_INVOICE_MARKED_AS_UNCOLLECTIBLE = (
        "sales_invoice_marked_as_uncollectible"  # Invoice was marked as irrecoverable
    )
    SALES_INVOICE_MERGED = "sales_invoice_merged"  # Invoice has been merged with another invoice before sending
    SALES_INVOICE_MERGED_WITH_RECURRING_SALES_INVOICE = "sales_invoice_merged_with_recurring_sales_invoice"  # Invoice has been merged with other recurring invoices before sending
    SALES_INVOICE_PAUSED = (
        "sales_invoice_paused"  # Processing of invoice has been paused
    )
    SALES_INVOICE_REVERT_DUBIOUS = (
        "sales_invoice_revert_dubious"  # Revert marking as dubious
    )
    SALES_INVOICE_REVERT_UNCOLLECTIBLE = (
        "sales_invoice_revert_uncollectible"  # Invoice marked as uncollectible
    )
    SALES_INVOICE_SEND_EMAIL = "sales_invoice_send_email"  # Invoice sent by email
    SALES_INVOICE_SEND_MANUALLY = (
        "sales_invoice_send_manually"  # Invoice manually marked as sent
    )
    SALES_INVOICE_SEND_POST = "sales_invoice_send_post"  # Invoice sent by mail
    SALES_INVOICE_SEND_POST_CONFIRMATION = (
        "sales_invoice_send_post_confirmation"  # Invoice sent via mail by Moneybird
    )
    SALES_INVOICE_SEND_POST_CANCELLED = (
        "sales_invoice_send_post_cancelled"  # Sending by mail cancelled
    )
    SALES_INVOICE_SEND_REMINDER_EMAIL = "sales_invoice_send_reminder_email"  # Reminder for this sales invoice sent by email
    SALES_INVOICE_SEND_REMINDER_MANUALLY = (
        "sales_invoice_send_reminder_manually"  # Reminder sent manually
    )
    SALES_INVOICE_SEND_REMINDER_POST = (
        "sales_invoice_send_reminder_post"  # Reminder sent by mail
    )
    SALES_INVOICE_SEND_REMINDER_POST_CONFIRMATION = "sales_invoice_send_reminder_post_confirmation"  # Invoice reminder sent by mail by Moneybird
    SALES_INVOICE_SEND_SI = "sales_invoice_send_si"  # Invoice sent via Peppol
    SALES_INVOICE_SEND_SI_DELIVERED = (
        "sales_invoice_send_si_delivered"  # Received Peppol delivery notification
    )
    SALES_INVOICE_SEND_SI_ERROR = (
        "sales_invoice_send_si_error"  # An error occurred while sending via Peppol
    )
    SALES_INVOICE_SEND_TO_PAYT = (
        "sales_invoice_send_to_payt"  # Invoice forwarded to Online incasso
    )
    SALES_INVOICE_STATE_CHANGED_TO_DRAFT = (
        "sales_invoice_state_changed_to_draft"  # Invoice state changed to draft
    )
    SALES_INVOICE_STATE_CHANGED_TO_LATE = (
        "sales_invoice_state_changed_to_late"  # Invoice has expired
    )
    SALES_INVOICE_STATE_CHANGED_TO_OPEN = (
        "sales_invoice_state_changed_to_open"  # State of invoice changed to open
    )
    SALES_INVOICE_STATE_CHANGED_TO_PAID = (
        "sales_invoice_state_changed_to_paid"  # Invoice has been paid
    )
    SALES_INVOICE_STATE_CHANGED_TO_PENDING_PAYMENT = (
        "sales_invoice_state_changed_to_pending_payment"  # Invoice is pending payment
    )
    SALES_INVOICE_STATE_CHANGED_TO_REMINDED = (
        "sales_invoice_state_changed_to_reminded"  # Invoice state changed to reminded
    )
    SALES_INVOICE_STATE_CHANGED_TO_SCHEDULED = (
        "sales_invoice_state_changed_to_scheduled"  # Invoice state changed to scheduled
    )
    SALES_INVOICE_STATE_CHANGED_TO_UNCOLLECTIBLE = "sales_invoice_state_changed_to_uncollectible"  # Invoice state changed to uncollectible
    SALES_INVOICE_UNPAUSED = (
        "sales_invoice_unpaused"  # Processing of invoice has been resumed
    )
    SALES_INVOICE_UPDATED = "sales_invoice_updated"  # Invoice updated
    SEND_PAYMENT_EMAIL = "send_payment_email"  # Payment notification email sent
    SEND_PAYMENT_UNSUCCESSFUL_EMAIL = (
        "send_payment_unsuccessful_email"  # Email after a failed payment sent
    )

    SUBGOAL = "subgoal"

    SUBGOAL_ASSIGNED = "subgoal_assigned"  # Step assigned
    SUBGOAL_COMPLETED = "subgoal_completed"  # Step completed
    SUBGOAL_UNCOMPLETED = "subgoal_uncompleted"  # Step not completed

    SUBSCRIPTION = "subscription"

    SUBSCRIPTION_CANCELLED = "subscription_cancelled"  # Subscription cancelled
    SUBSCRIPTION_CREATED = "subscription_created"  # Subscription created
    SUBSCRIPTION_DESTROYED = "subscription_destroyed"  # Subscription deleted
    SUBSCRIPTION_EDITED = "subscription_edited"  # Plan changed
    SUBSCRIPTION_UPDATED = "subscription_updated"  # Subscription updated

    TAX_RATE = "tax_rate"

    TAX_RATE_ACTIVATED = "tax_rate_activated"  # Activate VAT rate
    TAX_RATE_CREATED = "tax_rate_created"  # VAT rate added
    TAX_RATE_DEACTIVATED = "tax_rate_deactivated"  # VAT rate deactivated
    TAX_RATE_DESTROYED = "tax_rate_destroyed"  # VAT rate deleted
    TAX_RATE_UPDATED = "tax_rate_updated"  # VAT rate updated

    TIME_ENTRY = "time_entry"

    TIME_ENTRY_CREATED = "time_entry_created"  # Time entry created
    TIME_ENTRY_DESTROYED = "time_entry_destroyed"  # Time entry destroyed
    TIME_ENTRY_SALES_INVOICE_CREATED = (
        "time_entry_sales_invoice_created"  # Time entry invoiced
    )
    TIME_ENTRY_UPDATED = "time_entry_updated"  # Time entry updated

    TODO = "todo"

    TODO_COMPLETED = "todo_completed"  # To-do completed
    TODO_CREATED = "todo_created"  # To-do added
    TODO_DESTROYED = "todo_destroyed"  # To-do deleted
    TODO_OPENED = "todo_opened"  # To-do viewed

    ULTIMATE_BENIFICIAL_OWNER = "ultimate_benificial_owner"

    ULTIMATE_BENIFICIAL_OWNER_CREATED = (
        "ultimate_benificial_owner_created"  # Ultimate beneficial owner created
    )
    ULTIMATE_BENIFICIAL_OWNER_UPDATED = (
        "ultimate_benificial_owner_updated"  # Ultimate beneficial owner updated
    )

    USER = "user"

    USER_INVITED = "user_invited"  # User invited
    USER_INVITED_FOR_CALL = "user_invited_for_call"  # User invited for a call
    USER_REMOVED = "user_removed"  # User deleted

    VAT_RETURN = "vat_return"

    VAT_RETURN_CREATED = "vat_return_created"  # VAT-return filed
    VAT_RETURN_RECEIVED = (
        "vat_return_received"  # VAT-return is received by the tax authorities
    )
    VAT_RETURN_PAID = "vat_return_paid"  # VAT-return paid
    VAT_SUPPLETION_CREATED = (
        "vat_suppletion_created"  # Digital VAT suppletion submitted
    )
    VAT_SUPPLETION_RECEIVED = "vat_suppletion_received"  # Electronic vat-suppletion is received by the tax authority

    WORKFLOW = "workflow"

    WORKFLOW_CREATED = "workflow_created"  # Workflow added
    WORKFLOW_DEACTIVATED = "workflow_deactivated"  # Workflow deactivated
    WORKFLOW_DESTROYED = "workflow_destroyed"  # Workflow deleted
    WORKFLOW_UPDATED = "workflow_updated"  # Workflow updated
