from dataclasses import dataclass


@dataclass
class BridgeData:
    address: str = "0x57Fc396328b665f0f8bD235F0840fCeD43128c6b"
    abi: list = open("./abi/bridge.json", "r").read()


@dataclass
class GreenIDData:
    address: str = "0x776Fcec07e65dC03E35a9585f9194b8a9082CDdb"
    abi: list = open("./abi/green_id.json", "r").read()


@dataclass
class CommemorativeNFTData:
    address: str = "0xbc4b1cbbfF3Fe2C61Ad2Fd94b91126d5F7593D40"
    abi: list = open("./abi/commemorative_nft.json", "r").read()


@dataclass
class OmnihubData:
    address: str = "0xD473b08745288eF9b412a339ACCfaCce5Cebdd90"
    abi: list = open("./abi/omnihub.json", "r").read()


@dataclass
class MakeNFTGreatAgainData:
    address: str = "0x1a7464938aa694c5dB38Da52114C4fEdBc4EBF6A"
    abi: list = open("./abi/make_nft_great_again.json", "r").read()


@dataclass
class SummerNFTData:
    address: str = "0x98b322D37d54fac46f4980F4171bE2D0Ba8c54C2"
    abi: list = open("./abi/summer_nft.json", "r").read()


@dataclass
class MintFlagData:
    address: str = "0xa6660ba7F9a45e2707efC8dc574aF1DB4319Ee55"
    abi: list = open("./abi/mint_flag.json", "r").read()


@dataclass
class MintShopData:
    address: str = "0xBEEbbAEe8F085F506ce0eA3591f8FBb9C24Af356"
    abi: list = open("./abi/mint_shop.json", "r").read()


@dataclass
class MintAir3Data:
    address: str = "0x38f56A88a9eCD523086804f43Bdf881B8403107a"
    abi: list = open("./abi/mint_air3.json", "r").read()


@dataclass
class MintSupermintData:
    address: str = "0xDD351CDd289d9Bdf88D20EA3c9E316b99dF31412"
    abi: list = open("./abi/mint_supermint.json", "r").read()


@dataclass
class CometBridgeData:
    address: str = "0x0fbCf4a62036E96C4F6770B38a9B536Aa14d1846"
    abi: list = open("./abi/cometa.json", "r").read()


@dataclass
class Vip3MintData:
    address: str = "0xabe292b291A18699b09608de86888D77aD6BAf23"
    abi: list = open("./abi/vip3_nft.json", "r").read()


@dataclass
class GainfiMintData:
    address: str = "0xec863FCCfcbd25421D0747424e53ED0136aC9f82"
    abi: list = open("./abi/mint_gainfi.json", "r").read()
