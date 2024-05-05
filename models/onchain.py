from dataclasses import dataclass



@dataclass
class BridgeData:
    address: str = "0x57Fc396328b665f0f8bD235F0840fCeD43128c6b"
    abi: list = open("./abi/bridge.json", "r").read()
