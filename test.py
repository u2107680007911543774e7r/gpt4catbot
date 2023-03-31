from pymongo import MongoClient
import certifi
from pymongo import MongoClient
import os

# Set the SSL_CERT_FILE environment variable to point to the downloaded CA certificates file
os.environ['SSL_CERT_FILE'] = 'cacert.pem'


# Replace the following variables with your actual MongoDB Atlas serverless credentials
mongo_user = 'u2107680007911543774e7r'
mongo_pass = 'evOCiYG3bpip5TB1'
cluster_url = 'serverlessinstance0.bnnnc12.mongodb.net'

# Create a connection string
connection_string = f"mongodb+srv://{mongo_user}:{mongo_pass}@{cluster_url}/gpt4catbot?retryWrites=true&w=majority"

# Connect to the MongoDB Atlas serverless instance using SSL and the CA certificate bundle provided by certifi
client = MongoClient(connection_string)

# Replace 'your_database_name' with the name of your database
db = client["gpt4catbot"]

# Replace 'your_collection_name' with the name of your collection
collection = db["messages"]


# Define function to handle messages
def save_context():
    collection.insert_one({"user": "user"})
    print(collection.find())


if __name__ == '__main__':
    save_context()
