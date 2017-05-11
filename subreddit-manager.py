# Created by Michael Fessenden (MikeFez)
# Requires Python 2.7
# Must have beautifulsoup4 & requests installed

# -*- coding: utf-8 -*-

# Downloaded Packages
import requests
import requests.utils  # Used for receiving webpage responses
import bs4  # Used to parse webpage
import getpass
import os

session = requests.session()
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'}
subreddit_file = "files/reddit/subreddits.txt"


def main():
    print("Please Choose An Option:")
    print("[1] backup\t- saves a list of subreddit subscriptions to a file")
    print("[2] restore\t- subscribes to subreddits listed in backup file, unsubscribing from current subreddits")
    print("[3] clear\t- unsubscribes from all subreddits in an account")
    print("[4] merge\t- subscribes to subreddits listed in backup file, keeping current subscriptions.")
    print("\n")
    run_type = input("Please enter the number of the option you'd like: ")
    while not run_type.isdigit() or int(run_type) < 1 or int(run_type) > 4:
        print("Unexpected input!")
        run_type = input("Please enter the number of the option you'd like: ")

    run_type = int(run_type)

    logged_in = False
    while logged_in is False:
        logged_in = login()

    if run_type == 1:  # backup
        if confirm("Warning - This will overwrite previous backup - are you sure?"):
            backup()

    elif run_type == 2:  # restore
        if confirm("Warning - This will clear your current subreddits before restoring - are you sure?"):
            if file_check():
                clear()
                restore()

    elif run_type == 3:  # clear
        if confirm("Warning - This will clear your current subreddits - are you sure?"):
                clear()

    elif run_type == 4:  # merge
        if confirm("Warning - This will merge your current subreddits with those backed up - are you sure?"):
            restore()
    return


def confirm(message):
    state = False
    option = input(message + " (y/n): ")
    while option != "y" and option != "n":
        print("Unexpected input!")
        option = input(message + " (y/n): ")
    if option == "y":
        state = True
    elif option == "n":
        print("Canceling...")
    return state


def file_check():
    state = False
    try:
        if os.stat(subreddit_file).st_size > 0:
            state = True
        else:
            print("Warning - Backup file (subreddits.txt) was found, but is empty!")
            print("Canceling...")
    except OSError:
        print("Warning - No backup file (subreddits.txt) was found!")
        print("Canceling...")
    return state


# Logs into SF
def login():
    username = input("Enter your reddit username: ")
    password = getpass.getpass()

    payload = {
        "dest": "https://www.reddit.com/",
        "user": username,
        "passwd": password,
        "rem": "",
        "op": "login"
    }
    res = session.post("https://www.reddit.com/api/login/" + username, data=payload, headers=headers)
    res.raise_for_status()
    success = False
    if "WRONG_PASSWORD" not in res.text:
        print("Successfully Logged In\n")
        success = True
    else:
        print("Error - Wrong Password or Username! Please try again.")
    return success


def backup():
    res = session.get("https://www.reddit.com/subreddits/mine", headers=headers)
    res.raise_for_status()
    sub_result = bs4.BeautifulSoup(res.text, "html.parser")
    sub_box = sub_result.find("div", {"class": "subscription-box"})
    sub_items = sub_box.findAll('li')

    sub_dict = {}
    for li in sub_items:
        ban_check = li.find('span', {"class": "title banned"})
        if ban_check is None:
            id_raw = li.find('a', href=True, text='unsubscribe')
            id_raw = id_raw["onclick"].split("('")
            id_raw = id_raw[1].split("')")
            sub_id = id_raw[0]

            sub_link = li.find('a', {"class": "title"})
            sub_dict[sub_id] = sub_link['href']

    with open(subreddit_file, 'w+') as f:
        for sub_id, sub_link in list(sub_dict.items()):
            print("Saving to file: " + sub_link)
            f.write(sub_id + '|' + sub_link + '\n')

    return


def clear():
    res = session.get("https://www.reddit.com/subreddits/mine", headers=headers)
    res.raise_for_status()
    sub_result = bs4.BeautifulSoup(res.text, "html.parser")

    modhash_raw = sub_result.find("input", {"name": "uh"})
    modhash = modhash_raw["value"]

    sub_box = sub_result.find("div", {"class": "subscription-box"})
    sub_items = sub_box.findAll('li')

    sub_dict = {}
    for li in sub_items:
        id_raw = li.find('a', href=True, text='unsubscribe')
        id_raw = id_raw["onclick"].split("('")
        id_raw = id_raw[1].split("')")
        sub_id = id_raw[0]

        sub_link = li.find('a', {"class": "title"})

        sub_dict[sub_id] = sub_link['href']

    for sub_id, sub_link in list(sub_dict.items()):
        payload = {
            "sr": sub_id,
            "action": "unsub",
            "uh": modhash,
            "renderstyle": "html"
        }
        print("Unsubscribing from " + sub_link)
        res = session.post("https://www.reddit.com/api/subscribe", data=payload, headers=headers)
        res.raise_for_status()

    return


def restore():
    sub_dict = {}
    with open(subreddit_file, 'r') as f:
        for line in f:
            line_raw = line.rstrip('\n')
            line_raw = line_raw.split('|')
            sub_dict[line_raw[0]] = line_raw[1]

    res = session.get("https://www.reddit.com/subreddits/mine", headers=headers)
    res.raise_for_status()
    sub_result = bs4.BeautifulSoup(res.text, "html.parser")

    modhash_raw = sub_result.find("input", {"name": "uh"})
    modhash = modhash_raw["value"]

    sub_box = sub_result.find("div", {"class": "subscription-box"})
    sub_items = sub_box.findAll('li')

    id_list = []
    for li in sub_items:
        id_raw = li.find('a', href=True, text='unsubscribe')
        id_raw = id_raw["onclick"].split("('")
        id_raw = id_raw[1].split("')")
        sub_id = id_raw[0]
        id_list.append(sub_id)

    for sub_id, sub_link in list(sub_dict.items()):
        if sub_id not in id_list:
            payload = {
                "sr": sub_id,
                "action": "sub",
                "uh": modhash,
                "renderstyle": "html"
            }

            try:
                res = session.post("https://www.reddit.com/api/subscribe", data=payload, headers=headers)
                res.raise_for_status()
                print("Subscribing to " + sub_link)
            except requests.exceptions.RequestException as e:  # This is the correct syntax
                if "403 Client Error" in str(e):
                    print("Could Not Subscribe to " + sub_link + " - Community is invite only or banned")
        else:
            print("Already Subscribed to " + sub_link)

    return

if __name__ == '__main__':
    continue_script = True
    while continue_script is True:
        main()
        print("\nProcess Complete!")
        if not confirm("Would you like to perform an additional task?"):
            continue_script = False

    print("Exiting")
