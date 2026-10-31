BASE_OPTIONS = {
    "weaponvo": [
        "pistol", "rifle", "assault", "burstrifle", "smg", "lmg", "mg",
        "shotgun", "sniper", "launcher", "grenade", "betty", "generic",
        "dual", "dualwield", "energy_pistol", "raygun", "wpck_ray", "ray3",
        "tesla", "thundergun", "monkey", "octobomb", "gersh_device",
        "wpck_bowie", "bowie", "spikes", "elemental_bow",
    ],
    "class": [
        "pistol", "rifle", "smg", "lmg", "shotgun",
        "sniper", "grenade", "special", "launcher", "ball",
    ],
    "price": [
        "250", "500", "750", "900", "1000", "1200", "1250", "1400", "1500",
        "1750", "2000", "2500", "3000", "4000", "5000", "10000",
    ],
}

EDITOR_LAYOUT = [
    ("weapon_name",       0, 0, 1, "entry"),
    ("upgrade_name",      0, 1, 1, "upgrade"),
    ("cost",              1, 0, 1, "price"),
    ("ammo_cost",         1, 1, 1, "price"),
    ("limit",             2, 0, 1, "count"),
    ("upgrade_limit",     2, 1, 1, "count"),
    ("weaponVO",          3, 0, 1, "weaponvo"),
    ("weaponVOresp",      3, 1, 1, "weaponvo"),
    ("create_vox",        4, 0, 1, "entry"),
    ("class",             4, 1, 1, "class"),
    ("hint",              5, 0, 2, "entry"),
    ("force_attachments", 6, 0, 2, "attachments"),
    ("in_box",            0, 0, 1, "bool"),
    ("upgrade_in_box",    1, 0, 1, "bool"),
    ("is_limited",        2, 0, 1, "bool"),
    ("is_wonder_weapon",  3, 0, 1, "bool"),
    ("is_aat_exempt",     4, 0, 1, "bool"),
    ("wallbuy_autospawn", 5, 0, 1, "bool"),
    ("obsolete_false",    6, 0, 1, "bool"),
    ("obsolete2_false",   7, 0, 1, "bool"),
]

FIELD_TIPS = {
    "weapon_name":
        "The weapon file this row sets up, e.g. pistol_standard.\n"
        "Must be in your zone file and unique in this list.",
    "upgrade_name":
        "What Pack-a-Punch turns it into, e.g. pistol_standard_upgraded.\n"
        "Leave blank and the weapon can't be upgraded.",
    "cost":
        "Wallbuy price in points.",
    "ammo_cost":
        "Price to buy ammo back from the wallbuy.",
    "in_box":
        "TRUE puts it in the Mystery Box.\n"
        "FALSE keeps it to wallbuys and scripts.",
    "upgrade_in_box":
        "TRUE is meant to let the box give out the upgraded version.",
    "is_limited":
        "TRUE turns on the limit and upgrade limit caps.",
    "limit":
        "With is limited TRUE, the box stops offering it once\n"
        "this many are held or out. Wallbuys ignore it.",
    "upgrade_limit":
        "Same box cap for the upgraded version.\n"
        "Needs is limited and an upgrade name.",
    "create_vox":
        "Meant to register an extra pickup voice line.",
    "weaponVO":
        "Voice type played on pickup, from a wallbuy or the box.\n"
        "Only heard if your map has player voices set up.",
    "weaponVOresp":
        "What a nearby player says back when\n"
        "someone picks this weapon up.",
    "hint":
        "Localized string for the wallbuy prompt text.",
    "class":
        "Weapon class, e.g. smg or sniper. Groups the weapon\n"
        "for wallbuy autofill spots that ask for a class.",
    "is_wonder_weapon":
        "TRUE: Secret Shopper won't sell its ammo and\n"
        "Disorderly Combat never hands it out.",
    "is_aat_exempt":
        "TRUE: Pack-a-Punch never adds an Alternate Ammo\n"
        "Type to it. Needs an upgrade name.",
    "wallbuy_autospawn":
        "TRUE lets wallbuy autofill spots\n"
        "(wallbuy_autofill structs) pick this weapon.",
    "obsolete_false":
        "unused, leave blank or false.",
    "obsolete2_false":
        "unused, leave blank or false.",
    "force_attachments":
        "Attachments it always spawns with, split by spaces,\n"
        "e.g. reflex extclip. Leave blank for none.",
}

FIELD_TYPES = {field: wtype
               for field, _row, _col, _span, wtype in EDITOR_LAYOUT}

COMBO_TYPES = set(BASE_OPTIONS) | {"upgrade"}

BOOL_FIELDS = {field for field, wtype in FIELD_TYPES.items() if wtype == "bool"}

EDITABLE_COMBOS = {"weaponvo", "class", "price", "upgrade"}
