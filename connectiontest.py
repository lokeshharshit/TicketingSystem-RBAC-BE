import pyodbc

server = "ticketingsystemserver.database.windows.net"
database = "ticketingsystemDB"
username = "ssadmin"
password = "Ww@hack,2025"
driver = "{ODBC Driver 17 for SQL Server}"

try:
    # Connect to the database
    conn = pyodbc.connect(f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}")
    cursor = conn.cursor()
    
    # Fetch table names
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = cursor.fetchall()

    # Print table names
    print("✅ Connection Successful! Tables in the database:")
    for table in tables:
        print(f"- {table[0]}")

    # Close the connection
    conn.close()
except Exception as e:
    print(f"❌ Connection Failed: {e}")
