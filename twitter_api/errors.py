class TwitterError(Exception):
    """Base class for Twitter errors"""

    def __init__(self, error_dict: dict):
        self.error_dict = error_dict

    @property
    def error_message(self) -> str:
        if self.error_code == 32:
            return "Failed to authenticate account. Check your credentials."

        elif self.error_code == 36:
            return "You cannot use your own user ID to report spam call"

        elif self.error_code == 38:
            return "The request is missing the <named> parameter (such as media, text, etc.) in the request."

        elif self.error_code == 50:
            return "User not found."

        elif self.error_code == 89:
            return "The access token used in the request is incorrect or has expired."

        elif self.error_code == 92:
            return "SSL is required. Only TLS v1.2 connections are allowed in the API. Update the request to a secure connection."

        elif self.error_code == 139:
            return "You have already favorited this tweet. (Duplicate)"

        elif self.error_code == 160:
            return "You've already requested to follow the user. (Duplicate)"

        elif self.error_code == 186:
            return "Tweet needs to be a bit shorter. The text is too long."

        elif self.error_code == 187:
            return "Text of your tweet is identical to another tweet. Change your text. (Duplicate)"

        elif self.error_code == 205:
            return "The account limit for reporting spam has been reached. Try again later."

        elif self.error_code == 214:
            return "Account is not set up to have open Direct Messages when trying to set up a welcome message."

        elif self.error_code == 220:
            return "The authentication token in use is restricted and cannot access the requested resource."

        elif self.error_code == 323:
            return "Only one animated GIF may be attached to a single Post."

        elif self.error_code == 325:
            return "The media ID attached to the Post was not found."

        elif self.error_code == 327:
            return "You cannot repost the same Post more than once."

        elif self.error_code == 349:
            return "You does not have privileges to Direct Message the recipient."

        return self.error_dict.get("error_message")

    @property
    def error_code(self) -> int:
        return self.error_dict.get("error_code")


class TwitterAccountSuspended(Exception):
    """Raised when account is suspended"""

    pass


class CaptchaError(Exception):
    """Raised when captcha solving failed"""

    pass


class RateLimitError(Exception):
    """Raised when rate limit exceeded"""

    pass


class IncorrectData(Exception):
    """Raised when validation error"""

    pass
