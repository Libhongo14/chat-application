import hashlib
import sqlite3

def hash_password(password):
  """ This function hashes a plain text password"""
  
  h = hashlib.sha256(password.encode())
  hashedPassword = h.hexdigest()
  return hashedPassword

def password_equal(password, hashedPassword):
  """ This function compares two passwords """

  return hash_password(password) == hashedPassword

def create_database():
    """ Creates DB and User table """

    # Connect to sqlite database
    conn = sqlite3.connect('users.db')
    # cursor object
    cursor = conn.cursor()
    # drop query
    cursor.execute("DROP TABLE IF EXISTS USER")
    # create query
    query = """
            CREATE TABLE User (
                Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                Username CHAR(225) NOT NULL, 
                Password CHAR(225) NOT NULL
            ) 
            """
    cursor.execute(query)
    # commit and close
    conn.commit()
    conn.close()

def findUser(username):
    """ searches for a user in DB using username """

    conn = sqlite3.connect('users.db')
    try:
        cursor = conn.execute("SELECT * FROM User WHERE Username='{0}'".format(username))
        userRecord = cursor.fetchall()[0]

        if userRecord:
            return { 
                "success": True,
                "username": userRecord[1],
                "password": userRecord[2]
            } 
        else: 
            return { "success": False }

    except IndexError:
        return { "success": False }

def addUser(username, password):
    """ inserts user into DB """

    conn = sqlite3.connect('users.db')

    # check for already existing username
    if findUser(username)["success"] == False:
        query = ('INSERT INTO User (Username, Password ) '
            'VALUES (:Username, :Password);'
        )
        params = {
                'Username': username,
                'Password': hash_password(password)
        }
        conn.execute(query, params)    
        conn.commit()
        return { "success": True }
    else:
        return { "success": False }
        