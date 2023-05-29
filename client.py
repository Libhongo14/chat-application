import ast
import hashlib
import multiprocessing
import sys
import time
from socket import *
from threading import Thread

import auth


class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BLINKING = '\033[5m'
    GREEN_HIGHLIGHTED = '\033[102m'
    YELLOW_HIGHLIGHTED = '\033[43m'
    RED_HIGHLIGHTED = '\033[91m'
    BLUE_HIGHLIGHTED = '\033[104m'
    WHITE_HEIGHLIGHTED = '\033[7m'

serverName = gethostname()
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_DGRAM)

# This data structure holds the currently logged in user
currently_logged_user = {
    "username": "",
    "password": ""
}

def login_and_connect_client(message = {}):
    """ This function sends a message to the server to login & establish a connection """
    
    message_struct = {
        "header": {
            "command": "LOGIN",
            "message_type": "INITIATE_SESSION",
            "recipient_data": (serverName, serverPort),
        },
        "body": message
    }

    h = hashlib.sha256(str(message_struct))
    hashedMessageValue = h.hexdigest()

    toBeSentMessage = str([message_struct,  hashedMessageValue]).encode()
    clientSocket.sendto(toBeSentMessage, (serverName, serverPort))

def logout_and_disconnect_client(message = {}):
    """ This function sends a message to the server to logout & disconnect connection """

    message_struct = {
        "header": {
            "command": "LOGOUT",
            "message_type": "DESTROY_SESSION",
            "recipient_data": (serverName, serverPort),
        },
        "body": message
    }
    
    h = hashlib.sha256(str(message_struct))
    hashedMessageValue = h.hexdigest()

    toBeSentMessage = str([message_struct,  hashedMessageValue]).encode()
    clientSocket.sendto(toBeSentMessage, (serverName, serverPort))
    
def message_to_online_user(message = {}):
    """ This function sends a message to an online user """

    message_struct = {
        "header": {
            "command": "SEND_MESSAGE",
            "message_type": "MESSAGE_EXCHANGE",
            "recipient_data": (serverName, serverPort),
        },
        "body": message
    }
    
    h = hashlib.sha256(str(message_struct))
    hashedMessageValue = h.hexdigest()

    toBeSentMessage = str([message_struct,  hashedMessageValue]).encode()
    clientSocket.sendto(toBeSentMessage, (serverName, serverPort))

def message_to_all_users(message = {}):
    """ This function sends a message to all online users """

    message_struct = {
        "header": {
            "command": "SEND_ALL_MESSAGE",
            "message_type": "MESSAGE_EXCHANGE",
            "recipient_data": (serverName, serverPort),
        },
        "body": message
    }
    
    h = hashlib.sha256(str(message_struct))
    hashedMessageValue = h.hexdigest()

    toBeSentMessage = str([message_struct,  hashedMessageValue]).encode()
    clientSocket.sendto(toBeSentMessage, (serverName, serverPort))
    
def show_connected_clients(message = {}):
    """ This function requests for online users"""

    message_struct = {
        "header":{
            "command": "CONTACTS",
            "message_type": "DISPLAY_CONTACTS",
            "recipient_data": "",
        },
        "body": message
    } 

    h = hashlib.sha256(str(message_struct))
    hashedMessageValue = h.hexdigest()

    toBeSentMessage = str([message_struct,  hashedMessageValue]).encode()
    clientSocket.sendto(toBeSentMessage, (serverName, serverPort))

def logout_and_disconnect_client(message = {}):
    """ This function sends a message to the server to logout & disconnect """

    message_struct = {
        "header": {
            "command": "LOGOUT",
            "message_type": "DETROY_SESSION",
            "recipient_data": (serverName, serverPort),
        },
        "body": message
    }

    h = hashlib.sha256(str(message_struct))
    hashedMessageValue = h.hexdigest()

    toBeSentMessage = str([message_struct,  hashedMessageValue]).encode()
    clientSocket.sendto(toBeSentMessage, (serverName, serverPort))

def send_acknowledgement_message(message = {}):
    message_struct = {
        "header": {
            "command": "",
            "message_type": "ACKNOWLEDGEMENT",
            "recipient_data": (serverName, serverPort),
        },
        "body": message
    }  

    h = hashlib.sha256(str(message_struct))
    hashedMessageValue = h.hexdigest()

    toBeSentMessage = str([message_struct,  hashedMessageValue]).encode()
    clientSocket.sendto(toBeSentMessage, (serverName, serverPort))

def receive():
    """ Handles receiving of messages from the server. """

    while True:
        try:
            message, _ = clientSocket.recvfrom(2048)

            # transform dictionary in text format to dictionary format (text -> dict)
            dictMessage = ast.literal_eval(message.decode())

            header = dictMessage["header"]
            message_type = header["message_type"]
            command = header["command"]
            message = dictMessage["body"]

            # print the text if message type of ALERT, GREETING OR ACKNOWLEDGEMENT
            if len(command) == 0 or command == "":
                if message_type == "ACKNOWLEDGEMENT":
                    print(bcolors.GREEN + message + bcolors.ENDC)

                elif message_type == "GREETING":
                    print(bcolors.BLUE_HIGHLIGHTED + message + bcolors.ENDC)

                elif message_type == "MESSAGE_EXCHANGE":
                    print(bcolors.CYAN + message + bcolors.ENDC)

                elif message_type == "ALERT" or message_type == "LIST_CONTACTS":
                    print(bcolors.YELLOW + message + bcolors.ENDC)

                else:
                    print(message)

            # acknowledge message was received if type of message is MESSAGE_EXCHANGE (client-to-client) 
            if message_type == "MESSAGE_EXCHANGE":
                username = message.split(" ")[3].split(":")[0] # username of the client to send acknowledgement message to
                message = {
                    "username": username, 
                    "text": "Message received by " + currently_logged_user["username"],
                }

                send_acknowledgement_message(message)
                

        except OSError:  # Possibly client has left the chat.
            break

