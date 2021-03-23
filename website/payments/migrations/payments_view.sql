CREATE VIEW payments_paymentuser AS
SELECT
    "auth_user"."id" as "id",
	"auth_user"."id" as "user_ptr_id",
	COALESCE("payments_allowed"."tpay_allowed", false) as "tpay_allowed",
	COALESCE("payments_balance"."tpay_balance", 0) as "tpay_balance",
	COALESCE(("payments_allowed"."tpay_allowed" AND "payments_valid_bankaccount"."has_valid_bankaccount"), false) AS "tpay_enabled"
FROM
	"auth_user"
	-- Union of possible ways a user can be allowed to use thalia pay
	LEFT JOIN (
		-- User has individual permission for tpay_allowed
		SELECT
			"auth_user_user_permissions"."user_id" AS "user_id",
			TRUE AS "tpay_allowed"
		FROM
			"auth_permission"
			INNER JOIN "auth_user_user_permissions" ON ("auth_permission"."id" = "auth_user_user_permissions"."permission_id")
			INNER JOIN "django_content_type" ON ("auth_permission"."content_type_id" = "django_content_type"."id")
		WHERE
			"django_content_type"."app_label" = 'payments'
			AND "auth_permission"."codename" = 'tpay_allowed'
	UNION
		-- User belongs to a group which has tpay_allowed
		SELECT
			"auth_user_groups"."user_id" AS "user_id",
			TRUE AS "tpay_allowed"
		FROM
			"auth_permission"
			INNER JOIN "auth_group_permissions" ON ("auth_permission"."id" = "auth_group_permissions"."permission_id")
			INNER JOIN "auth_group" ON ("auth_group_permissions"."group_id" = "auth_group"."id")
			INNER JOIN "auth_user_groups" ON ("auth_group"."id" = "auth_user_groups"."group_id")
			INNER JOIN "django_content_type" ON ("auth_permission"."content_type_id" = "django_content_type"."id")
		WHERE
			"django_content_type"."app_label" = 'payments'
			AND "auth_permission"."codename" = 'tpay_allowed'
	UNION
		-- User belongs to a membergroup which has tpay_allowed
		SELECT
			"activemembers_membergroupmembership"."member_id" AS "user_id",
			TRUE AS "tpay_allowed"
		FROM
			"activemembers_membergroupmembership"
			INNER JOIN "activemembers_membergroup" ON "activemembers_membergroup"."id" = "activemembers_membergroupmembership"."group_id"
			INNER JOIN "activemembers_membergroup_permissions" ON "activemembers_membergroup_permissions"."membergroup_id" = "activemembers_membergroup"."id"
			INNER JOIN "auth_permission" ON "auth_permission"."id" = "activemembers_membergroup_permissions"."permission_id"
			INNER JOIN "django_content_type" ON "django_content_type"."id" = "auth_permission"."content_type_id"
		WHERE ("activemembers_membergroupmembership"."until" >= CURRENT_DATE
			OR "activemembers_membergroupmembership"."until" IS NULL)
		AND "django_content_type"."app_label" = 'payments'
		AND "auth_permission"."codename" = 'tpay_allowed'
	UNION
		-- User is superuser
		SELECT
			"auth_user"."id" AS "user_id",
			TRUE AS "tpay_allowed"
		FROM
			"auth_user"
		WHERE
			"is_superuser" = TRUE
	) AS "payments_allowed" ON "auth_user"."id" = "payments_allowed"."user_id"
	-- User has valid bank account
	LEFT JOIN (
		SELECT
			"payments_bankaccount"."owner_id" AS "user_id", TRUE AS "has_valid_bankaccount"
		FROM
			"payments_bankaccount"
		WHERE
			"payments_bankaccount"."valid_from" IS NOT NULL
			AND "payments_bankaccount"."valid_from" <= CURRENT_DATE
			AND("payments_bankaccount"."valid_until" IS NULL
				OR "payments_bankaccount"."valid_until" >= CURRENT_DATE)
	) AS "payments_valid_bankaccount" ON "auth_user"."id" = "payments_valid_bankaccount"."user_id"
	-- Balance since last processed batch
	LEFT JOIN (
		SELECT
			"payments_payment"."paid_by_id" AS "user_id",
			-(SUM("payments_payment"."amount")) AS "tpay_balance"
		FROM
			"payments_payment"
			LEFT JOIN "payments_batch" ON "payments_payment"."batch_id" = "payments_batch"."id"
		WHERE
			"payments_payment"."type" = 'tpay_payment'
			AND("payments_payment"."batch_id" IS NULL
				OR "payments_batch"."processed" = FALSE)
		GROUP BY
			"payments_payment"."paid_by_id"
	) AS "payments_balance" ON "auth_user"."id" = "payments_balance"."user_id";
