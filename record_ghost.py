import import_ghost_to_save
import gen_gecko_codes
from gen_gecko_codes import GeckoParam

def main():
    rkg = import_ghost_to_save.import_ghost_to_save(
        "rksys.dat", "01m08s7732250 Cole.rkg",
        "dolphin/User/Wii/title/00010004/524d4345/data/rksys.dat",
        "dolphin/User/Wii/shared2/menu/FaceLib/RFL_DB.dat"
    )

    params = gen_gecko_codes.create_gecko_code_params_from_rkg(rkg)
    gen_gecko_codes.create_gecko_code_file("RMCE01_gecko_codes_template.ini", "dolphin/User/GameSettings/RMCE01.ini", params)

if __name__ == "__main__":
    main()
