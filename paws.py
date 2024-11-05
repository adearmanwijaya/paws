import json
import requests
import time
import urllib3
from colorama import init, Fore, Style
from mnemonic import Mnemonic
from nacl.signing import SigningKey
from hashlib import sha256
import base58

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
init(autoreset=True)






RED = Fore.RED + Style.BRIGHT
GREEN = Fore.GREEN + Style.BRIGHT
YELLOW = Fore.YELLOW + Style.BRIGHT
CYAN = Fore.CYAN + Style.BRIGHT
WHITE = Fore.WHITE + Style.BRIGHT
BLUE = Fore.BLUE + Style.BRIGHT

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Cache-Control': 'no-cache',
    'Origin': 'https://app.notpx.app',
    'Pragma': 'no-cache',
    'Referer': 'https://app.notpx.app/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Content-Type': 'application/json'
})

def generate_mnemonic():
    """Generate a mnemonic phrase for a TON wallet."""
    mnemo = Mnemonic("english")
    mnemonic_phrase = mnemo.generate(256)
    return mnemonic_phrase

def get_wallet_from_mnemonic(mnemonic_phrase):
    """Derive key pair and simulate TON wallet address from mnemonic."""

    seed = Mnemonic.to_seed(mnemonic_phrase)
    

    signing_key = SigningKey(seed[:32])  
    verify_key = signing_key.verify_key
    
    private_key = signing_key.encode().hex()
    public_key = verify_key.encode().hex()
    

    sha256_hash = sha256(verify_key.encode()).digest()
    ton_address = "UQ" + base58.b58encode(sha256_hash).decode()

    return {
        "TON Wallet Address": ton_address,
        "Mnemonic Phrase": mnemonic_phrase,
        "Private Key": private_key,
    }


def save_wallet_to_file(wallet_data, username):
    """Save wallet mnemonic, address, private key, and username to files."""

    with open("wallet.txt", "a", encoding="utf-8") as wallet_file:
        wallet_file.write(f"{wallet_data['TON Wallet Address']}\n")
    
    with open("phrase.txt", "a", encoding="utf-8") as mnemonic_file:
        mnemonic_file.write(f"---- User: {username} ----\n")
        mnemonic_file.write(f"Mnemonic Phrase: {wallet_data['Mnemonic Phrase']}\n")
        mnemonic_file.write(f"Private Key: {wallet_data['Private Key']}\n")
        mnemonic_file.write(f"TON Wallet Address: {wallet_data['TON Wallet Address']}\n")
        mnemonic_file.write("\n")
    
    print(f"{GREEN}Wallet details saved for user: {WHITE}{username}")


