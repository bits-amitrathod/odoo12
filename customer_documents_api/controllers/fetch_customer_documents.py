# -*- coding: utf-8 -*-

import requests
import json

# ---- Configuration ----
ODOO_URL = 'http://localhost:8070'
DATABASE = 'feb_12'
LOGIN = 'info@surgicalproductsolutions.com'
PASSWORD = '$P$2019@$$'
PARTNER_ID = 1929  # Change to the customer/partner ID you want to fetch documents for


def authenticate(session, url, db, login, password):
    """Authenticate with Odoo and return session with cookies."""
    auth_url = '%s/web/session/authenticate' % url
    payload = {
        'jsonrpc': '2.0',
        'params': {
            'db': db,
            'login': login,
            'password': password,
        },
    }
    response = session.post(auth_url, json=payload)
    result = response.json()

    if result.get('error'):
        raise Exception('Authentication failed: %s' % result['error']['data']['message'])

    print('Authenticated successfully as: %s' % login)
    return session


def fetch_customer_documents(session, url, partner_id):
    """Fetch documents for a given partner/customer ID."""
    endpoint = '%s/api/customer/documents/%s' % (url, partner_id)
    response = session.get(endpoint)

    if response.status_code == 200:
        return response.json()
    else:
        print('Error: HTTP %s' % response.status_code)
        return response.json()


if __name__ == '__main__':
    session = requests.Session()

    # Step 1: Authenticate
    session = authenticate(session, ODOO_URL, DATABASE, LOGIN, PASSWORD)

    # Step 2: Fetch customer documents
    result = fetch_customer_documents(session, ODOO_URL, PARTNER_ID)

    # Step 3: Print response
    print(json.dumps(result, indent=2))
