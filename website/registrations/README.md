# Registrations

This document explains how the registrations module behaviour is defined. The behaviour of this app
should implement the Rules and Regulations of Thalia. If the Rules and Regulations ever change this
app should be updated to reflect those changes.

The functionality of this app is mainly to automate the creation of `members.Membership`s, providing
a way for prospective members to enter their profile information, for the board to review and accept
registrations and renewals, and to process their payments.

The flows that take place can be divided in two: registrations, where new members or benefactors are
made, and renewals, where existing members renew their membership.


> This app is very important for Thalia, and it is mainly used only at the beginning of the year. This means that we need to be very sure it works correctly. Hence, we require complete test coverage for this app.


## New member or benefactor registrations

1. The user enters information.
    - If the membership type is 'benefactor' the contribution amount is provided by the user, with a minimum.
2. The user accepts the privacy policy. This step is obligatory. We do not accept people that do not accept the privacy policy.
3. The form is saved, creating a `Registration`. We validate the filled in data:
    - The address and other fields are well-formed.
    - The user's email address is unique and valid.
    - The privacy policy is accepted.
    - If the selected membership type is 'member':
        - The student number is unique and valid.
        - A programme and cohort is selected.
4. An email is sent to the user asking to verify their email address.
5. The user confirms their email address.
    - If the membership type is 'benefactor', and the user is not iCIS staff (who are exempt from having to provide references),
      an email is sent to the user explaining that they need to provide references. It contains a URL that existing members of
      Thalia can use to provide a reference for the prospective benefactor.
    - An email is sent to the board, notifying them of the new registration.
6. The board accepts the registration.
    - If the registration has direct debit payment information, a Thalia Pay payment is
      automatically created, and the registration is completed.
    - Otherwise, an email is sent to the user explaining that they need to pay their contribution.
7. The user pays their contribution. Then, a `Member` and `Membership` are created, and an email
    is sent to the user with their username and password.

If the automatically created username is not unique, the board can override it by setting a username on the registration in the admin.

## Existing member renewals

1. The user creates a `Renewal`. The possible options depend on the user's current membership, and the current date.
    - They pick a length (year or study, if the user is a 'member').
    - They indicate whether they still are 'member' or want to become a 'benefactor'.
    - If 'benefactor', the user picks a contribution amount (with minimum).
    - A 'member' with a current 'year' membership can upgrade to a 'study' membership. There is a discount for this.
    - An expired 'member' can get a new 'study' membership. This is currently not discounted, but this may change depending on the Rules and Regulations.
    - An expired or current 'member' can get a new 'year' membership for the current year, or in August for the next year.

2. If the user is a benefactor and not a previous 'member', the user gets an email with a link for references.
3. The board accepts the renewal. The user gets an email telling them to pay.
4. Once a payment is made, a membership is created or extended.
