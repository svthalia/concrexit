def moneybird_data(self, info):
        return {
            "external_invoice": {
                "contact_id": info["contact_id"],
                "reference": self.id,
                "date": self.created_at.date().isoformat(),
                "currency": "EUR",
                "prices_are_incl_tax": True,
                "details_attributes":[
                    {
                        "description": self.topic,
                        "price": self.amount,
                        "ledger_account_id": settings.MONEYBIRD_LEDGER_ACCOUNT_ID,
                        "project_id": info["project_id"],
                    },
                ],
            }
        }