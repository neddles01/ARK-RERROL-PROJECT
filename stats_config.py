"""
Configuração de stats para análise de itens no ARK.
"""

ITEM_TYPES = ["Sela (Saddle)", "Armadura (Armor)"]

SADDLE_STATS = {
    "Damage Taken Reduced By %": {"label": "Redução de Dano (%)", "priority": 1},
    "Melee Damage Increased By %": {"label": "Dano Melee (%)", "priority": 1},
    "Ability Damage Increase By %": {"label": "Dano de Ability (%)", "priority": 1},
    "Explosion Damage Taken Reduced By %": {"label": "Redução Dano Explosão (%)", "priority": 2},
    "Reactive Damage Taken Reduced By %": {"label": "Redução Dano Reativo (%)", "priority": 2},
    "Nature Damage Taken Reduced By %": {"label": "Redução Dano Natureza (%)", "priority": 2},
    "Armor Bonus When Equipped": {"label": "Bônus de Armadura", "priority": 3},
    "Swim Speed Increased By %": {"label": "Velocidade de Nado (%)", "priority": 3},
    "Chance To Dodge %": {"label": "Chance de Esquiva (%)", "priority": 3}
}

ARMOR_STATS = {
    "Magic Find Increased By %": {"label": "Magic Find (%)", "priority": 1},
    "Damage Taken Reduced By %": {"label": "Redução de Dano (%)", "priority": 2},
    "Elemental Damage Taken Reduced By %": {"label": "Redução Dano Elemental (%)", "priority": 2},
    "Nature Damage Taken Reduced By %": {"label": "Redução Dano Natureza (%)", "priority": 3},
    "Stamina Increased By": {"label": "Stamina", "priority": 3},
    "Weight Increased By": {"label": "Peso Bônus", "priority": 3},
    "Food Increased By": {"label": "Comida Bônus", "priority": 3},
    "Maximum Durability Increased By": {"label": "Durabilidade Máxima", "priority": 3},
    "Swim Speed Increased By %": {"label": "Velocidade de Nado (%)", "priority": 3}
}
