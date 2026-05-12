import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

def create_auth():
    config = {
        'credentials': {
            'usernames': {
                'admin': {
                    'email': 'admin@trading.com',
                    'name': 'Admin',
                    'password': '$2b$12$CgL7PLUGsmhFbR9M4oPbV.W86UTeLjnyy6ZE0R.pClnt9gp0TEkqK'
                },
                'trader': {
                    'email': 'trader@trading.com',
                    'name': 'Trader',
                    'password': '$2b$12$CgL7PLUGsmhFbR9M4oPbV.W86UTeLjnyy6ZE0R.pClnt9gp0TEkqK'
                }
            }
        },
        'cookie': {
            'expiry_days': 30,
            'key': 'trading_dashboard_key',
            'name': 'trading_cookie'
        },
        'pre-authorized': {
            'emails': ['admin@trading.com']
        }
    }

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    return authenticator