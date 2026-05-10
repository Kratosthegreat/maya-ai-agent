import requests
import socket
import pytz

from datetime import datetime


class MayaTools:

    def __init__(self):

        self.cached_geo = None

    ####################################
    # NETWORK
    ####################################

    def get_public_ip(self):

        try:

            r = requests.get(
                "https://api.ipify.org",
                timeout=10
            )

            return r.text.strip()

        except Exception:

            return "unknown"

    ####################################
    # GEO
    ####################################

    def get_geo_data(self):

        try:

            if self.cached_geo:

                return self.cached_geo

            ip = self.get_public_ip()

            r = requests.get(

                f"https://ipapi.co/{ip}/json/",

                timeout=10

            )

            data = r.json()

            self.cached_geo = data

            return data

        except Exception:

            return {}

    ####################################
    # LOCATION
    ####################################

    def get_location(self):

        data = self.get_geo_data()

        city = data.get(
            "city",
            "unknown"
        )

        country = data.get(
            "country_name",
            "unknown"
        )

        return f"{city}, {country}"

    ####################################
    # TIMEZONE
    ####################################

    def get_timezone(self):

        data = self.get_geo_data()

        return data.get(
            "timezone",
            "UTC"
        )

    ####################################
    # TIME
    ####################################

    def get_time(self):

        try:

            timezone = self.get_timezone()

            tz = pytz.timezone(
                timezone
            )

            now = datetime.now(tz)

            return now.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        except Exception:

            return datetime.utcnow().strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )

    ####################################
    # WEATHER
    ####################################

    def get_weather(self):

        try:

            location = self.get_location()

            r = requests.get(

                f"https://wttr.in/{location}?format=3",

                timeout=10

            )

            return r.text

        except Exception:

            return "Weather unavailable"

    ####################################
    # HOST
    ####################################

    def get_hostname(self):

        return socket.gethostname()

    def get_local_ip(self):

        try:

            s = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM
            )

            s.connect(("8.8.8.8", 80))

            ip = s.getsockname()[0]

            s.close()

            return ip

        except Exception:

            return "unknown"

    ####################################
    # SEARCH
    ####################################

    def internet_search(

        self,

        query

    ):

        try:

            r = requests.get(

                "https://duckduckgo.com/html/",

                params={

                    "q": query

                },

                timeout=10

            )

            return r.text[:3000]

        except Exception as e:

            return str(e)
