import json

# Mapping ID YouTube baru (Mayoritas IGN Review & Gameplay Tanpa Batasan Usia/Embed)
NEW_TRAILERS = {
    "Celeste": "iofYDsA2yqc",
    "Firewatch": "cXWbVuJqeNg",
    "Journey": "mU3nNT4ncFw",
    "A Short Hike": "_yqgK-6E6Qo",
    "Hades": "mD8BNcwCAhw",
    "Doom Eternal": "FkklG9MA0vM",
    "Devil May Cry 5": "K1Hw1pA4wbg",
    "Disco Elysium": "T_jG-m_2z4Q",
    "What Remains of Edith Finch": "2j1w2KAY-xM",
    "Outer Wilds": "d6LGnV4wShA",
    "Baldur's Gate 3": "1T22wetXQDU",
    "Divinity: Original Sin 2": "bTWTFX8qzPI",
    "Dark Souls III": "_zDZYrIUgKE",
    "Dead Cells": "RvGJUJnt808",
    "Shovel Knight": "jo-XqOQZeqM",
    "Ori and the Blind Forest": "cklw-Yu3moE",
    "Cuphead": "4TjUPXAn2Rg",
    "Limbo": "a6uvTGB0L1I",
    "Undertale": "1Hojv0m3TqA",
    "Night in the Woods": "4wJt8Q1jYg0",
    "Oxenfree": "kH_gL1_i-sI",
    "Gris": "B0g1e9rM9hA",
    "Spiritfarer": "YwuERutjK2c",
    "Prey (2017)": "Lq2OQvHkXEQ",
    "BioShock Infinite": "bLHW78X1XeE",
    "Titanfall 2": "EXwdWuSuiEA",
    "Monster Hunter: World": "Ro6r15wzp2Y",
    "Persona 5 Royal": "D_A59h7k0tM",
    "Subnautica": "Rz2SNm8VguE",
    "Into the Breach": "0yYk9zD37Zc",
    "Slay the Spire": "1kEwQvNlFwA",
    "FTL: Faster Than Light": "dK-dITxT8O0",
    "Ori and the Will of the Wisps": "2reK8kGEqJw",
    "Katana ZERO": "zXzP3I7UuGw",
    "Disco Elysium: The Final Cut": "T_jG-m_2z4Q",
    "Hades II": "l-iHDbE1nZ4",
    "Vampire Survivors": "QZ9W3zP_Nsc",
    "Resident Evil 4 Remake": "j5Xv2lM9MEs",
    "Deus Ex: Mankind Divided": "q2kd7F3YFz8",
    "Bastion": "Tpt0Z9I0-Lg",
    "Transistor": "RT55lch6y_U",
    "Pyre": "9Q8x-nN_4aA",
    "Tunic": "V-H38iX-R7o",
    "Hob": "qCUKH0B0V3w",
    "Chicory: A Colorful Tale": "P8kG5p3-W8Y",
    "Doki Doki Literature Club": "w9AWvii8vEw",
    "Omori": "A4zOa3d0mBc",
    "Pathfinder: Wrath of the Righteous": "Q-q4t4qM-W8",
    "Pillars of Eternity II": "O9h8Vp_WEMk",
    "Planescape: Torment Enhanced": "3Fw2zZ9D0oA",
    "Unpacking": "wJ_dF-v1sO8",
    "Coffee Talk": "cZ2r0R731iA",
    "Alba: A Wildlife Adventure": "R4aC08qJ1-c",
    "Flower": "nJqzXgI44vE",
    "Abzu": "P2G54w8H4oM",
    "Euro Truck Simulator 2": "xlTuC18xVII",
    "Talos Principle": "mHj_bQ1fXEM",
    "Antichamber": "fXqAmJm1aGE",
    "The Room": "x2w6K8F8p2A",
    "Myst": "pBw8k0V2Gxc",
    "Ace Attorney Trilogy": "y0m8aY1l2U4",
    "Danganronpa 1-2 Reload": "v4E_W8p9WcE",
    "NieR: Automata": "ARHVsBbyzXU",
    "Ghostrunner": "PoRzRB8bIoE",
    "Hyper Light Drifter": "uNENfF3O_wY",
    "Enter the Gungeon": "1Yw0pQx3O0w",
    "Risk of Rain 2": "Z1m_tQp9hZg",
    "Spelunky 2": "nZ5vQf3z9K4",
    "Salt and Sanctuary": "b9R8G0r2aCg",
    "Blasphemous": "uF8A9b1T2Y0",
    "Metroid Dread": "ER_x4vXS3Ag",
    "Graveyard Keeper": "A-M60u9m67M",
    "Planet Coaster": "2vWw9Y-oDxg",
    "Factorio": "KVvXv1Z6EY8",
    "Kenshi": "v_h2h2xG2_w",
    "Tyranny": "9H8x0w1_qT4",
    "Torchlight II": "1q_1K2Z0oQ0",
    "This War of Mine": "Hk1qZ1W_a_E",
    "Frostpunk": "qqEpCBt_ZgI",
    "Papers Please": "_WEuG3X_3aA",
    "A Plague Tale: Innocence": "b3v_B1n2Otc",
    "Twelve Minutes": "4WzW8gq-g8Q"
}

def update_seed_file():
    file_path = "data/games_seed.json"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            games = json.load(f)
    except FileNotFoundError:
        print(f"File {file_path} tidak ditemukan. Pastikan path-nya sesuai.")
        return

    updated_count = 0
    for game in games:
        title = game.get("title")
        if title in NEW_TRAILERS:
            game["trailer_youtube_id"] = NEW_TRAILERS[title]
            updated_count += 1

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(games, f, indent=2)

    print(f"✅ Berhasil memperbarui {updated_count} ID trailer YouTube di {file_path}!")

if __name__ == "__main__":
    update_seed_file()