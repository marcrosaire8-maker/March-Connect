"""Données de référence pour les secteurs (classification des offres)."""

SECTEUR_SEED_DATA: list[dict[str, list[str] | str]] = [
    {
        "nom": "BTP/Travaux publics",
        "mots_cles": [
            "construction",
            "travaux",
            "bâtiment",
            "route",
            "génie civil",
            "infrastructure",
            "réhabilitation",
        ],
    },
    {
        "nom": "Informatique/Télécoms",
        "mots_cles": [
            "informatique",
            "logiciel",
            "réseau",
            "télécom",
            "système d'information",
            "numérique",
            "serveur",
        ],
    },
    {
        "nom": "Santé",
        "mots_cles": [
            "santé",
            "médical",
            "hôpital",
            "pharmacie",
            "équipement médical",
            "laboratoire",
        ],
    },
    {
        "nom": "Eau/Assainissement",
        "mots_cles": [
            "eau",
            "assainissement",
            "adduction",
            "forage",
            "station d'épuration",
            "hydraulique",
        ],
    },
    {
        "nom": "Énergie",
        "mots_cles": [
            "énergie",
            "électricité",
            "solaire",
            "gaz",
            "électrification",
            "réseau électrique",
        ],
    },
    {
        "nom": "Transport",
        "mots_cles": [
            "transport",
            "véhicule",
            "logistique",
            "mobilité",
            "ferroviaire",
            "aérien",
        ],
    },
    {
        "nom": "Agriculture",
        "mots_cles": [
            "agriculture",
            "élevage",
            "pêche",
            "semence",
            "irrigation",
            "agroalimentaire",
        ],
    },
    {
        "nom": "Études/Conseil",
        "mots_cles": [
            "étude",
            "conseil",
            "audit",
            "assistance technique",
            "faisabilité",
            "consultant",
        ],
    },
    {
        "nom": "Fournitures/Équipements",
        "mots_cles": [
            "fourniture",
            "équipement",
            "mobilier",
            "matériel",
            "achat",
            "approvisionnement",
        ],
    },
]
