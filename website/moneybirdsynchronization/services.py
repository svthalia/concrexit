def get_financial_account_id(api, name):
    for financial_account in api.get("financial_accounts"):
        if financial_account["name"] == name:
            return financial_account["id"]