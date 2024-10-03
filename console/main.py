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
        "Complete Tasks",
        "Mint Random All NFTs",
        "Claim Daily Rewards and Inject",
        "Find and Steal Other Trees Rewards",
        "Total Users",
        "Bridge ETH to MINT (via Comet)",
        "Only Claim Daily Rewards",
        "Export Trees IDs",
        "Fix sign",
        "Mint Green ID",
        "Mint Commemorative NFT",
        "Mint OmniHub Collection",
        "Mint Make NFT Great Again",
        "Mint Flag NFT",
        "Mint Shop NFT",
        "Mint Air3 NFT",
        "Mint SuperMint NFT",
        "Mint Owlto SummerFest NFT",
        "Mint Omnihub SummerFest NFT",
        "Mint Vip3 NFT",
        "Mint Gainfi NFT",
        "Exit",
    )
    MODULES_DATA = {
        "Complete Tasks": "tasks",
        "Claim Daily Rewards and Inject": "rewards",
        "Find and Steal Other Trees Rewards": "find_and_steal_other_trees_rewards",
        "Total Users": "total_user",
        "Mint Random All NFTs": "mint_random_all_nfts",
        "Bridge ETH to MINT (via Comet)": "comet_bridge",
        "Export Trees IDs": "export_trees_ids",
        "Only Claim Daily Rewards": "only_rewards",
        "Fix sign": "fix_sign",
        "Mint Commemorative NFT": "mint_comm_nft",
        "Mint Make NFT Great Again": "mint_make_nft_great_again",
        "Mint Flag NFT": "mint_flag",
        "Mint Shop NFT": "mint_shop",
        "Mint Air3 NFT": "mint_air3",
        "Mint SuperMint NFT": "mint_supermint",
        "Mint Owlto SummerFest NFT": "mint_owlto_summer_nft",
        "Mint Omnihub SummerFest NFT": "mint_omnihub_summer_nft",
        "Mint Vip3 NFT": "mint_vip3_nft",
        "Mint Green ID": "mint_green_id",
        "Mint Gainfi NFT": "mint_gainfi_nft",
    }

    @staticmethod
    def show_dev_info():
        os.system("cls")
        tprint("JamBit  &  Mr. X")
        print("\033[36m" + "VERSION: " + "\033[34m" + "4.0" + "\033[34m")
        print(
            "\033[36m" + "Channel: " + "\033[34m" + "https://t.me/JamBitPY" + "\033[34m"
        )
        print(
            "\033[36m" + "Channel: " + "\033[34m" + "https://t.me/mrxcrypto" + "\033[34m"
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
            + "GitHub: "
            + "\033[34m"
            + "https://github.com/mrxdegen"
            + "\033[34m"
        )
        print(
            "\033[36m"
            + "JAMBIT DONATION EVM ADDRESS: "
            + "\033[34m"
            + "0xe23380ae575D990BebB3b81DB2F90Ce7eDbB6dDa"
            + "\033[0m"
        )
        print(
            "\033[36m"
            + "MR. X DONATION EVM ADDRESS: "
            + "\033[34m"
            + "0xB12B3Df66BaE895916d18248435928892B3D3aae"
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