def getData(init_data, reff):
    print(f"{CYAN}[ 🔑 ] Reff code: {WHITE}{reff}")
    url = "https://api.paws.community/v1/user/auth"
    data = json.dumps({
        "data": init_data,
        "referralCode": reff
    })
    try:
        response = session.post(url, data=data, verify=False)
        if response.status_code in [200, 201]:
            response_json = response.json()
            if response_json.get("success"):
                return response_json
            else:
                print(f"{RED}[ ❌ ] Failed Get Access Token. {response_json}")
        else:
            print(f"{RED}[ ❌ ] Failed Get Access Token. {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"{RED}[ ❌ ] Failed Get Access Token. : {e}")
    return None

def refferal(token):
    url = "https://api.paws.community/v1/referral/my"
    session.headers['Authorization'] = f'Bearer {token}'
    try:
        response = session.get(url, verify=False)
        if response.status_code == 200 and response.json().get("success"):
            print(f"{GREEN}[ 🚀 ] Reff: Success Reff!")
            return True
    except requests.exceptions.RequestException as e:
        print(f"{RED}Referral injection error: {e}")
    print(f"{RED}Failed referral injection.")
    return False

def getUser(token):
    """Retrieve user data and check if wallet is already connected."""
    url = "https://api.paws.community/v1/user"
    session.headers['Authorization'] = f'Bearer {token}'
    retry_attempts = 5
    for attempt in range(retry_attempts):
        try:
            response = session.get(url, verify=False)
            if response.status_code == 200:
                ress = response.json()
                if ress.get("success"):
                    username = ress["data"]["userData"].get("username", "Unknown")
                    balance = ress["data"]["gameData"].get("balance", "N/A")
                    wallet_address = ress["data"]["userData"].get("wallet", None)
                    if wallet_address:
                        pass
                    else:
                        print(f"{CYAN}[ 🔗 ] Wallet : No wallet")
                    return username, balance, wallet_address
                else:
                    print(f"{RED}[ ❌ ] Wallet : Failed to get user information.")
            elif response.status_code == 503:
                print(f"{RED}[ ❌ ] Wallet : Failed to get user data with status code 503. Retrying... ({attempt + 1}/{retry_attempts})")
                time.sleep(1)  # Optional: wait before retrying
            else:
                print(f"{RED}[ ❌ ] Wallet : Failed to get user data with status code {response.status_code}")
                break
        except requests.exceptions.RequestException as e:
            print(f"{RED}[ ❌ ] Wallet : Get user error: {e}")
    return None, None, None

def getTask(token):
    url = "https://api.paws.community/v1/quests/list"
    session.headers['Authorization'] = f'Bearer {token}'
    retry_attempts = 5
    for attempt in range(retry_attempts):
        try:
            response = session.get(url, verify=False)
            if response.status_code in [200, 201, 204]:
                ress = response.json()
                for quest in ress['data']:
                    if quest["progress"]["current"] == 0:
                        if startTask(token, quest["_id"], quest["title"], quest['rewards'][0]['amount']):
                            print(f"{GREEN}          ➤ Successfully completed task: {WHITE}{quest['title']}")
                        else:
                            print(f"{YELLOW}          ➤ Skipped task: {WHITE}{quest['title']} (could not complete)")
                    elif quest["progress"]["current"] == 1 and not quest["progress"]["claimed"]:
                        claimTask(token, quest["_id"], quest["title"], quest['rewards'][0]['amount'])
                break
            elif response.status_code == 503:
                print(f"{RED}          ➤ Failed to get tasks with status code 503. Retrying... ({attempt + 1}/{retry_attempts})")
                time.sleep(1)  # Optional: wait before retrying
            else:
                print(f"{RED}          ➤ Failed to get tasks with status code {response.status_code}")
                break
        except requests.exceptions.RequestException as e:
            print(f"{RED}          ➤ Get task error: {e}")

def startTask(token, quest_id, quest_title, quest_reward):
    url = 'https://api.paws.community/v1/quests/completed'
    session.headers['Authorization'] = f'Bearer {token}'
    data = json.dumps({"questId": quest_id})
    try:
        response = session.post(url, data=data, verify=False)
        if response.status_code in [200, 201, 204]:
            ress = response.json()
            return ress.get("success") and ress.get("data")
    except requests.exceptions.RequestException as e:
        print(f"{RED}Start task error: {e}")
    return False

def claimTask(token, quest_id, quest_title, quest_reward):
    url = 'https://api.paws.community/v1/quests/claim'
    data = json.dumps({"questId": quest_id})
    session.headers['Authorization'] = f'Bearer {token}'
    try:
        response = session.post(url, data=data, verify=False)
        if response.status_code in [200, 201, 204] and response.json().get("success"):
            print(f"{GREEN}          ➤ Task: {WHITE}{quest_title} {GREEN}. Reward: {quest_reward}")
    except requests.exceptions.RequestException as e:
        print(f"{RED}          ➤ Claim task error: {e}")

def connectWallet(token, wallet_address):
    url = "https://api.paws.community/v1/user/wallet"
    session.headers['Authorization'] = f'Bearer {token}'
    data = json.dumps({"wallet": wallet_address})
    
    try:
        response = session.post(url, data=data, verify=False)
        if response.status_code == 201:
            ress = response.json()
            if ress.get("success"):
                print(f"{GREEN}[ ✨ ] Wallet connected successfully!")
                return ress["data"]
            else:
                print(f"{RED}[ ❌ ] Failed to connect wallet.")
        else:
            print(f"{RED}[ ❌ ] Failed to connect wallet with status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"{RED}[ ❌ ] Wallet connection error: {e}")
    return None

def main():
    print(Fore.WHITE + r""" 
          
🆂🅸🆁🅺🅴🅻
          
█▀▀ █▀▀ █▄░█ █▀▀ █▀█ █▀█ █░█ █▀
█▄█ ██▄ █░▀█ ██▄ █▀▄ █▄█ █▄█ ▄█
          """)
    
    print(f"Auto Refferal and Clear Task PAWS")
    querr = "query.txt"
    reff_file = "codereff.txt"
    task_flag = input("Do you want to claim tasks? (y/n): ") or 'y'
    wallet_flag = input("Do you want to connect and generate a wallet? (y/n): ") or 'n'
    bot_delay = input("Enter the bot delay in seconds between accounts: ") or '1'
    bot_delay = int(bot_delay)

    with open(reff_file, 'r') as file:
        ref_codes = [line.strip() for line in file.readlines()]

    ref_index = 0  
    account_count = 0
    total_balance = 0
    with open(querr, 'r') as file:
        for line in file:
            init_data = line.strip()
            
            if account_count % 10 == 0 and account_count > 0:
                ref_index = (ref_index + 1) % len(ref_codes)
            reff = ref_codes[ref_index]

            print(f"{BLUE}\n{'-'*40}")
            print(f"{BLUE}Processing Account #{account_count + 1}")
            print(f"{BLUE}{'-'*40}{WHITE}")
            
            retry_attempts = 3
            for attempt in range(retry_attempts):
                try:
                    result = getData(init_data, reff)
                    # print(result)
                    if result:
                        token = result["data"][0]
                        user_data = result.get("data", [None, {}])[1]
                        username = user_data.get("userData", {}).get("username") or "No Username"
                        firstname = user_data.get("userData", {}).get("firstname")
                        balance = user_data.get("gameData", {}).get("balance")
                        print(f"{YELLOW}[ 👑 ] Name : {firstname} | {username}")
                        total_balance += balance 
                        allocation_data = user_data["allocationData"]
                        hamster_allocation = allocation_data["hamster"]["converted"]
                        dogs_allocation = allocation_data["dogs"]["converted"]
                        paws_allocation = allocation_data["paws"]["converted"]
                        not_allocation = allocation_data["notcoin"]["converted"]
                        telegram_age = allocation_data["telegram"]["age"]
                        telegram_year = allocation_data["telegram"]["year"]
                        telegram_allocation = allocation_data["telegram"]["converted"]
                        total_allocation = allocation_data["total"]
                        print(f"{CYAN}[ 🎖️ ] Allocation Information") 
                        print(f"{WHITE}          ➤ 🐹 Hamster : {hamster_allocation}")
                        print(f"{WHITE}          ➤ 🦴 Dogs : {dogs_allocation}")
                        print(f"{WHITE}          ➤ 🐾 Paws : {paws_allocation}")
                        print(f"{WHITE}          ➤ ⚠️ Notcoin : {not_allocation}")
                        print(f"{WHITE}          ➤ 💬 Telegram : {telegram_allocation} [ Age {telegram_age} | {telegram_year} ]")
                        print(f"{WHITE}          ➤ 📊 Total Allocation : {total_allocation}")
                        print(f"{GREEN}[ 💵 ] Balance : {balance}")
                        
                        refferal(token)
                        username, balance, existing_wallet_address = getUser(token)
                        
                        if wallet_flag.lower() == 'y' and not existing_wallet_address:
                            wallet_data = get_wallet_from_mnemonic(generate_mnemonic())
                            save_wallet_to_file(wallet_data, f"Account #{account_count + 1} {username} {firstname}")
                            connectWallet(token, wallet_data["TON Wallet Address"])
                        elif existing_wallet_address:
                            print(f"{YELLOW}[ 🔗 ] Wallet : Already Connected. {existing_wallet_address}")
                        
                        if task_flag.lower() == 'y':
                            print(f"{CYAN}[ 📝 ] Task Information") 
                            getTask(token)
                        account_count += 1
                    break  # Exit retry loop if successful
                except KeyError as e:
                    print(f"{RED}[ ❌ ] Error Get Data. Retrying... ({attempt + 1}/{retry_attempts})")
                    time.sleep(1)  # Optional: wait before retrying
                except Exception as e:
                    print(f"{RED}[ ❌ ] Unexpected error: {e}. Retrying... ({attempt + 1}/{retry_attempts})")
                    time.sleep(1)  # Optional: wait before retrying

            time.sleep(bot_delay)   
        formatted_balance = f"{total_balance:,}".replace(",", ".")
        print(f"{GREEN} TOTAL BALANCE: {formatted_balance}")

if __name__ == "__main__": 
    main()