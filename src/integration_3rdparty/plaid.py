from django.conf import settings
from plaid import Client

# Available environments are 'sandbox', 'development', and 'production'.
client = Client(client_id=settings.PLAID_API['CLIENT_ID'],
                secret=settings.PLAID_API['SECRET'],
                environment=settings.PLAID_API['ENVIRONMENT'])


class PlaidManagement(object):
    @staticmethod
    def get_transaction(access_token: str, from_date: str, to_date: str):
        response = client.Transactions.get(access_token, start_date=from_date, end_date=to_date)
        transactions = response['transactions']
        while len(transactions) < response['total_transactions']:
            response = client.Transactions.get(access_token, start_date=from_date, end_date=to_date,
                                               offset=len(transactions)
                                               )
            transactions.extend(response['transactions'])

        return transactions

    @staticmethod
    def get_categories():
        categories = client.Categories.get()
        cats = []
        for cat in categories['categories']:
            cats.extend(cat['hierarchy'])

        print(set(cats))
        return cats
