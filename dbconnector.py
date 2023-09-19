import psycopg2

# Replace the placeholders with your actual values
DB_HOST = "localhost"  # If using a remote container, replace with the container IP/hostname
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "test1337scrap"  # Replace with the password you specified during container creation

try:
    # Establish the connection
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    # Create a cursor to execute queries
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS maxima "
                   "(id INT, "
                   "name VARCHAR(255), "
                   "discount INT, "
                   "old_price BIGINT, "
                   "new_price BIGINT);")
    # Create the sequence
    cursor.execute("CREATE SEQUENCE IF NOT EXISTS maxima_id_seq;")

    # Link the sequence to the table's primary key column
    cursor.execute("ALTER TABLE maxima ALTER COLUMN id SET DEFAULT nextval('maxima_id_seq');")

    # Commit the transaction to make the changes permanent
    conn.commit()

    # Now you can execute SQL queries with cursor.execute() and fetch results
    cursor.execute("SELECT * FROM maxima;")
    result = cursor.fetchall()

    # Do something with the result
    print(result)

    # Don't forget to close the cursor and connection when you're done
    cursor.close()
    conn.close()

except psycopg2.Error as e:
    print("Error connecting to PostgreSQL:", e)