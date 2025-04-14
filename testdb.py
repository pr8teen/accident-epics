import psycopg2

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="AccidentDB", 
    user="postgres", 
    password="dadmom2004", 
    host="localhost", 
    port="5432"
)

# Create a cursor to execute SQL queries
cursor = conn.cursor()
print("Connected to PostgreSQL Database")