import csv
from base64 import b64decode

import requests
from rapidfuzz import process


# (fuzzy-)match string local auth names to gov.uk register codes
class CodeMatcher:
    def __init__(self):
        councils = self.get_data()
        self.names = [c["la-name"] for c in councils]
        self.councils_lookup = {
            c["la-name"]: c["local-authority-code"] for c in councils
        }

    def get_data(self):
        resp = requests.get(
            "https://api.github.com/repos/mysociety/uk_local_authority_names_and_codes/contents/data/lookup_name_to_registry.csv"
        )
        resp.raise_for_status()
        body = resp.json()
        decoded = b64decode(body["content"]).decode("utf-8")

        csv_reader = csv.DictReader(decoded.splitlines())
        return list(csv_reader)

    def get_register_code(self, name):
        match, score, index = process.extractOne(name, self.names)
        code = self.councils_lookup[match]

        if score >= 95:
            # close enough
            return (code, match, score)

        return (None, match, score)
