from uk_election_ids.datapackage import ELECTION_TYPES


# These types exist in EE but don't have defined behaviour in the IdBuilder
ELECTION_TYPES["ref"] = {
    "name": "Referendum",
    "subtypes": [],
    "default_voting_system": "FPTP",
}


VOTING_SYSTEMS = [
    {
        "slug": "AMS",
        "name": "Additional Member System",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Additional_Member_System",
        "description": "In an election using the Additional Member System, each voter casts two votes: a vote for a candidate standing in their constituency (with or without an affiliated party), and a vote for a party list standing in a wider region made up of multiple constituencies.",
        "uses_party_lists": True,
    },
    {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "wikipedia_url": "https://en.m.wikipedia.org/wiki/First-past-the-post_voting",
        "description": "A first-past-the-post (abbreviated FPTP, 1stP, 1PTP or FPP) or winner-takes-all election is one that is won by the candidate receiving more votes than any others.",
        "uses_party_lists": False,
    },
    {
        "slug": "sv",
        "name": "Supplementary Vote",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Contingent_vote#Supplementary_vote",
        "description": "Under the supplementary vote (SV), voters express a first and second choice of candidate only, and, if no candidate receives an absolute majority of first-choice votes, all but the two leading candidates are eliminated and the votes of those eliminated redistributed according to their second-choice votes to determine the winner.",
        "uses_party_lists": False,
    },
    {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Single_transferable_vote",
        "description": "The single transferable vote (STV) is a voting system designed to achieve proportional representation through ranked voting in multi-seat organizations or constituencies (voting districts).",
        "uses_party_lists": False,
    },
    {
        "slug": "PR-CL",
        "name": "Closed List",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Closed_list",
        "description": "Closed list describes the variant of party-list proportional representation where voters can (effectively) only vote for political parties as a whole and thus have no influence on the party-supplied order in which party candidates are elected.",
        "uses_party_lists": True,
    },
]
