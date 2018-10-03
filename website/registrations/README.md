Registrations
=====

This document explains how the registrations module behaviour is defined.
The behaviour of upgrading an existing 'year' membership to a 'study' membership (until graduation) is taken from the HR. If the HR ever changes this behaviour should be changed to reflect those changes.

_Note that registrations and renewals for benefactors are implemented in the models, there are simply no views providing this functionality. If we ever want to implement this then it would be best to create a complete new form just for benefactors registrations._

## New member registration

### Frontend

- User enters information
- User accepts privacy policy
- System validates info
	- Correct address
	- Valid and unique email address
		- Checked against existing users
	- Privacy policy accepted
	- If the selected member type is 'member':
	    - valid and unique student number
	    - selected programme
	    - cohort
- Registration model created (status: Awaiting email confirmation)
- Email address confirmation sent
- User confirms email address
- Registration model status changed (status: Ready for review)

### Backend

1. Admin accepts registration
	- System checks if username is unique
		- If it's not unique a username can be entered manually
		- If it's still not unique the registration cannot be accepted
		- If it's unique the generated username will be added to the registration
	- Payment model is created (processed: False)
		- Amount is calculated based on the selected length ('study' or 'year')
			- Values are located in thaliawebsite.settings
		- Email is sent as acceptance confirmation containg instructions for [payment](#payment-processing)
2. Admin rejects registration
	- Email is sent as rejection message


## Existing user membership renewal

### Frontend

- User enters information (length, type)
	- If latest membership has not ended yet: always allow 'study' length
	- If latest membership has ended or ends within 1 month: also allow 'year' length
	- If latest membership is 'study' and did not end: do not allow renewal
- Renewal model created (status: Ready for review)

### Backend

1. Admin accepts renewal
	- Payment model is created (processed: False)
		- Amount is calculated based on selected length ('study' or 'year')
			- Values are located in thaliawebsite.settings
			- If the current membership has not ended yet and an until date is present for that membership and
			 the selected length is 'study' the amount will be price['study'] - price['year']
		- Email is sent as acceptance confirmation containg instructions for [payment](#payment-processing)
2. Admin rejects renewal
	- Email is sent as rejection message


## Payment processing

### Backend

- Admin (or the system, if automated using e.g. iDeal) processes payment
	- If this is a Registration model then User and Member models are created
	- If this is a Renewal model then the Member is retrieved
	- A membership is added to the provided Member model based on the provided length
	    - If the __latest__ (_not current, since there may have been some time between asking for the upgrade and accepting it_) membership has an until date and
			 the selected length is 'study' that membership will be updated to have None as until date. No new membership will be created.
	    - During a lecture year the until date will be the 31 August of the lecture year + 1. Thus is you process payments in November 2016 that means the memberships will end on 31 August 2017
	    - For payments processed in August the lecture year will be increased by 1. So if you process payments in August 2017 that means the memberships will end on 31 August 2018.
	- Payment confirmation sent (if this is a Renewal model)

