from collections import namedtuple


IdSpec = namedtuple('IdSpec', [
    'subtypes',
    'can_have_orgs',
    'can_have_divs'])


class DataPackageParser:

    """
    Parser which uses the data in datapackage.py to build
    a dict of IdSpec() objects which describe what sort of
    IDs we can and can't create for each election type.
    """

    def __init__(self, data):
        self.data = data

    def build_subtypes(self, record):
        if record['subtypes']:
            return tuple(subtype['election_subtype'] for subtype in record['subtypes'])
        return None

    def build_can_have_orgs(self, record):
        if 'can_have_orgs' in record:
            return record['can_have_orgs']
        else:
            return {
                subtype['election_subtype']: subtype['can_have_orgs']\
                for subtype in record['subtypes']
            }

    def build_can_have_divs(self, record):
        if 'can_have_divs' in record:
            return record['can_have_divs']
        else:
            return {
                subtype['election_subtype']: subtype['can_have_divs']\
                for subtype in record['subtypes']
            }

    def build_rules(self):
        rules = {}
        for key, record in self.data.items():
            subtypes = self.build_subtypes(record)
            can_have_orgs = self.build_can_have_orgs(record)
            can_have_divs = self.build_can_have_divs(record)
            rules[key] = IdSpec(subtypes, can_have_orgs, can_have_divs)
        return rules
