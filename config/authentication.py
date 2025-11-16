from rest_framework import HTTP_HEADER_ENCODING
from rest_framework_simplejwt.authentication import JWTAuthentication, AUTH_HEADER_TYPES


class FlexibleJWTAuthentication(JWTAuthentication):
    """
    Allow JWT tokens to be sent without the ``Bearer`` prefix by adding it automatically.
    Retains the standard behaviour whenever the prefix is already present.
    """

    def get_raw_token(self, header: bytes):
        header = header.strip()

        if header and b" " not in header and AUTH_HEADER_TYPES:
            default_type = AUTH_HEADER_TYPES[0].encode(HTTP_HEADER_ENCODING)
            header = default_type + b" " + header

        return super().get_raw_token(header)