def establish_connection_and_commands():
    """ This function runs on a seperate thread to take user commands and 
        do some operations { login & establishing connections, logout, messaging } 
    """

    while True:
        # take in the command from the user... login, logout, message, contacts
        user_input = raw_input(bcolors.BLINKING + "> " + bcolors.ENDC).split(" ")

        command = user_input[0]

        if command == "login":

            # check if user not logged in already
            if currently_logged_user["username"] != "":
                print("alread logged in... as " + currently_logged_user["username"])
                continue

            username = raw_input("enter username: ")

            # check if username is not already in use

            user = auth.findUser(username)

            if user["success"]:
                
                # try user password until user loggs in
                while len(currently_logged_user["username"]) == 0:

                    # compare password
                    password = raw_input("enter password: ")

                    if auth.password_equal(password, user["password"]):

                        # found user, proceed with login
                        userCredentials = {"username": username, "password": auth.hash_password(password)}

                        print("loging in....")
                        time.sleep(1)
                        login_and_connect_client(userCredentials)
                        
                        # store user locally
                        currently_logged_user["username"] = username 
                        currently_logged_user["password"] = auth.hash_password(password) 
                        break
                    else:
                        print("Wrong password!")
            
            # user not found 
            else:
                print("User record doesn't exist")
                answer = raw_input("sign up ? Y/N... ")
                
                if answer in ["Y", "Yes", "y", "yes"]:
                    password = raw_input("enter password: ")

                    print("signing up...")
                    time.sleep(1)

                    # add user to database
                    auth.addUser(username, password)

                    userCredentials = {"username": username, "password": auth.hash_password(password)}

                    print("loging in....")
                    time.sleep(1)
                    login_and_connect_client(userCredentials)
                    
                    # store user locally
                    currently_logged_user["username"] = username 
                    currently_logged_user["password"] = auth.hash_password(password)

                else:
                    print("quiting....")
                    break
                # user not found, automitaclly register on database and login

        elif command == "quit":
            print("quitting...")
            time.sleep(1)

            currently_logged_user["username"] = "" 
            currently_logged_user["password"] = "" 
            logout_and_disconnect_client() 
            break
        
        elif command in ["message", "contacts", "logout", "message*"]: # commands reserved for logged in users

            # error if user enters commands valid for logged in user if they are not logged in
            if currently_logged_user["username"] == "":
                print(bcolors.RED + "not authenticated" + bcolors.ENDC)

            else:
                if command == "logout":
                    print("logging out...")
                    time.sleep(1)

                    currently_logged_user["username"] = "" 
                    currently_logged_user["password"] = "" 
                    logout_and_disconnect_client() 

                elif command == "message":
                    receiver_username = user_input[1]
                    text = " ".join(user_input[2:])
                    
                    if receiver_username == currently_logged_user["username"]:
                        print("messages to oneself not allowed!")
                    else:
                        message = {
                            "sender_username": currently_logged_user["username"],
                            "receiver_username": receiver_username,
                            "text": text
                        }
                        message_to_online_user(message)    
                    
                elif command == "message*":
                    text = " ".join(user_input[1:])
                
                    message = {
                    "sender_username": currently_logged_user["username"],
                    "receiver_username": "",
                    "text": text
                    }
                    message_to_all_users(message)

                elif command == "contacts":
                    show_connected_clients()
                    time.sleep(1)

                else:
                    print("valid commands: {} | {} | {} | {}".format(bcolors.YELLOW + "message" + bcolors.ENDC, bcolors.YELLOW + "message*" + bcolors.ENDC, bcolors.CYAN + "contacts" + bcolors.ENDC, bcolors.BLUE + "logout" + bcolors.ENDC, bcolors.RED + "quit" + bcolors.ENDC)) 
        else:
            if currently_logged_user["username"] == "":
                print("valid commands: {} | {} ".format(bcolors.GREEN + "login" + bcolors.ENDC, bcolors.RED + "quit" + bcolors.ENDC)) 
            else:
                print("valid commands: {} | {} | {} | {}".format(bcolors.YELLOW + "message" + bcolors.ENDC, bcolors.YELLOW + "message*" + bcolors.ENDC, bcolors.CYAN + "contacts" + bcolors.ENDC, bcolors.BLUE + "logout" + bcolors.ENDC, bcolors.RED + "quit" + bcolors.ENDC)) 
    
    sys.exit()

if __name__ == '__main__':
    Thread(target = receive).start()
    Thread(target = establish_connection_and_commands).start()
