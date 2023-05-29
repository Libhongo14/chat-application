import json
import ast
import hashlib
from socket import *
from auth import create_database

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)          #Assigns an IP address and a port number to a socket instance
serverSocket.bind(('', serverPort))

# set up database
create_database()

print("The server is ready to connect ....")

clients = []    # to store all online clients
    
def serve_and_listen():
    
    while True:
        message, clientSenderAddress = serverSocket.recvfrom(2048)        # 2048 defines the number of bytes in message
        
        dictMessage = ast.literal_eval(str(message.decode()))[0] # decode message from clients and transform into dictionary
        clientMessageHashValue = ast.literal_eval(str(message.decode()))[1] # get the message hash value to compare for validation

        # conversion to tuples
        tups = list(dictMessage["header"].items())
        dictMessage["header"] = dict(tups)

        # hash received message
        h = hashlib.sha256(str(dictMessage))
        messageHashValue = h.hexdigest()

        # verify that messages are correctly received if not send error message
        if str(clientMessageHashValue) != str(messageHashValue):
            # send error message for incorrect message
            message_struct = {
                "header": {
                    "command": "",
                    "message_type": "ERROR",
                    "recipient_data": clientSenderAddress,
                },
                "body": "Incorrect message format!",
            }
            toBeSentMessage = str(message_struct).encode()
            serverSocket.sendto(toBeSentMessage, clientSenderAddress)
            continue

        command = dictMessage["header"]["command"] 
        message_type = dictMessage["header"]["message_type"]

        if command == "LOGIN": 
            """ mimic handshaking protocol connection 
                login user and store user credentials together with client address 
            """      
            user = dictMessage["body"]  
            username = user["username"] 
            password = user["password"] 

            # store user in user-dictionary
            clients.append({ "username": username, "password": password, "address": clientSenderAddress}) # store client data..Appends dictionary into a ist
            
            message_struct = {
                "header": {
                    "command": "",
                    "message_type": "GREETING",
                    "recipient_data": clientSenderAddress,
                },
                "body": "Greetings from the Chat Room!",
            }

            toBeSentMessage = str(message_struct).encode()
            serverSocket.sendto(toBeSentMessage, clientSenderAddress)

            # find all users to send online message (xxxxx user is online!)
            for client in clients:
                address = client["address"] 
                message_struct = {
                    "header": {
                        "command": "", 
                        "message_type": "ALERT",
                        "recipient_data": address,
                    },
                    "body": "{0} {1}".format(username, "is online!")
                }

                # send message to all users except the user (this user) that just joined the chat
                if clientSenderAddress != address:
                    toBeSentMessage = str(message_struct).encode()
                    serverSocket.sendto(toBeSentMessage, address)

        # functionality for logging out a user
        elif command == "LOGOUT":
            for client in clients:
                if clientSenderAddress == client["address"]:
                    clients.remove(client)

        # functionality for sending a message to a user
        elif (command == "SEND_MESSAGE"):
            message_info = dictMessage["body"]
            sender_username = message_info["sender_username"]
            receiver_username = message_info["receiver_username"]
            text_to_be_sent = message_info["text"]
            
            # find user who is supposed to receive message
            for client in clients:
                if receiver_username == client["username"]:
                    address = client["address"] 
                    message_struct = {
                            "header": {
                                "command": "",
                                "message_type": "MESSAGE_EXCHANGE",
                                "recipient_data": address,
                                "sender_data":  clientSenderAddress,
                        },
                        "body": "Private message from " + str(sender_username) + ": " + str(text_to_be_sent)
                    }

                    toBeSentMessage = str(message_struct).encode()
                    serverSocket.sendto(toBeSentMessage, address)  # send welcome message to all other clients except the current client
                    
        elif (command == "SEND_ALL_MESSAGE"):
            message_info = dictMessage["body"]
            sender_username = message_info["sender_username"]
            #receiver_username = message_info["receiver_username"]
            text_to_be_sent = message_info["text"]
            
            # find all users who are supposed to receive the message
            for client in clients:
                address = client["address"] 

                if address != clientSenderAddress:
                    message_struct = {
                        "header": {
                            "command": "",
                            "message_type": "MESSAGE_EXCHANGE",
                            "recipient_data": address,
                            "sender_data":  clientSenderAddress,
                        },
                        "body": "Group Message from " + str(sender_username) + ": " + str(text_to_be_sent)
                    }   

                    toBeSentMessage = str(message_struct).encode()
                    serverSocket.sendto(toBeSentMessage, address)  # send welcome message to all other
                    
        # functionality for listing all online users
        elif command == "CONTACTS":
            for current_client in clients:
                if current_client["address"] != clientSenderAddress:
                    message_struct = {
                        "header": {
                            "command": "",
                            "message_type": "LIST_CONTACTS",
                        },
                        "body": "{0} : {1} {2}".format(current_client["username"], current_client["address"], "is online!")
                    }

                    toBeSentMessage = str(message_struct).encode()
                    serverSocket.sendto(toBeSentMessage, clientSenderAddress) 

        # functionality for sending acknowledgement messages between users 
        elif command == "" and message_type == "ACKNOWLEDGEMENT":
            username = dictMessage["body"]["username"]
            text = dictMessage["body"]["text"]

            for client in clients:
                if client["username"] == username:
                    message_struct = {
                        "header": {
                            "command": "",
                            "message_type": "ACKNOWLEDGEMENT",
                        },
                        "body": text
                    }

                    toBeSentMessage = str(message_struct).encode()
                    serverSocket.sendto(toBeSentMessage, client["address"])  # send message to all other clients except the current client

if __name__ == '__main__':
    serve_and_listen()
