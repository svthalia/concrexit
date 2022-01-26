# Registrations

This document explains how the registrations module behaviour is defined.
The behaviour of upgrading an existing 'year' membership to a 'study' membership (until graduation) are taken from the Rules and Regulations. If the Rules and Regulations ever change this behaviour should be changed to reflect those changes.

This module both provides registration for members and for benefactors. The only difference is the form and view used for their registration since the information we ask from them is different.


## New member/benefactor registration

### Frontend

- User enters information
    - If the membership type is 'benefactor':
        The amount used in the payment is provided during the registration process by the user.
- User accepts privacy policy
    This step is obligatory. We do not accept people that do not accept the privacy policy. It's currently implemented as a checkbox in the forms.
- System validates info
    - Correct address
    - Valid and unique email address
        - Checked against existing users
    - Privacy policy accepted
    - If the selected membership type is 'member':
        - valid and unique student number
            - Checked against existing users
        - selected programme
        - cohort
- Registration model created (status: Awaiting email confirmation)
- If the membership type is 'member':
    - Contribution is calculated based on selected length ('study' or 'year')
            - Values are located in thaliawebsite.settings
- Email address confirmation sent
- User confirms email address
- Registration model status changed (status: Ready for review)
- If the registration is for a benefactor an email is sent with a link to get references
    - Existing members of Thalia add references using the link

### Backend

1. Admin accepts registration
    - System checks if username is unique
        - If it's not unique a username can be entered manually
        - If it's still not unique the registration cannot be accepted
        - If it's unique the generated username will be added to the registration
    - If the membership type is 'benefactor':
        - Amount is determined by the value entered during registration
    - Email is sent as acceptance confirmation containing instructions for [Payment processing](#payment-processing)
2. Admin rejects registration
    - Email is sent as rejection message


## Existing user membership renewal

### Frontend

- User enters information (length, type)
    - If latest membership has not ended yet: always allow 'study' length
    - If latest membership has ended or ends within 1 month: also allow 'year' length
    - If latest membership is 'study' and did not end: do not allow renewal
    - If the membership type is 'member':
        - Contribution is calculated based on selected length ('study' or 'year')
            - Values are located in thaliawebsite.settings
            - If the current membership has not ended yet and an until date is present for that membership and
              the selected length is 'study' the amount will be `price['study'] - price['year']`
- Renewal model created (status: Ready for review)
- If the renewal is for a benefactor an email is sent with a link to get references
    - Existing members of Thalia add references using the link

### Backend

1. Admin accepts renewal
    - Email is sent as acceptance confirmation containing instructions for [Payment processing](#payment-processing)
2. Admin rejects renewal
    - Email is sent as rejection message


## Payment processing

## Backend

- Admin (or the system, if automated using e.g. iDeal) creates payment
    - If this is a Registration model then User and Member models are created
    - If this is a Renewal model then the Member is retrieved
    - A membership is added to the provided Member model based on the provided length
        - If the **latest** (*not current, since there may have been some time between asking for the upgrade and accepting it*) membership has an until date and
             the selected length is 'study' that membership will be updated to have None as until date. No new membership will be created.
        - During a lecture year the until date will be the 31 August of the lecture year + 1. Thus is you process payments in November 2016 that means the memberships will end on 31 August 2017
        - For payments processed in August the lecture year will be increased by 1. So if you process payments in August 2017 that means the memberships will end on 31 August 2018.
    - If this is a Renewal model then the Payment confirmation sent

