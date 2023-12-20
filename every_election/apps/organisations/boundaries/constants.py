from itertools import groupby

AREA_TYPE_TO_FILE = [
    ("CED", "county_electoral_division_region.shp"),
    ("UTE", "unitary_electoral_division_region.shp"),
    ("DIW", "district_borough_unitary_ward_region.shp"),
    ("LBW", "district_borough_unitary_ward_region.shp"),
    ("MTW", "district_borough_unitary_ward_region.shp"),
    ("UTW", "district_borough_unitary_ward_region.shp"),
    ("CTY", "county_region.shp"),
    ("GLA", "county_region.shp"),
    ("UTA", "district_borough_unitary_region.shp"),
    ("MTD", "district_borough_unitary_region.shp"),
    ("LBO", "district_borough_unitary_region.shp"),
    ("DIS", "district_borough_unitary_region.shp"),
    ("LAC", "greater_london_const_region.shp"),
    ("SPC", "scotland_and_wales_const_region.shp"),
    ("WAC", "scotland_and_wales_const_region.shp"),
    ("SPE", "scotland_and_wales_region.shp"),
    ("WAE", "scotland_and_wales_region.shp"),
    ("WMC", "westminster_const_region.shp"),
    ("EUR", "european_region_region.shp"),
]


def get_area_type_lookup(filter=lambda x: True, group=False):
    filtered = [a for a in AREA_TYPE_TO_FILE if filter(a[0])]

    if group is True:
        lookup = {}
        for filename, types in groupby(filtered, lambda x: x[1]):
            lookup[tuple((rec[0] for rec in types))] = filename
        return lookup

    return {a[0]: a[1] for a in filtered}


"""
There are some organisations
(e.g: GLA, Scottish Parliament, Welsh Assembly)
which we want to assign a boundary to
but which don't appear directly in BoundaryLine.

For convenience we'll just map them to a
European Region (E15) as a proxy.
"""
SPECIAL_CASES = {
    # London
    "E12000007": {"file": "european_region_region.shp", "code": "E15000007"},
    # Scotland
    "S92000003": {"file": "european_region_region.shp", "code": "S15000001"},
    # Wales
    "W92000004": {"file": "european_region_region.shp", "code": "W08000001"},
}


