import pytest
from analyzer import analyze_text

def test_armor_mode_approved():
    text = "Some random text\nHealth Increased By 150.5%\nDurability: 50"
    res = analyze_text(text, "Armor", "Health Increased By %", 150.0)
    assert res["stat_found"] is True
    assert res["value_found"] == 150.5
    assert res["approved"] is True
    assert res["found_line"] == "Health Increased By 150.5%"

def test_percentage_requirement():
    # Target stat requires percentage, but OCR doesn't have it (e.g. flat value)
    text = "Melee Damage: 150\nHealth: 100"
    res = analyze_text(text, "Armor", "Melee Damage Increased By %", 100.0)
    assert res["stat_found"] is False # Should be false because percentage was required but not found

    # Now it has percentage
    text_pct = "Melee Damage: 150%"
    res_pct = analyze_text(text_pct, "Armor", "Melee Damage Increased By %", 100.0)
    assert res_pct["stat_found"] is True

def test_saddle_unique_anchor_found_approved():
    text = "Saddle Name\nArmor: 50\nRandom Stat Bonuses\nHealth Increased By 120%\nMelee Damage: 300"
    res = analyze_text(text, "Saddle unique", "Health Increased By %", 100.0)
    assert res["stat_found"] is True
    assert res["value_found"] == 120.0
    assert res["approved"] is True

def test_saddle_unique_anchor_found_but_in_wrong_section():
    text = "Saddle Name\nHealth Increased By 150%\nRandom Stat Bonuses\nMelee Damage: 300"
    res = analyze_text(text, "Saddle unique", "Health Increased By %", 100.0)
    assert res["stat_found"] is False
    assert res["approved"] is False

def test_saddle_unique_anchor_not_found():
    text = "Saddle Name\nHealth Increased By 150%\nMelee Damage: 300"
    res = analyze_text(text, "Saddle unique", "Health Increased By %", 100.0)
    assert res["stat_found"] is False
    assert res["approved"] is False
    assert res["reason"] == "âncora não encontrada"

def test_saddle_comum_mode():
    text = "Saddle Name\nArmor: 50\nMelee Damage: 300\nMovement Speed Increased By 20%"
    res = analyze_text(text, "Saddle comum", "Melee Damage", 250.0)
    assert res["stat_found"] is True
    assert res["value_found"] == 300.0
    assert res["approved"] is True
