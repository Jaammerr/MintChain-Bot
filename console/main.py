import os
import sys
import inquirer

from inquirer.themes import GreenPassion
from art import tprint

from colorama import Fore
from loader import config
from .logger import info_log

sys.path.append(os.path.realpath("."))


class Console:
    MODULES = (
        "Claim Points Onchain and Inject",
        "Claim Boxes Onchain",
        "Steal Energy Onchain",
        "Spin Turntable Onchain",
        "Bridge from OP to MINT (CometBridge)",
        "Mint Green ID NFT",
        "Exit",
    )
    MODULES_DATA = {
        "Claim Points Onchain and Inject": "claim_points_onchain_and_inject",
        "Claim Boxes Onchain": "claim_boxes_onchain",
        "Steal Energy Onchain": "steal_energy_onchain",
        "Spin Turntable Onchain": "spin_turntable_onchain",
        "Bridge from OP to MINT (CometBridge)": "comet_bridge_onchain",
        "Mint Green ID NFT": "mint_green_id_nft",
    }

    @staticmethod
    def show_dev_info():
        os.system("cls")
        tprint("JamBit")
        print("\033[36m" + "VERSION: " + "\033[34m" + "3.0" + "\033[34m")
        print(
            "\033[36m" + "Channel: " + "\033[34m" + "https://t.me/JamBitPY" + "\033[34m"
        )
        print(
            "\033[36m"
            + "GitHub: "
            + "\033[34m"
            + "https://github.com/Jaammerr"
            + "\033[34m"
        )
        print(
            "\033[36m"
            + "DONATION EVM ADDRESS: "
            + "\033[34m"
            + "0xe23380ae575D990BebB3b81DB2F90Ce7eDbB6dDa"
            + "\033[0m"
        )
        print()

    @staticmethod
    def prompt(data: list):
        answers = inquirer.prompt(data, theme=GreenPassion())
        return answers

    def get_module(self):
        questions = [
            inquirer.List(
                "module",
                message=Fore.LIGHTBLACK_EX + "Select the module",
                choices=self.MODULES,
            ),
        ]

        answers = self.prompt(questions)
        return answers.get("module")

    def build(self) -> None:
        os.system("cls")
        self.show_dev_info()
        info_log(
            f"\n- accounts: {len(config.accounts)}\n- referral_code: {config.referral_code}\n- threads: {config.threads}\n"
        )

        module = self.get_module()
        if module == "Exit":
            exit(0)

        config.module = self.MODULES_DATA[module]
