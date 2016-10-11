ELECTION_TYPES = {
    'parl': {
        'name': "UK parliament",
        'subtypes': [],
    },
    'nia': {
        'name': "Northern Ireland assembly",
        'subtypes': [],
    },
    'naw': {
        'name': "Welsh assembly",
        'subtypes': [
            {'name': 'Constituencies', 'election_subtype': 'c'},
            {'name': 'Regions', 'election_subtype': 'r'},
        ],
    },
    'sp': {
        'name': "Scottish parliament",
        'subtypes': [
            {'name': 'Constituencies', 'election_subtype': 'c'},
            {'name': 'Regions', 'election_subtype': 'r'},
        ],
    },
    'gla': {
        'name': "Greater London assembly",
        'subtypes': [
            {'name': 'Constituencies', 'election_subtype': 'c'},
            {'name': 'Additional', 'election_subtype': 'a'},
        ],
    },
    'local': {
        'name': "Local elections",
        'subtypes': [],
    },
    'pcc': {
        'name': "Police and crime commissioner",
        'subtypes': [],
    },
    'mayor': {
        'name': "City mayor",
        'subtypes': [],
    },
    'eu': {
        'name': "European parliament (UK)",
        'subtypes': [],
    },
    'ref': {
        'name': "Referendum",
        'subtypes': [],
    },
}
