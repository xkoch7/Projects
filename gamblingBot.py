import random
import discord
import asyncio
import json
import os

#grabbing users info from discord and reading it into a json file to store info
DATA_FILE = 'bank.json' #any file name works
def open_account(user_id):
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"users": []}

    if not any(user['id'] == user_id for user in data['users']):
        data['users'].append({"id": user_id, "wallet": 200})
        
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    return data

def change_money(user_id, amount):
    data = open_account(user_id)
    for user in data['users']:
        if user['id'] == user_id:
            user['wallet'] += amount
            break
            
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def reset_money(user_id, amount):
    data = open_account(user_id)
    for user in data["users"]:
        if user["id"] == user_id:
            user["wallet"] = amount
            break

    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

#setting a wheel for teh roulette function
ROULETTE_WHEEL = {
    0: "green", 1: "red", 2: "black", 3: "red", 4: "black", 5: "red",
    6: "black", 7: "red", 8: "black", 9: "red", 10: "black",
    11: "black", 12: "red", 13: "black", 14: "red", 15: "black",
    16: "red", 17: "black", 18: "red", 19: "red", 20: "black",
    21: "red", 22: "black", 23: "red", 24: "black", 25: "red",
    26: "black", 27: "red", 28: "black", 29: "black",
    30: "red", 31: "black", 32: "red", 33: "black",
    34: "red", 35: "black", 36: "red"
}
#setting options for slots function
slots = {
    1: "🍒 Cherry",
    2: "🍋 Lemon",
    3: "🍊 Orange",
    4: "🍉 Watermelon",
    5: "🍇 Grapes",
    6: "🔔 Bell",
    7: "⭐ Star",
    8: "💎 Diamond",
    9: "7️⃣ Lucky Seven",
    10: "🍀 Clover",
    11: "🔥 Fire",
    12: "⚡ Lightning",
    13: "👑 Crown",
    14: "🎰 Slot Machine",
    15: "💰 Money Bag",
    16: "🪙 Coin",
    17: "🎲 Dice",
    18: "🃏 Joker",
    19: "🃏 Wild Card",
    20: "🐉 Dragon"
}
#creating a deck for blackjack function (to be updated later)
def makedeck():
    deck = [ 
    "A♠","2♠","3♠","4♠","5♠","6♠","7♠","8♠","9♠","10♠","J♠","Q♠","K♠",
    "A♥","2♥","3♥","4♥","5♥","6♥","7♥","8♥","9♥","10♥","J♥","Q♥","K♥",
    "A♦","2♦","3♦","4♦","5♦","6♦","7♦","8♦","9♦","10♦","J♦","Q♦","K♦",
    "A♣","2♣","3♣","4♣","5♣","6♣","7♣","8♣","9♣","10♣","J♣","Q♣","K♣"
    ]
    return deck
#spinning slots fucntion definition
def spin_slots():
    number1 = random.randint(1,20)
    symbol1 = slots[number1]
    number2 = random.randint(1,20)
    symbol2 = slots[number2]
    number3 = random.randint(1,20)
    symbol3 = slots[number3]
    return symbol1, symbol2, symbol3
#spinning roulette wheel fucntion definition
def spin_wheel():
    number = random.randint(0, 36) 
    colour = ROULETTE_WHEEL[number]
    return number, colour