LGBCE_SLUG_TO_ORG_SLUG = {
    "adur": "adur",
    "allerdale": "allerdale",
    "alnwick": "alnwick",
    "amber-valley": "amber-valley",
    "arun": "arun",
    "ashfield": "ashfield",
    "ashford": "ashford",
    "aylesbury-vale": "aylesbury-vale",
    "babergh": "babergh",
    "barnsley": "barnsley",
    "barrow-furness": "barrow-in-furness",
    "basildon": "basildon",
    "basingstoke-and-deane": "basingstoke-and-deane",
    "bassetlaw": "bassetlaw",
    "bath-and-north-east-somerset": "bath-and-north-east-somerset",
    "bedford": "bedford",
    "birmingham": "birmingham",
    "blaby": "blaby",
    "blackburn-darwen": "blackburn-with-darwen",
    "blackpool": "blackpool",
    "bolsover": "bolsover",
    "bolton": "bolton",
    "kings-lynn-and-west-norfolk": "kings-lynn-and-west-norfolk",
    "poole": "poole",
    "boston": "boston",
    "bournemouth": "bournemouth",
    "bournemouth-christchurch-and-poole": "bournemouth-christchurch-and-poole",
    "bracknell-forest": "bracknell-forest",
    "braintree": "braintree",
    "breckland": "breckland",
    "brentwood": "brentwood",
    "brighton-and-hove": "brighton-and-hove",
    "bristol": "bristol",
    "broadland": "broadland",
    "bromsgrove": "bromsgrove",
    "broxbourne": "broxbourne",
    "broxtowe": "broxtowe",
    "buckinghamshire": "buckinghamshire",
    "burnley": "burnley",
    "bury": "bury",
    "calderdale": "calderdale",
    "cambridge": "cambridge",
    "cambridgeshire-and-peterborough": "cambridgeshire-and-peterborough",
    "cambridgeshire": "cambridgeshire",
    "cannock-chase": "cannock-chase",
    "canterbury": "canterbury",
    "carlisle": "carlisle",
    "castle-point": "castle-point",
    "central-bedfordshire": "central-bedfordshire",
    "charnwood": "charnwood",
    "chelmsford": "chelmsford",
    "cheltenham": "cheltenham",
    "cherwell": "cherwell",
    "cheshire-east": "cheshire-east",
    "cheshire-west-and-chester": "cheshire-west-and-chester",
    "chesterfield": "chesterfield",
    "chichester": "chichester",
    "chiltern": "chiltern",
    "chorley": "chorley",
    "christchurch": "christchurch",
    "bradford": "bradford",
    "lincoln": "city-of-lincoln",
    "city-of-london-alder": "city-of-london-alder",
    "city-of-london": "city-of-london",
    "westminster": "westminster",
    "wolverhampton": "wolverhampton",
    "york": "york",
    "colchester": "colchester",
    "copeland": "copeland",
    "corby": "corby",
    "cornwall": "cornwall",
    "cotswold": "cotswold",
    "isles-scilly": "isles-of-scilly",
    "coventry": "coventry",
    "craven": "craven",
    "crawley": "crawley",
    "cumberland": "cumberland",
    "cumbria": "cumbria",
    "dacorum": "dacorum",
    "darlington": "darlington",
    "dartford": "dartford",
    "daventry": "daventry",
    "derby": "derby",
    "derbyshire": "derbyshire",
    "derbyshire-dales": "derbyshire-dales",
    "devon": "devon",
    "doncaster": "doncaster",
    "dorset": "dorset",
    "dover": "dover",
    "dudley": "dudley",
    "county-durham": "county-durham",
    "eastbourne": "eastbourne",
    "east-cambridgeshire": "east-cambridgeshire",
    "east-devon": "east-devon",
    "east-dorset": "east-dorset",
    "east-hampshire": "east-hampshire",
    "east-hertfordshire": "east-hertfordshire",
    "eastleigh": "eastleigh",
    "east-lindsey": "east-lindsey",
    "east-northamptonshire": "east-northamptonshire",
    "east-riding-yorkshire": "east-riding-of-yorkshire",
    "east-staffordshire": "east-staffordshire",
    "east-suffolk": "east-suffolk",
    "east-sussex": "east-sussex",
    "eden": "eden",
    "elmbridge": "elmbridge",
    "epping-forest": "epping-forest",
    "epsom-and-ewell": "epsom-and-ewell",
    "erewash": "erewash",
    "essex": "essex",
    "exeter": "exeter",
    "fareham": "fareham",
    "fenland": "fenland",
    "folkestone-and-hythe": "folkestone-hythe",
    "forest-heath": "forest-heath",
    "forest-dean": "forest-of-dean",
    "fylde": "fylde",
    "gateshead": "gateshead",
    "gedling": "gedling",
    "gloucester": "gloucester",
    "gloucestershire": "gloucestershire",
    "gosport": "gosport",
    "gravesham": "gravesham",
    "london": "london",
    "greater-london-authority": "greater-london",
    "greater-manchester-ca": "greater-manchester-ca",
    "great-yarmouth": "great-yarmouth",
    "guildford": "guildford",
    "halton": "halton",
    "hambleton": "hambleton",
    "hampshire": "hampshire",
    "harborough": "harborough",
    "harlow": "harlow",
    "harrogate": "harrogate",
    "hart": "hart",
    "hartlepool": "hartlepool",
    "hastings": "hastings",
    "havant": "havant",
    "herefordshire": "herefordshire",
    "hertfordshire": "hertfordshire",
    "hertsmere": "hertsmere",
    "high-peak": "high-peak",
    "hinckley-and-bosworth": "hinckley-and-bosworth",
    "horsham": "horsham",
    "kingston-upon-hull": "kingston-upon-hull",
    "huntingdonshire": "huntingdonshire",
    "hyndburn": "hyndburn",
    "ipswich": "ipswich",
    "isle-wight": "isle-of-wight",
    "kent": "kent",
    "kettering": "kettering",
    "kirklees": "kirklees",
    "knowsley": "knowsley",
    "lancashire": "lancashire",
    "lancaster": "lancaster",
    "leeds": "leeds",
    "leicester": "leicester",
    "leicestershire": "leicestershire",
    "lewes": "lewes",
    "lichfield": "lichfield",
    "lincolnshire": "lincolnshire",
    "liverpool": "liverpool",
    "liverpool-city-ca": "liverpool-city-ca",
    "barking-and-dagenham": "barking-and-dagenham",
    "barnet": "barnet",
    "bexley": "bexley",
    "brent": "brent",
    "bromley": "bromley",
    "camden": "camden",
    "croydon": "croydon",
    "ealing": "ealing",
    "enfield": "enfield",
    "hackney": "hackney",
    "hammersmith-and-fulham": "hammersmith-and-fulham",
    "haringey": "haringey",
    "harrow": "harrow",
    "havering": "havering",
    "hillingdon": "hillingdon",
    "hounslow": "hounslow",
    "islington": "islington",
    "lambeth": "lambeth",
    "lewisham": "lewisham",
    "merton": "merton",
    "newham": "newham",
    "redbridge": "redbridge",
    "richmond-upon-thames": "richmond-upon-thames",
    "southwark": "southwark",
    "sutton": "sutton",
    "tower-hamlets": "tower-hamlets",
    "waltham-forest": "waltham-forest",
    "wandsworth": "wandsworth",
    "luton": "luton",
    "maidstone": "maidstone",
    "maldon": "maldon",
    "malvern-hills": "malvern-hills",
    "manchester": "manchester",
    "mansfield": "mansfield",
    "medway": "medway",
    "melton": "melton",
    "mendip": "mendip",
    "mid-devon": "mid-devon",
    "middlesbrough": "middlesbrough",
    "mid-suffolk": "mid-suffolk",
    "mid-sussex": "mid-sussex",
    "milton-keynes": "milton-keynes",
    "mole-valley": "mole-valley",
    "newark-and-sherwood": "newark-and-sherwood",
    "newcastle-upon-tyne": "newcastle-upon-tyne",
    "newcastle-under-lyme": "newcastle-under-lyme",
    "new-forest": "new-forest",
    "norfolk": "norfolk",
    "northampton": "northampton",
    "northamptonshire": "northamptonshire",
    "north-devon": "north-devon",
    "north-dorset": "north-dorset",
    "north-east-derbyshire": "north-east-derbyshire",
    "north-east-lincolnshire": "north-east-lincolnshire",
    "north-hertfordshire": "north-hertfordshire",
    "north-kesteven": "north-kesteven",
    "north-lincolnshire": "north-lincolnshire",
    "north-norfolk": "north-norfolk",
    "north-northamptonshire": "north-northamptonshire",
    "north-of-tyne": "north-of-tyne",
    "north-somerset": "north-somerset",
    "north-tyneside": "north-tyneside",
    "northumberland": "northumberland",
    "north-warwickshire": "north-warwickshire",
    "north-west-leicestershire": "north-west-leicestershire",
    "north-yorkshire": "north-yorkshire",
    "norwich": "norwich",
    "nottingham": "nottingham",
    "nottinghamshire": "nottinghamshire",
    "nuneaton-and-bedworth": "nuneaton-and-bedworth",
    "oadby-and-wigston": "oadby-and-wigston",
    "oldham": "oldham",
    "oxford": "oxford",
    "oxfordshire": "oxfordshire",
    "pendle": "pendle",
    "peterborough": "peterborough",
    "plymouth": "plymouth",
    "portsmouth": "portsmouth",
    "preston": "preston",
    "purbeck": "purbeck",
    "reading": "reading",
    "redcar-and-cleveland": "redcar-and-cleveland",
    "redditch": "redditch",
    "reigate-and-banstead": "reigate-and-banstead",
    "ribble-valley": "ribble-valley",
    "richmondshire": "richmondshire",
    "rochdale": "rochdale",
    "rochford": "rochford",
    "rossendale": "rossendale",
    "rother": "rother",
    "rotherham": "rotherham",
    "greenwich": "greenwich",
    "kensington-and-chelsea": "kensington-and-chelsea",
    "kingston-upon-thames": "kingston-upon-thames",
    "windsor-and-maidenhead": "windsor-and-maidenhead",
    "rugby": "rugby",
    "runnymede": "runnymede",
    "rushcliffe": "rushcliffe",
    "rushmoor": "rushmoor",
    "rutland": "rutland",
    "ryedale": "ryedale",
    "salford": "salford",
    "sandwell": "sandwell",
    "scarborough": "scarborough",
    "sedgemoor": "sedgemoor",
    "sefton": "sefton",
    "selby": "selby",
    "sevenoaks": "sevenoaks",
    "sheffield": "sheffield",
    "shepway": "shepway",
    "shropshire": "shropshire",
    "slough": "slough",
    "solihull": "solihull",
    "somerset": "somerset",
    "somerset-west-and-taunton": "somerset-west-and-taunton",
    "southampton": "southampton",
    "south-bucks": "south-bucks",
    "south-cambridgeshire": "south-cambridgeshire",
    "south-derbyshire": "south-derbyshire",
    "southend-sea": "southend-on-sea",
    "south-gloucestershire": "south-gloucestershire",
    "south-hams": "south-hams",
    "south-holland": "south-holland",
    "south-kesteven": "south-kesteven",
    "south-lakeland": "south-lakeland",
    "south-norfolk": "south-norfolk",
    "south-northamptonshire": "south-northamptonshire",
    "south-oxfordshire": "south-oxfordshire",
    "south-ribble": "south-ribble",
    "south-somerset": "south-somerset",
    "south-staffordshire": "south-staffordshire",
    "south-tyneside": "south-tyneside",
    "sheffield-city-ca": "sheffield-city-ca",
    "spelthorne": "spelthorne",
    "stafford": "stafford",
    "staffordshire": "staffordshire",
    "staffordshire-moorlands": "staffordshire-moorlands",
    "st-albans": "st-albans",
    "st-edmundsbury": "st-edmundsbury",
    "stevenage": "stevenage",
    "st-helens": "st-helens",
    "stockport": "stockport",
    "stockton-tees": "stockton-on-tees",
    "stoke-trent": "stoke-on-trent",
    "stratford-avon": "stratford-on-avon",
    "stroud": "stroud",
    "suffolk-coastal": "suffolk-coastal",
    "suffolk": "suffolk",
    "sunderland": "sunderland",
    "surrey": "surrey",
    "surrey-heath": "surrey-heath",
    "swale": "swale",
    "swindon": "swindon",
    "tameside": "tameside",
    "tamworth": "tamworth",
    "tandridge": "tandridge",
    "taunton-deane": "taunton-deane",
    "tees-valley": "tees-valley",
    "teignbridge": "teignbridge",
    "telford-and-wrekin": "telford-and-wrekin",
    "tendring": "tendring",
    "test-valley": "test-valley",
    "tewkesbury": "tewkesbury",
    "thanet": "thanet",
    "three-rivers": "three-rivers",
    "thurrock": "thurrock",
    "tonbridge-and-malling": "tonbridge-and-malling",
    "torbay": "torbay",
    "torridge": "torridge",
    "trafford": "trafford",
    "tunbridge-wells": "tunbridge-wells",
    "uttlesford": "uttlesford",
    "vale-white-horse": "vale-of-white-horse",
    "wakefield": "wakefield",
    "walsall": "walsall",
    "warrington": "warrington",
    "warwick": "warwick",
    "warwickshire": "warwickshire",
    "watford": "watford",
    "waveney": "waveney",
    "waverley": "waverley",
    "wealden": "wealden",
    "wellingborough": "wellingborough",
    "welwyn-hatfield": "welwyn-hatfield",
    "west-berkshire": "west-berkshire",
    "west-devon": "west-devon",
    "west-dorset": "west-dorset",
    "west-lancashire": "west-lancashire",
    "west-lindsey": "west-lindsey",
    "west-midlands": "west-midlands",
    "westmorland-and-furness": "westmorland-and-furness",
    "west-northamptonshire": "west-northamptonshire",
    "west-of-england": "west-of-england",
    "west-oxfordshire": "west-oxfordshire",
    "west-somerset": "west-somerset",
    "west-suffolk": "west-suffolk",
    "west-sussex": "west-sussex",
    "west-yorkshire": "west-yorkshire",
    "weymouth-and-portland": "weymouth-and-portland",
    "wigan": "wigan",
    "wiltshire": "wiltshire",
    "winchester": "winchester",
    "wirral": "wirral",
    "woking": "woking",
    "wokingham": "wokingham",
    "worcester": "worcester",
    "worcestershire": "worcestershire",
    "worthing": "worthing",
    "wychavon": "wychavon",
    "wycombe": "wycombe",
    "wyre": "wyre",
    "wyre-forest": "wyre-forest",
    # Extras
    "bedfordshire": "bedfordshire",
    "berkshire": "berkshire",
    "berwick-upon-tweed": "berwick-upon-tweed",
    "blyth-valley": "blyth-valley",
    "bridgnorth": "bridgnorth",
    "caradon": "caradon",
    "carrick": "carrick",
    "castle-morpeth": "castle-morpeth",
    "chester": "chester",
    "chester-le-street": "chester-le-street",
    "congleton": "congleton",
    "easington": "easington",
    "east-lindsay": "east-lindsay",
    "macclesfield": "macclesfield",
    "mid-bedfordshire": "mid-bedfordshire",
    "pabr-barnsley-and-sheffield": "pabr-barnsley-and-sheffield",
    "pabr-east-hertfordshire-and-stevenage": "pabr-east-hertfordshire-and-stevenage",
    "pabr-northumberland-and-gateshead": "pabr-northumberland-and-gateshead",
    "south-buckinghamshire": "south-buckinghamshire",
    "teesdale": "teesdale",
    "wrekin": "wrekin",
    "wansbeck": "wansbeck",
}
