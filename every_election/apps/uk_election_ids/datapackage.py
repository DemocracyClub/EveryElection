ELECTION_TYPES = {
    'parl': {
        'name': "UK Parliament Elections",
        'subtypes': [],
        'default_voting_system': 'FPTP',
        'can_have_orgs': False,
        'can_have_divs': True,
    },
    'nia': {
        'name': "Northern Ireland Assembly Elections",
        'subtypes': [],
        'default_voting_system': 'STV',
        'can_have_orgs': False,
        'can_have_divs': True,
    },
    'naw': {
        'name': "Welsh Assembly Elections",
        'subtypes': [
            {'name': 'Constituencies', 'election_subtype': 'c'},
            {'name': 'Regions', 'election_subtype': 'r'},
        ],
        'default_voting_system': 'AMS',
        'can_have_orgs': False,
        'can_have_divs': True,
    },
    'sp': {
        'name': "Scottish Parliament Elections",
        'subtypes': [
            {'name': 'Constituencies', 'election_subtype': 'c'},
            {'name': 'Regions', 'election_subtype': 'r'},
        ],
        'default_voting_system': 'AMS',
        'can_have_orgs': False,
        'can_have_divs': True,
    },
    'gla': {
        'name': "Greater London Assembly Elections",
        'subtypes': [
            {
                'name': 'Constituencies',
                'election_subtype': 'c',
                'can_have_divs': True,
            },
            {
                'name': 'Additional',
                'election_subtype': 'a',
                'can_have_divs': False,
            },
        ],
        'can_have_orgs': False,
        'default_voting_system': 'AMS',
    },
    'local': {
        'name': "Local Elections",
        'subtypes': [],
        'default_voting_system': 'FPTP',
        'can_have_orgs': True,
        'can_have_divs': True,
    },
    'pcc': {
        'name': "Police and Crime Commissioner Elections",
        'subtypes': [],
        'default_voting_system': 'sv',
        'can_have_orgs': True,
        'can_have_divs': False,
    },
    'mayor': {
        'name': "Mayoral Elections",
        'subtypes': [],
        'default_voting_system': 'sv',
        'can_have_orgs': True,
        'can_have_divs': False,
    }
}