#class to read measages inside the server and run functions
class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        if message.author == self.user:
            return
        #reset money function since bot doed not use real money
        if message.content.startswith("$reset"):
            user_id = str(message.author.id)
            open_account(user_id)
            reset_money(user_id, 200)
            await message.channel.send('Your money has reset to 200!')
        #function to see you balance
        if message.content.startswith("$balance"):
            user_id = str(message.author.id)
            data = open_account(user_id)
            current_wallet = next(u['wallet'] for u in data['users'] if u['id'] == user_id)
            await message.channel.send(f'Your current balance is {current_wallet}')
        #calling the roulette function in the server (have not implemented green wheel option yet)
        if message.content.startswith("$roulette"):
            user_id = str(message.author.id)
            open_account(user_id)

            await message.channel.send("Enter your bet amount and choice (e.g., '50 red' or '10 15')")
            def check(m):
                return m.author == message.author and m.channel == message.channel
            
            try:
                msg = await self.wait_for("message", check=check, timeout=30.0)
                parts = msg.content.split()
                if len(parts) < 2:
                    await message.channel.send("Please provide both an amount and a choice. Try $roulette again.")
                    return

                try:
                    bet_amount = int(parts[0])
                    user_choice = parts[1].lower()
                except ValueError:
                    await message.channel.send("Invalid format for the amount. Try $roulette again.")
                    return
                data = open_account(user_id)
                current_wallet = next(u['wallet'] for u in data['users'] if u['id'] == user_id)

                if bet_amount > current_wallet or bet_amount <= 0:
                    await message.channel.send(f"You must bet a valid amount between $1 and ${current_wallet}. Try $roulette again.")
                    return 

                number, colour = spin_wheel()
                
                if user_choice == str(number):
                    win_amount = bet_amount * 10
                    change_money(user_id, -bet_amount)
                    change_money(user_id, win_amount)
                    await message.channel.send(f"The wheel landed on {number} {colour}. You won and gained ${win_amount}!")
                elif user_choice.lower() == "even" and number % 2 == 0:
                    win_amount = bet_amount * 2
                    change_money(user_id, -bet_amount)
                    change_money(user_id, win_amount)
                    await message.channel.send(f"The wheel landed on {number} {colour}. You won and gained ${win_amount}!")
                elif user_choice.lower() == "odd" and number % 2 != 0:
                    win_amount = bet_amount * 2
                    change_money(user_id, -bet_amount)
                    change_money(user_id, win_amount)
                    await message.channel.send(f"The wheel landed on {number} {colour}. You won and gained ${win_amount}!")
                elif user_choice == colour.lower() and (user_choice.lower() == "red" or user_choice.lower() == "black"):
                    win_amount = bet_amount * 2
                    change_money(user_id, -bet_amount)
                    change_money(user_id, win_amount)
                    await message.channel.send(f"The wheel landed on {number} {colour}. You won and gained ${win_amount}!")
                else:
                    change_money(user_id, -bet_amount)
                    await message.channel.send(f"The wheel landed on {number} {colour}. You lost ${bet_amount}.")
                
            except asyncio.TimeoutError:
                await message.channel.send("Timed out! You took too long to reply.")
        #calling slots function in server (to be updated with impoved odds and more options like wild cards)
        if message.content.startswith("$slots"):
            user_id = str(message.author.id)
            open_account(user_id)

            await message.channel.send("Enter your bet amount")
            def check(m):
                return m.author == message.author and m.channel == message.channel
            
            try:
                msg = await self.wait_for("message", check=check, timeout=30.0)
                parts = msg.content.split()
                if len(parts) != 1:
                    await message.channel.send("Please provide just an amount. Try $slots again.")
                    return
                try:
                    bet_amount = int(parts[0])
                except ValueError:
                    await message.channel.send("Invalid format for the amount. Try $slots again.")
                    return
                data = open_account(user_id)
                current_wallet = next(u['wallet'] for u in data['users'] if u['id'] == user_id)

                if bet_amount > current_wallet or bet_amount <= 0:
                    await message.channel.send(f"You must bet a valid amount between $1 and ${current_wallet}. Try $slots again.")
                    return 
                
                symbol1, symbol2, symbol3 = spin_slots()
                if symbol1 == symbol2 == symbol3:
                    lucky7 = "7️⃣ Lucky Seven"
                    count7 = 0
                    for symbol in (symbol1, symbol2, symbol3):
                        if symbol == lucky7:
                            count7 += 1
                    if count7 == 3:
                        win_amount = bet_amount * 50
                        change_money(user_id, -bet_amount)
                        change_money(user_id, win_amount)
                        await message.channel.send(f"{symbol1}{symbol2}{symbol3} JACKPOT! you won {win_amount}!")
                    else:
                        win_amount = bet_amount * 5
                        change_money(user_id, -bet_amount)
                        change_money(user_id, win_amount)
                        await message.channel.send(f"({symbol1}{symbol2}{symbol3}) you won {win_amount}!")
                else:
                    await message.channel.send(f"({symbol1}{symbol2}{symbol3}) you lost and fucking suck!")
                    change_money(user_id, -bet_amount)
            except asyncio.TimeoutError:
                await message.channel.send("Timed out! You took too long to reply.")
        #black jack function to be updated and finished

        # if message.content.startswith("$blackjack"):
        #     user_id = str(message.author.id)
        #     open_account(user_id)

        #     await message.channel.send("Enter your bet amount")
        #     def check(m):
        #         return m.author == message.author and m.channel == message.channel
            
        #     try:
        #         msg = await self.wait_for("message", check=check, timeout=30.0)
        #         parts = msg.content.split()
        #         if len(parts) != 1:
        #             await message.channel.send("Please provide just an amount. Try $blackjack again.")
        #             return
        #         try:
        #             bet_amount = int(parts[0])
        #         except ValueError:
        #             await message.channel.send("Invalid format for the amount. Try $blackjack again.")
        #             return
        #         data = open_account(user_id)
        #         current_wallet = next(u['wallet'] for u in data['users'] if u['id'] == user_id)

        #         if bet_amount > current_wallet or bet_amount <= 0:
        #             await message.channel.send(f"You must bet a valid amount between $1 and ${current_wallet}. Try $blackjack again.")
        #             return 
        #         current_deck = makedeck()
                

intents = discord.Intents.default()
intents.message_content = True


client = MyClient(intents=intents)
client.run("YOUR TOKEN HERE") #your discord bots specific token (do not share with others)
