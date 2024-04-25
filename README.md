
# MintChain Daily Bot

## 🔗 Links

🔔 CHANNEL: https://t.me/JamBitPY

💬 CHAT: https://t.me/JamBitChat

💰 DONATION EVM ADDRESS: 0x08e3fdbb830ee591c0533C5E58f937D312b07198


## 🤖 | Features:

- **Auto registration**
- **Auto bind referral**
- **Auto bind twitter**
- **Auto collect twitter tasks**
- **Auto collect daily rewards every X time**


## 🚀 Installation

``Docker``


``1. Close the repo and open CMD (console) inside it``

``2. Setup configuration and accounts``

``3. Run: docker-compose up -d --build``

``OR``


`` Required python >= 3.10``

``1. Close the repo and open CMD (console) inside it``

``2. Install requirements: pip install -r requirements.txt``

``3. Setup configuration and accounts``

``4. Run: python run.py``


## ⚙️ Config (config > settings.yaml)

| Name | Description                                                                                        |
| --- |----------------------------------------------------------------------------------------------------|
| referral_code | Your referral code                                                                                 |
| rpc_url | RPC URL (if not have, leave the default value)                                                     |
| iteration_delay | Delay between iterations in hours (Let's say every 24 hours the script will collect daily rewards) |


## ⚙️ Accounts format (config > accounts.txt)

- twitter_auth_token|wallet_mnemonic|proxy|proxy_change_url
- twitter_auth_token|wallet_mnemonic|proxy
- twitter_auth_token|wallet_mnemonic

`` Proxy format: IP:PORT:USER:PASS``
