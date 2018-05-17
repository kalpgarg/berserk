# -*- coding: utf-8 -*-
import json
import urllib

import requests


class NdJsonDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def decode(self, s, *args, **kwargs):
        lines = ','.join(s.splitlines())
        return super().decode(f'[{lines}]', *args, **kwargs)


class LiSession:
    def __init__(self, session=None):
        if session is None:
            session = requests.Session()
        self.session = session

    def __getattr__(self, name):
        return getattr(self.session, name)

    # hook into here to log exceptions
    def request(self, *args, **kwargs):
        response = self.session.request(*args, **kwargs)
        # response.raise_for_status()
        return response

    # use json mixin instead?
    def get(self, *args, **kwargs):
        response = self.session.get(*args, **kwargs)
        return response.json()

    def get_stream(self, *args, **kwargs):
        with self.session.get(*args, stream=True, **kwargs) as r:
            for line in r.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    yield json.loads(decoded_line)

    def get_ndjson(self, *args, **kwargs):
        response = self.session.get(*args, **kwargs)
        return json.loads(response.text, cls=NdJsonDecoder)


class TokenSession(LiSession):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.session.headers = {'Authorization': f'Bearer {token}'}


class Client:
    base_url = 'https://lichess.org/'

    def __init__(self, session, base_url=None):
        self.base_url = base_url or self.base_url
        self.session = session

    def get_account(self):
        url = urllib.parse.urljoin(self.base_url, 'api/account')
        return self.session.get(url)

    def get_account_email(self):
        url = urllib.parse.urljoin(self.base_url, 'api/account/email')
        return self.session.get(url)

    def get_account_preferences(self):
        url = urllib.parse.urljoin(self.base_url, 'api/account/preferences')
        return self.session.get(url)

    def get_account_kid(self):
        url = urllib.parse.urljoin(self.base_url, 'api/account/kid')
        return self.session.get(url)

    def get_users_status(self, *user_ids):
        url = urllib.parse.urljoin(self.base_url, 'api/users/status')
        return self.session.get(url, params={'ids': ','.join(user_ids)})

    def get_player(self):
        headers = {'Accept': 'application/vnd.lichess.v3+json'}
        url = urllib.parse.urljoin(self.base_url, 'player')
        return self.session.get(url, headers=headers)

    def get_player_top(self, perf, count=10):
        headers = {'Accept': 'application/vnd.lichess.v3+json'}
        url = urllib.parse.urljoin(self.base_url, f'player/top/{count}/{perf}')
        return self.session.get(url, headers=headers)

    def get_user(self, username):
        url = urllib.parse.urljoin(self.base_url, f'api/user/{username}')
        return self.session.get(url)

    def get_user_activity(self, username):
        url = urllib.parse.urljoin(self.base_url,
                                   f'api/user/{username}/activity')
        return self.session.get(url)

    def get_team_users(self, team_id):
        url = urllib.parse.urljoin(self.base_url, f'team/{team_id}/users')
        return self.session.get_ndjson(url)

    def get_stream_event(self):
        url = urllib.parse.urljoin(self.base_url, 'api/stream/event')
        stream = self.session.get_stream(url)
        for line in stream:
            yield line

    def get_bot_game_stream(self, game_id):
        url = urllib.parse.urljoin(self.base_url,
                                   f'api/bot/game/stream/{game_id}')
        stream = self.session.get_stream(url)
        for line in stream:
            yield line

    def get_tournament(self):
        url = urllib.parse.urljoin(self.base_url, 'api/tournament')
        return self.session.get(url)


class TokenClient(Client):
    def __init__(self, token):
        token_session = TokenSession(token=token)
        super().__init__(session=token_session)


""" Example usage:
import berserk


with open('.lichess.org') as f:
    token = f.read().strip()

client = berserk.TokenClient(token=token)
"""
