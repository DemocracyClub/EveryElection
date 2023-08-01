from uk_election_ids.datapackage import ELECTION_TYPES

# These types exist in EE but don't have defined behaviour in the IdBuilder
ELECTION_TYPES["ref"] = {
    "name": "Referendum",
    "subtypes": [],
    "default_voting_system": "FPTP",
}
