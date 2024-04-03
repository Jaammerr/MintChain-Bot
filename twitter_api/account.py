import asyncio
import hashlib
import math
import mimetypes
import platform
import secrets
import httpx

from copy import deepcopy
from datetime import datetime
from string import ascii_letters
from typing import Coroutine
from uuid import uuid1, getnode

from curl_cffi import requests
from curl_cffi.requests.session import Response
from httpx import Cookies, Headers
from tqdm import tqdm

from .models import *
from .constants import *
from .errors import TwitterAccountSuspended, RateLimitError
from .models import BindAccountDataV1
from .util import *

# logging.getLogger("httpx").setLevel(logging.WARNING)

if platform.system() != "Windows":
    try:
        import uvloop

        uvloop.install()
    except ImportError as e:
        ...


class Account:
    def __init__(self):
        self._session: requests.Session = requests.Session()
        self._proxy: str = ""
        self._reformatted_proxy: str = ""

        self.gql_api = "https://twitter.com/i/api/graphql"
        self.v1_api = "https://api.twitter.com/1.1"
        self.v2_api = "https://twitter.com/i/api/2"

    @classmethod
    def run(
        cls,
        auth_token: str = None,
        cookies: dict[str] = None,
        proxy: str = None,
        setup_session: bool = True,
    ) -> "Account":
        account = cls()
        account._proxy = proxy
        if proxy:
            if proxy.startswith("http://"):
                account._session = requests.Session(
                    proxies={"http://": account.proxy}, timeout=30, verify=False
                )
                account._reformatted_proxy = account.proxy

            else:
                account._reformatted_proxy = account.get_reformatted_proxy
                account._session = requests.Session(
                    proxies=(
                        {"http://": account._reformatted_proxy}
                        if account._reformatted_proxy
                        else None
                    ),
                    timeout=30,
                    verify=False,
                )

        if not (auth_token, cookies):
            raise TwitterError(
                {
                    "error_message": "Failed to authenticate account. You need to set cookies or auth_token."
                }
            )

        if setup_session:
            if auth_token:
                account.session.cookies.update({"auth_token": auth_token})
                account.setup_session()
            else:
                account.session.cookies.update(cookies)

        else:
            if not account.session.cookies.get(
                "auth_token"
            ) and not account.session.cookies.get("ct0"):
                account.session.cookies.update({"auth_token": auth_token})
                account.setup_session()
            else:
                account.session.cookies.update(cookies)

        return account

    @property
    def get_auth_data(self) -> dict:
        return {
            "auth_token": self.auth_token,
            "cookies": dict(self.cookies),
            "proxy": self.proxy,
        }

    def gql(
        self,
        method: str,
        operation: tuple,
        variables: dict,
        features: dict = Operation.default_features,
    ) -> dict:
        qid, op = operation
        params = {
            "queryId": qid,
            "features": features,
            "variables": Operation.default_variables | variables,
        }
        if method == "POST":
            data = {"json": params}
        else:
            data = {"params": {k: orjson.dumps(v).decode() for k, v in params.items()}}

        r = self.session.request(
            method=method,
            url=f"{self.gql_api}/{qid}/{op}",
            headers=get_headers(self.session),
            allow_redirects=True,
            **data,
        )

        return self._verify_response(r)

    def v1(self, path: str, params: dict) -> dict:
        headers = get_headers(self.session)
        headers["content-type"] = "application/x-www-form-urlencoded"
        r = self.session.post(
            f"{self.v1_api}/{path}", headers=headers, data=params, allow_redirects=True
        )
        return self._verify_response(r)

    @staticmethod
    def _verify_response(r: Response) -> dict:
        try:
            rate_limit_remaining = r.headers.get("x-rate-limit-remaining")
            if rate_limit_remaining and int(rate_limit_remaining) in (0, 1):
                reset_ts = int(r.headers.get("x-rate-limit-reset"))
                raise RateLimitError(
                    f"Rate limit reached. Reset in {reset_ts - int(time.time())} seconds. "
                )
                # logger.info(
                #     f"Rate limit reached | Reset in {reset_ts - int(time.time())} seconds | Sleeping..."
                # )
                # current_ts = int(time.time())
                # difference = reset_ts - current_ts
                # asyncio.sleep(difference)

            data = r.json()
        except ValueError:
            raise TwitterError(
                {
                    "error_message": f"Failed to parse response: {r.text}. "
                    "If you are using proxy, make sure it is not blocked by Twitter."
                }
            )

        if "errors" in data:
            error_message = (
                data["errors"][0].get("message") if data["errors"] else data["errors"]
            )

            error_code = data["errors"][0].get("code") if data["errors"] else None

            if isinstance(error_message, str) and error_message.lower().startswith(
                "to protect our users from spam and other"
            ):
                raise TwitterAccountSuspended(error_message)

            raise TwitterError(
                {
                    "error_code": error_code,
                    "error_message": error_message,
                }
            )

        try:
            r.raise_for_status()
        except httpx.HTTPError as http_error:
            raise TwitterError(
                {
                    "error_message": str(http_error),
                }
            )

        return data

    @property
    def proxy(self):
        return self._proxy

    @property
    def get_reformatted_proxy(self):
        try:
            if self.proxy is None:
                return None

            ip, port, username, password = self.proxy.split(":")
            return f"http://{username}:{password}@{ip}:{port}"

        except (ValueError, AttributeError):
            raise TwitterError(
                {
                    "error_message": "Failed to parse proxy. "
                    "Make sure you are using correct proxy format: "
                    "ip:port:username:password"
                }
            )

    @property
    def session(self):
        return self._session

    @property
    def cookies(self) -> Cookies:
        return self._session.cookies

    @property
    def headers(self) -> Headers:
        return self._session.headers

    @property
    def auth_token(self) -> str:
        return self._session.cookies.get("auth_token", "")

    @property
    def ct0(self) -> str:
        return self._session.cookies.get("ct0", "")

    def request_ct0(self) -> str:
        url = "https://twitter.com/i/api/2/oauth2/authorize"
        r = self.session.get(url, allow_redirects=True)

        if "ct0" in r.cookies:
            return r.cookies.get("ct0")
        else:
            raise TwitterError(
                {
                    "error_message": "Failed to get ct0 token. "
                    "Make sure you are using correct cookies."
                }
            )

    def request_guest_token(
        self, session: requests.Session, csrf_token: str = None
    ) -> str:
        if not (csrf_token, self.session.cookies.get("ct0", "")):
            raise TwitterError(
                {
                    "error_message": "Failed to get guest token. "
                    "Make sure you are using correct cookies."
                }
            )

        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "x-csrf-token": (
                csrf_token if csrf_token else self.session.cookies.get("ct0")
            ),
        }
        r = session.post(
            f"{self.v1_api}/guest/activate.json",
            headers=headers,
            allow_redirects=True,
        )

        data = self._verify_response(r)
        return data["guest_token"]

    def setup_session(self):
        session = requests.Session(
            # follow_redirects=True,
            proxies={"http://": self._reformatted_proxy} if self.proxy else None,
            timeout=30,
            verify=False,
        )

        generated_csrf_token = secrets.token_hex(16)
        guest_token = self.request_guest_token(session, generated_csrf_token)

        cookies = {"ct0": generated_csrf_token, "gt": guest_token}
        headers = {"x-guest-token": guest_token, "x-csrf-token": generated_csrf_token}

        self.session.headers.update(headers)
        self.session.cookies.update(cookies)
        csrf_token = self.request_ct0()

        self.session.headers["x-csrf-token"] = csrf_token
        self.session.cookies.delete("ct0")
        self.session.cookies.update({"ct0": csrf_token})
        self.session.headers = get_headers(self.session)

        self.verify_credentials()
        self.session.headers.update(
            {"x-csrf-token": self.session.cookies.get("ct0", domain=".twitter.com")}
        )

    def bind_account_v1(self, bind_params: BindAccountParamsV1) -> BindAccountDataV1:

        def get_oauth_token() -> str:
            _response = requests.get(str(bind_params.url), allow_redirects=True)
            raise_for_status(_response)

            token = re.search(
                r'<input id="oauth_token" name="oauth_token" type="hidden" value="([^"]+)"',
                _response.text,
            )
            if token:
                return token.group(1)

            token = _response.text.split("oauth_token=")
            if len(token) > 1:
                return token[1]

            raise TwitterError(
                {
                    "error_message": "Failed to get oauth token. "
                    "Make sure you are using correct cookies or url."
                }
            )

        def get_authenticity_token(_oauth_token: str) -> BindAccountDataV1 | str:
            params = {
                "oauth_token": _oauth_token,
            }
            _response = self.session.get(
                "https://api.twitter.com/oauth/authenticate", params=params
            )
            raise_for_status(_response)

            token = re.search(
                r'<input name="authenticity_token" type="hidden" value="([^"]+)"',
                _response.text,
            )
            if token:
                return token.group(1)

            bond_url = re.search(
                r'<a class="maintain-context" href="([^"]+)', _response.text
            )
            if bond_url:
                bond_url = bond_url.group(1).replace("&amp;", "&")
                _oauth_token, _oauth_verifier = bond_url.split("oauth_token=")[1].split(
                    "&oauth_verifier="
                )
                return BindAccountDataV1(
                    url=bond_url,
                    oauth_token=_oauth_token,
                    oauth_verifier=_oauth_verifier,
                )

            raise TwitterError(
                {
                    "error_message": "Failed to get authenticity token. "
                    "Make sure you are using correct cookies or url."
                }
            )

        def get_confirm_url(_oauth_token: str, _authenticity_token: str) -> str:
            data = {
                "authenticity_token": _authenticity_token,
                "redirect_after_login": f"https://api.twitter.com/oauth/authorize?oauth_token={_oauth_token}",
                "oauth_token": _oauth_token,
            }

            response = self.session.post(
                "https://api.twitter.com/oauth/authorize",
                data=data,
                allow_redirects=True,
            )
            raise_for_status(response)

            _confirm_url = re.search(
                r'<a class="maintain-context" href="([^"]+)', response.text
            )
            if _confirm_url:
                return _confirm_url.group(1).replace("&amp;", "&")

            raise TwitterError(
                {
                    "error_message": "Failed to get confirm url. "
                    "Make sure you are using correct cookies or url."
                }
            )

        def process_confirm_url(_url: str) -> BindAccountDataV1:
            response = self.session.get(_url, allow_redirects=True)
            raise_for_status(response)

            if "status=error" in response.url:
                raise TwitterError(
                    {
                        "error_message": "Failed to bind account. "
                        "Make sure you are using correct cookies or url."
                    }
                )

            _oauth_token, _oauth_verifier = response.url.split("oauth_token=")[1].split(
                "&oauth_verifier="
            )
            return BindAccountDataV1(
                url=response.url,
                oauth_token=_oauth_token,
                oauth_verifier=_oauth_verifier,
            )

        oauth_token = get_oauth_token()
        authenticity_token = get_authenticity_token(oauth_token)

        if isinstance(authenticity_token, BindAccountDataV1):
            return authenticity_token

        confirm_url = get_confirm_url(oauth_token, authenticity_token)
        return process_confirm_url(confirm_url)

    def bind_account_v2(self, bind_params: BindAccountParamsV2) -> BindAccountDataV2:

        def get_auth_code() -> str:
            response = self.session.get(
                "https://twitter.com/i/api/2/oauth2/authorize",
                params=bind_params.model_dump(),
            )
            raise_for_status(response)
            self.session.headers.update(
                {"x-csrf-token": self.session.cookies.get("ct0", domain=".twitter.com")}
            )
            return response.json()["auth_code"]

        def approve_auth_code(_auth_code: str) -> str:
            _params = {
                "approval": "true",
                "code": _auth_code,
            }

            response = self.session.post(
                "https://twitter.com/i/api/2/oauth2/authorize",
                params=_params,
                allow_redirects=True,
            )
            raise_for_status(response)

            code = response.json()["redirect_uri"].split("code=")[1]
            return code

        auth_code = get_auth_code()
        approved_code = approve_auth_code(auth_code)
        return BindAccountDataV2(code=approved_code)

    def create_poll(self, text: str, choices: list[str], poll_duration: int) -> dict:
        options = {
            "twitter:card": "poll4choice_text_only",
            "twitter:api:api:endpoint": "1",
            "twitter:long:duration_minutes": poll_duration,  # max: 10080
        }
        for i, c in enumerate(choices):
            options[f"twitter:string:choice{i + 1}_label"] = c

        headers = get_headers(self.session)
        headers["content-type"] = "application/x-www-form-urlencoded"
        url = "https://caps.twitter.com/v2/cards/create.json"

        r = self.session.post(
            url,
            headers=headers,
            params={"card_data": orjson.dumps(options).decode()},
            allow_redirects=True,
        )
        card_uri = (self._verify_response(r))["card_uri"]

        data = self.tweet(text, poll_params={"card_uri": card_uri})
        return data

    def verify_credentials(self) -> dict:
        r = self.session.get(
            f"{self.v1_api}/account/verify_credentials.json", allow_redirects=True
        )
        return self._verify_response(r)

    def email_phone_info(self) -> dict:
        r = self.session.get(
            f"{self.v1_api}/users/email_phone_info.json", allow_redirects=True
        )
        return self._verify_response(r)

    def settings_info(self) -> dict:
        r = self.session.get(
            f"{self.v1_api}/account/settings.json", allow_redirects=True
        )
        return self._verify_response(r)

    def screen_name(self) -> str:
        data = self.verify_credentials()
        return data["screen_name"]

    def user_id(self) -> int:
        data = self.verify_credentials()
        return data["id"]

    def name(self) -> str:
        data = self.verify_credentials()
        return data["name"]

    def location(self) -> str:
        data = self.verify_credentials()
        return data["location"]

    def description(self) -> str:
        data = self.verify_credentials()
        return data["description"]

    def followers_count(self) -> int:
        data = self.verify_credentials()
        return data["followers_count"]

    def friends_count(self) -> int:
        data = self.verify_credentials()
        return data["friends_count"]

    def registration_date(self) -> str:
        data = self.verify_credentials()
        return data["created_at"]

    def suspended(self) -> bool:
        data = self.verify_credentials()
        return data["suspended"]

    def dm(self, text: str, receivers: list[int], media: str = "") -> dict:
        variables = {
            "message": {},
            "requestId": str(uuid1(getnode())),
            "target": {"participant_ids": receivers},
        }
        if media:
            media_id = self.upload_media(media, is_dm=True)
            variables["message"]["media"] = {"id": media_id, "text": text}
        else:
            variables["message"]["text"] = {"text": text}

        res = self.gql("POST", Operation.useSendMessageMutation, variables)
        if find_key(res, "dm_validation_failure_type"):
            raise TwitterError(
                {
                    "error_message": "Failed to send message. Sender does not have privilege to dm receiver(s)",
                    "error_code": 349,
                }
            )
        return res

    def custom_dm(self, text: str, receiver: int) -> dict:
        json_data = {
            "event": {
                "type": "message_create",
                "message_create": {
                    "target": {"recipient_id": f"{receiver}"},
                    "message_data": {"text": f"{text}"},
                },
            }
        }

        r = self.session.post(
            f"{self.v1_api}/direct_messages/events/new.json",
            json=json_data,
        )
        return self._verify_response(r)

    def delete_tweet(self, tweet_id: int | str) -> dict:
        variables = {"tweet_id": tweet_id, "dark_request": False}
        return self.gql("POST", Operation.DeleteTweet, variables)

    def tweet(
        self, text: str, *, media: List[MediaEntity] = None, **kwargs
    ) -> dict | Coroutine[Any, Any, dict]:
        variables = {
            "tweet_text": text,
            "dark_request": False,
            "media": {
                "media_entities": [],
                "possibly_sensitive": False,
            },
            "semantic_annotation_ids": [],
        }

        if reply_params := kwargs.get("reply_params", {}):
            variables |= reply_params
        if quote_params := kwargs.get("quote_params", {}):
            variables |= quote_params
        if poll_params := kwargs.get("poll_params", {}):
            variables |= poll_params

        draft = kwargs.get("draft")
        schedule = kwargs.get("schedule")

        if draft or schedule:
            variables = {
                "post_tweet_request": {
                    "auto_populate_reply_metadata": False,
                    "status": text,
                    "exclude_reply_user_ids": [],
                    "media_ids": [],
                },
            }
            if media:
                for m in media:
                    media_id = self.upload_media(m["media"])
                    variables["post_tweet_request"]["media_ids"].append(media_id)
                    if alt := m.get("alt"):
                        self._add_alt_text(media_id, alt)

            if schedule:
                variables["execute_at"] = (
                    datetime.strptime(schedule, "%Y-%m-%d %H:%M").timestamp()
                    if isinstance(schedule, str)
                    else schedule
                )
                return self.gql("POST", Operation.CreateScheduledTweet, variables)

            return self.gql("POST", Operation.CreateDraftTweet, variables)

        # regular tweet
        if media:
            for m in media:

                tagged_users_id = []
                for tagged_user in m.tagged_users:
                    user_id = self.get_user_id(tagged_user)
                    tagged_users_id.append(user_id)

                variables["media"]["media_entities"].append(
                    {"media_id": m.media_id, "tagged_users": tagged_users_id}
                )

        return self.gql("POST", Operation.CreateTweet, variables)

    def schedule_tweet(
        self, text: str, date: int | str, *, media: List[MediaEntity] = None
    ) -> dict:
        variables = {
            "post_tweet_request": {
                "auto_populate_reply_metadata": False,
                "status": text,
                "exclude_reply_user_ids": [],
                "media_ids": [],
            },
            "execute_at": (
                datetime.strptime(date, "%Y-%m-%d %H:%M").timestamp()
                if isinstance(date, str)
                else date
            ),
        }
        if media:
            for m in media:

                tagged_users_id = []
                for tagged_user in m.tagged_users:
                    user_id = self.get_user_id(tagged_user)
                    tagged_users_id.append(user_id)

                variables["media"]["media_entities"].append(
                    {"media_id": m.media_id, "tagged_users": tagged_users_id}
                )

        return self.gql("POST", Operation.CreateScheduledTweet, variables)

    def schedule_reply(
        self, text: str, date: int | str, tweet_id: int, *, media: list = None
    ) -> dict:
        variables = {
            "post_tweet_request": {
                "auto_populate_reply_metadata": True,
                "in_reply_to_status_id": tweet_id,
                "status": text,
                "exclude_reply_user_ids": [],
                "media_ids": [],
            },
            "execute_at": (
                datetime.strptime(date, "%Y-%m-%d %H:%M").timestamp()
                if isinstance(date, str)
                else date
            ),
        }
        if media:
            for m in media:
                media_id = self.upload_media(m["media"])
                variables["post_tweet_request"]["media_ids"].append(media_id)
                if alt := m.get("alt"):
                    self._add_alt_text(media_id, alt)

        return self.gql("POST", Operation.CreateScheduledTweet, variables)

    def unschedule_tweet(self, tweet_id: int | str) -> dict:
        variables = {"scheduled_tweet_id": tweet_id}
        return self.gql("POST", Operation.DeleteScheduledTweet, variables)

    def untweet(self, tweet_id: int | str) -> dict:
        variables = {"tweet_id": tweet_id, "dark_request": False}
        return self.gql("POST", Operation.DeleteTweet, variables)

    def reply(
        self, text: str, tweet_id: int | str, media: List[MediaEntity] = None
    ) -> dict:
        variables = {
            "tweet_text": text,
            "reply": {
                "in_reply_to_tweet_id": tweet_id,
                "exclude_reply_user_ids": [],
            },
            "batch_compose": "BatchSubsequent",
            "dark_request": False,
            "media": {
                "media_entities": [],
                "possibly_sensitive": False,
            },
            "semantic_annotation_ids": [],
        }

        if media:
            for m in media:
                tagged_users_id = []

                for tagged_user in m.tagged_users:
                    user_id = self.get_user_id(tagged_user)
                    tagged_users_id.append(user_id)

                variables["media"]["media_entities"].append(
                    {"media_id": m.media_id, "tagged_users": tagged_users_id}
                )

        return self.gql("POST", Operation.CreateTweet, variables)

    def quote(self, text: str, tweet_id: int) -> dict:
        variables = {
            "tweet_text": text,
            # can use `i` as it resolves to screen_name
            "attachment_url": f"https://twitter.com/i/status/{tweet_id}",
            "dark_request": False,
            "media": {
                "media_entities": [],
                "possibly_sensitive": False,
            },
            "semantic_annotation_ids": [],
        }
        return self.gql("POST", Operation.CreateTweet, variables)

    def retweet(self, tweet_id: int) -> dict:
        variables = {"tweet_id": tweet_id, "dark_request": False}
        return self.gql("POST", Operation.CreateRetweet, variables)

    def unretweet(self, tweet_id: int) -> dict:
        variables = {"source_tweet_id": tweet_id, "dark_request": False}
        return self.gql("POST", Operation.DeleteRetweet, variables)

    @staticmethod
    def __get_cursor_value(data: dict, target_cursor_type: str, target_entry_type: str):
        if target_entry_type != "threaded_conversation_with_injections_v2":
            for instruction in (
                data.get("data", {})
                .get(target_entry_type, {})
                .get("timeline", {})
                .get("instructions", [])
            ):
                for entry in instruction.get("entries", []):
                    content = entry.get("content", {})
                    cursor_type = content.get("cursorType")
                    if (
                        content.get("entryType") == "TimelineTimelineCursor"
                        and cursor_type == target_cursor_type
                    ):
                        return content.get("value")

        else:
            for instruction in (
                data.get("data", {}).get(target_entry_type, {}).get("instructions", [])
            ):
                for entry in instruction.get("entries", []):
                    content = entry.get("content", {})
                    cursor_type = content.get("cursorType")
                    if (
                        content.get("entryType") == "TimelineTimelineCursor"
                        and cursor_type == target_cursor_type
                    ):
                        return content.get("value")

        return None

    def tweet_likes(
        self, celery_task, tweet_id: int, limit: int = 0
    ) -> dict[str, list[dict]]:
        variables = {"tweetId": tweet_id, "count": 100}
        users_data = []

        while True:
            data = self.gql("GET", Operation.Favoriters, variables)

            for instruction in (
                data.get("data", {})
                .get("favoriters_timeline", {})
                .get("timeline", {})
                .get("instructions", [])
            ):
                try:
                    for entry in instruction["entries"]:
                        try:
                            result = entry["content"]["itemContent"]["user_results"][
                                "result"
                            ]
                            screen_name = result["legacy"]["screen_name"]
                            if screen_name not in (
                                user["screen_name"] for user in users_data
                            ):
                                users_data.append(
                                    self.get_user_data_from_user_results(result)
                                )

                        except (KeyError, TypeError, IndexError):
                            continue

                except KeyError:
                    return {"users": users_data[:limit] if limit > 0 else users_data}

            cursor_value = self.__get_cursor_value(
                data, "Bottom", "favoriters_timeline"
            )
            if not cursor_value or (0 < limit <= len(users_data)):
                return {"users": users_data[:limit] if limit > 0 else users_data}

            variables["cursor"] = cursor_value

    def tweet_retweeters(
        self, celery_task, tweet_id: int, limit: int = 0
    ) -> dict[str, list[Any]]:
        variables = {"tweetId": tweet_id, "count": 100}
        tweets_data = []

        while True:
            data = self.gql("GET", Operation.Retweeters, variables)

            for instruction in data["data"]["retweeters_timeline"]["timeline"][
                "instructions"
            ]:
                try:
                    for entry in instruction["entries"]:
                        try:
                            result = entry["content"]["itemContent"]["user_results"][
                                "result"
                            ]
                            screen_name = result["legacy"]["screen_name"]
                            if screen_name not in (
                                user["screen_name"] for user in tweets_data
                            ):
                                tweets_data.append(
                                    self.get_user_data_from_user_results(result)
                                )
                        except (KeyError, TypeError, IndexError):
                            continue

                except KeyError:
                    return {"users": tweets_data[:limit] if limit > 0 else tweets_data}

            cursor_value = self.__get_cursor_value(
                data, "Bottom", "retweeters_timeline"
            )

            if not cursor_value or (0 < limit <= len(tweets_data)):
                return {"users": tweets_data[:limit] if limit > 0 else tweets_data}

            variables["cursor"] = cursor_value

    @staticmethod
    def get_user_data_from_user_results(data: dict) -> dict:
        legacy = data.get("legacy", {})

        return {
            "id": data.get("rest_id"),
            "name": legacy.get("name"),
            "screen_name": legacy.get("screen_name"),
            "profile_image_url": legacy.get("profile_image_url_https"),
            "favourites_count": legacy.get("favourites_count"),
            "followers_count": legacy.get("followers_count"),
            "friends_count": legacy.get("friends_count"),
            "location": legacy.get("location"),
            "description": legacy.get("description"),
            "created_at": legacy.get("created_at"),
        }

    def tweet_replies(
        self, celery_task, tweet_id: int, limit: int = 0
    ) -> dict[str, list[dict[str, dict | Any]]]:
        variables = {"focalTweetId": tweet_id}
        replies_data = []

        while True:
            data = self.gql("GET", Operation.TweetDetail, variables)

            for entry in data["data"]["threaded_conversation_with_injections_v2"][
                "instructions"
            ][0]["entries"]:
                try:
                    result = entry["content"]["items"][0]["item"]["itemContent"][
                        "tweet_results"
                    ]["result"]
                    reply_text = result["legacy"]["full_text"]
                    user_results = result["core"]["user_results"]["result"]

                    if reply_text not in (
                        reply["reply_text"] for reply in replies_data
                    ):
                        replies_data.append(
                            {
                                "reply_text": reply_text,
                                "user_data": self.get_user_data_from_user_results(
                                    user_results
                                ),
                            }
                        )
                except (KeyError, TypeError, IndexError):
                    continue

            entries = data["data"]["threaded_conversation_with_injections_v2"][
                "instructions"
            ][0]["entries"]
            if not entries[-1]["entryId"].startswith("cursor-bottom") or (
                0 < limit <= len(replies_data)
            ):
                return {"replies": replies_data[:limit] if limit > 0 else replies_data}

            for entry in entries:
                if entry["entryId"].startswith("cursor-bottom"):
                    cursor_value = entry["content"]["itemContent"]["value"]
                    variables["cursor"] = cursor_value
                    break

    def user_followers(self, celery_task, username: str, limit: int = 0) -> list[str]:
        variables = {"screen_name": username, "count": 200}
        users = []

        while True:
            r = self.session.get(f"{self.v1_api}/followers/list.json", params=variables)
            if r.status_code == 503:
                asyncio.sleep(3)
                continue

            else:
                data = self._verify_response(r)
                new_users = [user["screen_name"] for user in data["users"]]
                users.extend(new_users)

                next_cursor = int(data.get("next_cursor"))
                if next_cursor == 0 or (0 < limit <= len(users)):
                    return users[:limit] if limit > 0 else users

                variables["cursor"] = data["next_cursor_str"]

    def user_followings(self, username: str) -> list[str]:
        variables = {"screen_name": username, "count": 200}
        users = []

        while True:
            r = self.session.get(f"{self.v1_api}/friends/list.json", params=variables)
            if r.status_code == 503:
                asyncio.sleep(5)
                continue

            else:
                data = self._verify_response(r)
                new_users = [user["screen_name"] for user in data["users"]]
                users.extend(new_users)

                if int(data.get("next_cursor")) == 0:
                    return users

                variables["cursor"] = data["next_cursor_str"]

    def user_last_tweets(
        self, user_id: int, username: str
    ) -> list[dict[str, str, str | None, str | None, str | None]]:
        data = self.gql("GET", Operation.UserTweets, {"userId": user_id})

        try:
            tweets_data = []
            timeline = data["data"]["user"]["result"]["timeline_v2"]["timeline"]
            for tweet in timeline["instructions"]:
                entries = tweet.get("entries", [])
                for entry in entries:
                    if entry["entryId"].startswith("tweet"):
                        tweet_link = f"https://twitter.com/{username}/status/{entry['entryId'].split('-')[-1]}"
                    else:
                        continue

                    tweet_results = (
                        entry.get("content", {})
                        .get("itemContent", {})
                        .get("tweet_results", {})
                        .get("result", {})
                        .get("legacy")
                    )
                    if tweet_results and tweet_results.get("full_text"):
                        full_text = tweet_results["full_text"]
                        created_at = tweet_results.get("created_at", "")
                        is_quote_status = tweet_results.get("is_quote_status", "")
                        lang = tweet_results.get("lang", "")

                        tweets_data.append(
                            {
                                "tweet_link": tweet_link,
                                "full_text": full_text,
                                "created_at": created_at,
                                "is_quote_status": is_quote_status,
                                "lang": lang,
                            }
                        )

            return tweets_data

        except Exception as error:
            raise TwitterError({"error_message": f"Failed to get user tweets: {error}"})

    def like(self, tweet_id: int) -> dict:
        variables = {"tweet_id": tweet_id}
        return self.gql("POST", Operation.FavoriteTweet, variables)

    def unlike(self, tweet_id: int) -> dict:
        variables = {"tweet_id": tweet_id}
        return self.gql("POST", Operation.UnfavoriteTweet, variables)

    def bookmark(self, tweet_id: int) -> dict:
        variables = {"tweet_id": tweet_id}
        return self.gql("POST", Operation.CreateBookmark, variables)

    def unbookmark(self, tweet_id: int) -> dict:
        variables = {"tweet_id": tweet_id}
        return self.gql("POST", Operation.DeleteBookmark, variables)

    def create_list(self, name: str, description: str, private: bool) -> dict:
        variables = {
            "isPrivate": private,
            "name": name,
            "description": description,
        }
        return self.gql("POST", Operation.CreateList, variables)

    def update_list(
        self, list_id: int, name: str, description: str, private: bool
    ) -> dict:
        variables = {
            "listId": list_id,
            "isPrivate": private,
            "name": name,
            "description": description,
        }
        return self.gql("POST", Operation.UpdateList, variables)

    def update_pinned_lists(self, list_ids: list[int]) -> dict:
        """
        Update pinned lists.
        Reset all pinned lists and pin all specified lists in the order they are provided.

        @param list_ids: list of list ids to pin
        @return: response
        """
        return self.gql("POST", Operation.ListsPinMany, {"listIds": list_ids})

    def pin_list(self, list_id: int) -> dict:
        return self.gql("POST", Operation.ListPinOne, {"listId": list_id})

    def unpin_list(self, list_id: int) -> dict:
        return self.gql("POST", Operation.ListUnpinOne, {"listId": list_id})

    def add_list_member(self, list_id: int, user_id: int) -> dict:
        return self.gql(
            "POST", Operation.ListAddMember, {"listId": list_id, "userId": user_id}
        )

    def remove_list_member(self, list_id: int, user_id: int) -> dict:
        return self.gql(
            "POST", Operation.ListRemoveMember, {"listId": list_id, "userId": user_id}
        )

    def delete_list(self, list_id: int) -> dict:
        return self.gql("POST", Operation.DeleteList, {"listId": list_id})

    def update_list_banner(self, list_id: int, media: str) -> dict:
        media_id = self.upload_media(media)
        variables = {"listId": list_id, "mediaId": media_id}
        return self.gql("POST", Operation.EditListBanner, variables)

    def delete_list_banner(self, list_id: int) -> dict:
        return self.gql("POST", Operation.DeleteListBanner, {"listId": list_id})

    def follow_topic(self, topic_id: int) -> dict:
        return self.gql("POST", Operation.TopicFollow, {"topicId": str(topic_id)})

    def unfollow_topic(self, topic_id: int) -> dict:
        return self.gql("POST", Operation.TopicUnfollow, {"topicId": str(topic_id)})

    def pin(self, tweet_id: int) -> dict:
        return self.v1(
            "account/pin_tweet.json", {"tweet_mode": "extended", "id": tweet_id}
        )

    def unpin(self, tweet_id: int) -> dict:
        return self.v1(
            "account/unpin_tweet.json", {"tweet_mode": "extended", "id": tweet_id}
        )

    def get_user_id(self, username: str) -> int:
        headers = get_headers(self.session)
        headers["content-type"] = "application/x-www-form-urlencoded"
        r = self.session.get(
            f"{self.v1_api}/users/show.json",
            headers=headers,
            params={"screen_name": username},
        )
        data = self._verify_response(r)
        return data["id"]

    def get_user_info(self, username: str) -> dict:
        headers = get_headers(self.session)
        headers["content-type"] = "application/x-www-form-urlencoded"
        r = self.session.get(
            f"{self.v1_api}/users/show.json",
            headers=headers,
            params={"screen_name": username},
        )
        return self._verify_response(r)

    def follow(self, user_id: int | str) -> dict:
        settings = deepcopy(follow_settings)
        settings |= {"user_id": user_id}
        return self.v1("friendships/create.json", settings)

    def unfollow(self, user_id: int | str) -> dict:
        settings = deepcopy(follow_settings)
        settings |= {"user_id": user_id}
        return self.v1("friendships/destroy.json", settings)

    def mute(self, user_id: int) -> dict:
        return self.v1("mutes/users/create.json", {"user_id": user_id})

    def unmute(self, user_id: int) -> dict:
        return self.v1("mutes/users/destroy.json", {"user_id": user_id})

    def enable_follower_notifications(self, user_id: int) -> dict:
        settings = deepcopy(follower_notification_settings)
        settings |= {"id": user_id, "device": "true"}
        return self.v1("friendships/update.json", settings)

    def disable_follower_notifications(self, user_id: int) -> dict:
        settings = deepcopy(follower_notification_settings)
        settings |= {"id": user_id, "device": "false"}
        return self.v1("friendships/update.json", settings)

    def block(self, user_id: int) -> dict:
        return self.v1("blocks/create.json", {"user_id": user_id})

    def unblock(self, user_id: int) -> dict:
        return self.v1("blocks/destroy.json", {"user_id": user_id})

    def update_profile_image(self, media: str) -> dict:
        media_id = self.upload_media(media)
        params = {"media_id": media_id}

        r = self.session.post(
            f"{self.v1_api}/account/update_profile_image.json",
            headers=get_headers(self.session),
            params=params,
        )
        return self._verify_response(r)

    def update_profile_banner(self, media: str) -> dict:
        media_id = self.upload_media(media)
        params = {"media_id": media_id}

        r = self.session.post(
            f"{self.v1_api}/account/update_profile_banner.json",
            headers=get_headers(self.session),
            params=params,
        )
        return self._verify_response(r)

    def update_profile_info(self, params: dict) -> dict:
        headers = get_headers(self.session)
        r = self.session.post(
            f"{self.v1_api}/account/update_profile.json", headers=headers, params=params
        )

        return self._verify_response(r)

    def update_search_settings(self, settings: dict) -> dict:
        twid = int(self.session.cookies.get("twid").split("=")[-1].strip('"'))
        headers = get_headers(self.session)

        r = self.session.post(
            url=f"{self.v1_api}/strato/column/User/{twid}/search/searchSafety",
            headers=headers,
            json=settings,
        )
        return self._verify_response(r)

    def update_settings(self, settings: dict) -> dict:
        return self.v1("account/settings.json", settings)

    def update_username(self, username: str):
        return self.update_settings({"screen_name": username})

    def change_password(self, old: str, new: str) -> dict:
        params = {
            "current_password": old,
            "password": new,
            "password_confirmation": new,
        }
        headers = get_headers(self.session)
        headers["content-type"] = "application/x-www-form-urlencoded"

        r = self.session.post(
            f"{self.v1_api}/account/change_password.json",
            headers=headers,
            data=params,
            allow_redirects=True,
        )
        return self._verify_response(r)

    def remove_interests(self, *args) -> dict:
        """
        Pass 'all' to remove all interests
        """
        r = self.session.get(
            f"{self.v1_api}/account/personalization/twitter_interests.json",
            headers=get_headers(self.session),
        )
        current_interests = r.json()["interested_in"]
        if args == "all":
            disabled_interests = [x["id"] for x in current_interests]
        else:
            disabled_interests = [
                x["id"] for x in current_interests if x["display_name"] in args
            ]
        payload = {
            "preferences": {
                "interest_preferences": {
                    "disabled_interests": disabled_interests,
                    "disabled_partner_interests": [],
                }
            }
        }
        r = self.session.post(
            f"{self.v1_api}/account/personalization/p13n_preferences.json",
            headers=get_headers(self.session),
            json=payload,
        )
        return self._verify_response(r)

    def home_timeline(self, limit=math.inf) -> list[dict]:
        return self._paginate(
            "POST", Operation.HomeTimeline, Operation.default_variables, int(limit)
        )

    def home_latest_timeline(self, limit=math.inf) -> list[dict]:
        return self._paginate(
            "POST",
            Operation.HomeLatestTimeline,
            Operation.default_variables,
            int(limit),
        )

    def bookmarks(self, limit=math.inf) -> list[dict]:
        return self._paginate("GET", Operation.Bookmarks, {}, int(limit))

    def _paginate(
        self, method: str, operation: tuple, variables: dict, limit: int
    ) -> list[dict]:
        initial_data = self.gql(method, operation, variables)
        res = [initial_data]
        ids = set(find_key(initial_data, "rest_id"))
        dups = 0
        DUP_LIMIT = 3

        cursor = get_cursor(initial_data)
        while (dups < DUP_LIMIT) and cursor:
            prev_len = len(ids)
            if prev_len >= limit:
                return res

            variables["cursor"] = cursor
            data = self.gql(method, operation, variables)

            cursor = get_cursor(data)
            ids |= set(find_key(data, "rest_id"))

            if prev_len == len(ids):
                dups += 1

            res.append(data)
        return res

    def custom_upload_media(self, file: Path) -> int | None:
        url = "https://upload.twitter.com/1.1/media/upload.json"

        headers = get_headers(self.session)
        with httpx.Client(
            headers=headers, cookies=dict(self.session.cookies)
        ) as client:
            upload_type = "tweet"
            media_type = mimetypes.guess_type(file)[0]
            media_category = (
                f"{upload_type}_gif"
                if "gif" in media_type
                else f'{upload_type}_{media_type.split("/")[0]}'
            )

            files = {"media": file.read_bytes()}

            post_data = {}
            if media_category is not None:
                post_data["media_category"] = media_category

            r = client.post(url=url, json=params, params=post_data, files=files)

            data = self._verify_response(r)
            return data["media_id"]

    def upload_media(self, filename: str, is_dm: bool = False) -> int | None:
        """
        https://developer.twitter.com/en/docs/twitter-api/v1/media/upload-media/uploading-media/media-best-practices
        """

        def check_media(category: str, size: int) -> None:
            fmt = lambda x: f"{(x / 1e6):.2f} MB"
            msg = (
                lambda x: f"cannot upload {fmt(size)} {category}, max size is {fmt(x)}"
            )
            if category == "image" and size > MAX_IMAGE_SIZE:
                raise Exception(msg(MAX_IMAGE_SIZE))
            if category == "gif" and size > MAX_GIF_SIZE:
                raise Exception(msg(MAX_GIF_SIZE))
            if category == "video" and size > MAX_VIDEO_SIZE:
                raise Exception(msg(MAX_VIDEO_SIZE))

        # if is_profile:
        #     url = 'https://upload.twitter.com/i/media/upload.json'
        # else:
        #     url = 'https://upload.twitter.com/1.1/media/upload.json'

        url = "https://upload.twitter.com/i/media/upload.json"

        file = Path(filename)
        total_bytes = file.stat().st_size
        headers = get_headers(self.session)

        upload_type = "dm" if is_dm else "tweet"
        media_type = mimetypes.guess_type(file)[0]
        media_category = (
            f"{upload_type}_gif"
            if "gif" in media_type
            else f'{upload_type}_{media_type.split("/")[0]}'
        )

        check_media(media_category, total_bytes)

        params = {
            "command": "INIT",
            "media_type": media_type,
            "total_bytes": total_bytes,
            "media_category": media_category,
        }
        r = self.session.post(
            url=url, headers=headers, params=params, allow_redirects=True
        )

        data = self._verify_response(r)
        media_id = data["media_id"]

        desc = f"uploading: {file.name}"
        with tqdm(
            total=total_bytes, desc=desc, unit="B", unit_scale=True, unit_divisor=1024
        ) as pbar:
            with open(file, "rb") as fp:
                i = 0
                while chunk := fp.read(UPLOAD_CHUNK_SIZE):
                    params = {
                        "command": "APPEND",
                        "media_id": media_id,
                        "segment_index": i,
                    }
                    try:
                        pad = bytes(
                            "".join(random.choices(ascii_letters, k=16)),
                            encoding="utf-8",
                        )
                        data = b"".join(
                            [
                                b"------WebKitFormBoundary",
                                pad,
                                b'\r\nContent-Disposition: form-data; name="media"; filename="blob"',
                                b"\r\nContent-Type: application/octet-stream",
                                b"\r\n\r\n",
                                chunk,
                                b"\r\n------WebKitFormBoundary",
                                pad,
                                b"--\r\n",
                            ]
                        )
                        _headers = {
                            b"content-type": b"multipart/form-data; boundary=----WebKitFormBoundary"
                            + pad
                        }
                        self.session.post(
                            url=url,
                            headers=headers | _headers,
                            params=params,
                            content=data,
                            allow_redirects=True,
                        )
                    except Exception as error:
                        try:
                            files = {"media": chunk}
                            self.session.post(
                                url=url, headers=headers, params=params, files=files
                            )
                        except Exception as error:
                            return

                    i += 1
                    pbar.update(fp.tell() - pbar.n)

        params = {"command": "FINALIZE", "media_id": media_id, "allow_async": "true"}
        if is_dm:
            params |= {"original_md5": hashlib.md5(file.read_bytes()).hexdigest()}

        r = self.session.post(
            url=url, headers=headers, params=params, allow_redirects=True
        )
        data = self._verify_response(r)

        processing_info = data.get("processing_info")
        while processing_info:
            state = processing_info["state"]
            if error := processing_info.get("error"):
                return
            if state == MEDIA_UPLOAD_SUCCEED:
                break
            if state == MEDIA_UPLOAD_FAIL:
                return
            check_after_secs = processing_info.get(
                "check_after_secs", random.randint(1, 5)
            )

            time.sleep(check_after_secs)
            params = {"command": "STATUS", "media_id": media_id}

            r = self.session.get(
                url=url, headers=headers, params=params, allow_redirects=True
            )
            data = self._verify_response(r)
            processing_info = data.get("processing_info")

        return media_id

    def _add_alt_text(self, media_id: int, text: str) -> dict:
        params = {"media_id": media_id, "alt_text": {"text": text}}
        url = f"{self.v1_api}/media/metadata/create.json"
        r = self.session.post(url, headers=get_headers(self.session), json=params)
        return self._verify_response(r)

    def dm_inbox(self) -> dict:
        """
        Get DM inbox metadata.

        @return: inbox as dict
        """
        r = self.session.get(
            f"{self.v1_api}/dm/inbox_initial_state.json",
            headers=get_headers(self.session),
            params=dm_params,
        )
        return self._verify_response(r)

    # def dm_history(self, conversation_ids: list[str] = None) -> list[dict]:
    #     """
    #     Get DM history.
    #
    #     Call without arguments to get all DMS from all conversations.
    #
    #     @param conversation_ids: optional list of conversation ids
    #     @return: list of messages as dicts
    #     """
    #
    #     def get(session: AsyncClient, conversation_id: str):
    #         params = deepcopy(dm_params)
    #         r = session.get(
    #             f"{self.v1_api}/dm/conversation/{conversation_id}.json",
    #             params=params,
    #         )
    #         res = (self._verify_response(r)).get("conversation_timeline", {})
    #         data = [x.get("message") for x in res.get("entries", [])]
    #         entry_id = res.get("min_entry_id")
    #         while entry_id:
    #             params["max_id"] = entry_id
    #             r = session.get(
    #                 f"{self.v1_api}/dm/conversation/{conversation_id}.json",
    #                 params=params,
    #             )
    #             res = (self._verify_response(r)).get("conversation_timeline", {})
    #             data.extend(x["message"] for x in res.get("entries", []))
    #             entry_id = res.get("min_entry_id")
    #         return data
    #
    #     def process(ids):
    #         limits = Limits(max_connections=100)
    #         headers, cookies = get_headers(self.session), self.session.cookies
    #         async with AsyncClient(
    #                 limits=limits, headers=headers, cookies=cookies, timeout=20
    #         ) as c:
    #             return tqdm_asyncio.gather(
    #                 *(get(c, _id) for _id in ids), desc="Getting DMs"
    #             )
    #
    #     if conversation_ids:
    #         ids = conversation_ids
    #     else:
    #         # get all conversations
    #         inbox = self.dm_inbox()
    #         ids = list(inbox["inbox_initial_state"]["conversations"])
    #
    #     return asyncio.run(process(ids))

    def dm_delete(self, *, conversation_id: str = None, message_id: str = None) -> dict:
        """
        Delete operations

        - delete (hide) a single DM
        - delete an entire conversation

        @param conversation_id: the conversation id
        @param message_id: the message id
        @return: result metadata
        """
        self.session.headers.update(headers=get_headers(self.session))
        results = {"conversation": None, "message": None}
        if conversation_id:
            results["conversation"] = self.session.post(
                f"{self.v1_api}/dm/conversation/{conversation_id}/delete.json",
            )  # not json response
        if message_id:
            # delete single message
            _id, op = Operation.DMMessageDeleteMutation
            results["message"] = self.session.post(
                f"{self.gql_api}/{_id}/{op}",
                json={"queryId": _id, "variables": {"messageId": message_id}},
            )
        return results

    def dm_search(self, query: str) -> dict:
        """
        Search DMs by keyword

        @param query: search term
        @return: search results as dict
        """

        def get(cursor=None):
            if cursor:
                params["variables"]["cursor"] = cursor.pop()
            _id, op = Operation.DmAllSearchSlice
            r = self.session.get(
                f"{self.gql_api}/{_id}/{op}",
                params=build_params(params),
            )
            res = r.json()
            cursor = find_key(res, "next_cursor")
            return res, cursor

        self.session.headers.update(headers=get_headers(self.session))
        variables = deepcopy(Operation.default_variables)
        variables["count"] = 50  # strict limit, errors thrown if exceeded
        variables["query"] = query
        params = {"variables": variables, "features": Operation.default_features}
        res, cursor = get()
        data = [res]
        while cursor:
            res, cursor = get(cursor)
            data.append(res)
        return {"query": query, "data": data}

    def scheduled_tweets(self, ascending: bool = True) -> dict:
        variables = {"ascending": ascending}
        return self.gql("GET", Operation.FetchScheduledTweets, variables)

    def delete_scheduled_tweet(self, tweet_id: int) -> dict:
        """duplicate, same as `unschedule_tweet()`"""
        variables = {"scheduled_tweet_id": tweet_id}
        return self.gql("POST", Operation.DeleteScheduledTweet, variables)

    def clear_scheduled_tweets(self) -> None:
        user_id = int(re.findall('"u=(\d+)"', self.session.cookies.get("twid"))[0])
        drafts = self.gql("GET", Operation.FetchScheduledTweets, {"ascending": True})
        for _id in set(find_key(drafts, "rest_id")):
            if _id != user_id:
                self.gql(
                    "POST", Operation.DeleteScheduledTweet, {"scheduled_tweet_id": _id}
                )

    def draft_tweets(self, ascending: bool = True) -> dict:
        variables = {"ascending": ascending}
        return self.gql("GET", Operation.FetchDraftTweets, variables)

    def delete_draft_tweet(self, tweet_id: int) -> dict:
        variables = {"draft_tweet_id": tweet_id}
        return self.gql("POST", Operation.DeleteDraftTweet, variables)

    def clear_draft_tweets(self) -> None:
        user_id = int(re.findall('"u=(\d+)"', self.session.cookies.get("twid"))[0])
        drafts = self.gql("GET", Operation.FetchDraftTweets, {"ascending": True})
        for _id in set(find_key(drafts, "rest_id")):
            if _id != user_id:
                self.gql("POST", Operation.DeleteDraftTweet, {"draft_tweet_id": _id})

    def notifications(self, params: dict = None) -> dict:
        r = self.session.get(
            f"{self.v2_api}/notifications/all.json",
            headers=get_headers(self.session),
            params=params or live_notification_params,
        )
        return self._verify_response(r)

    def recommendations(self, params: dict = None) -> dict:
        r = self.session.get(
            f"{self.v1_api}/users/recommendations.json",
            headers=get_headers(self.session),
            params=params or recommendations_params,
        )
        return self._verify_response(r)

    def fleetline(self, params: dict = None) -> dict:
        r = self.session.get(
            "https://twitter.com/i/api/fleets/v1/fleetline",
            headers=get_headers(self.session),
            params=params or {},
        )
        return self._verify_response(r)

    @property
    def id(self) -> int:
        """Get User ID"""
        return int(re.findall('"u=(\d+)"', self.session.cookies.get("twid"))[0])

    def save_cookies(self, fname: str = None):
        """Save cookies to file"""
        cookies = self.session.cookies
        Path(f'{fname or cookies.get("username")}.cookies').write_bytes(
            orjson.dumps(dict(cookies))
        )
