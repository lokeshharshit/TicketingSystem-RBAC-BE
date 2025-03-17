import logging
import azure.functions as func
import pyodbc
import json

# 🔹 Azure SQL Database Connection Details
server = "ticketingsystemserver.database.windows.net"
database = "ticketingsystemDB"
username = "ssadmin"
password = "Ww@hack,2025"
driver = "{ODBC Driver 17 for SQL Server}"

# ✅ Function to Get Database Connection
def get_db_connection():
    conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    return pyodbc.connect(conn_str)

# ✅ Main Azure Function Entry Point
def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        method = req.method  # GET, POST, PUT, DELETE

        if method == "GET":
            return handle_get(req, cursor)
        elif method == "POST":
            return handle_post(req, cursor, conn)
        elif method == "PUT":
            return handle_put(req, cursor, conn)
        elif method == "DELETE":
            return handle_delete(req, cursor, conn)
        else:
            return func.HttpResponse("Method Not Allowed", status_code=405)

    except Exception as e:
        logging.error(str(e))
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)


# ✅ GET: Fetch All Users, User by ID, or User by Username
def handle_get(req, cursor):
    user_id = req.params.get("UserId")  # Query parameter for UserId
    username = req.params.get("UserName")  # Query parameter for UserName

    if user_id:  # Fetch user by UserId
        cursor.execute("SELECT UserId, UserName, Email FROM Users WHERE UserId = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            user = {"UserId": row[0], "UserName": row[1], "Email": row[2]}
            return func.HttpResponse(json.dumps(user), mimetype="application/json", status_code=200)
        else:
            return func.HttpResponse("User not found", status_code=404)

    elif username:  # Fetch user by UserName
        cursor.execute("SELECT UserId, UserName, Email FROM Users WHERE UserName = ?", (username,))
        row = cursor.fetchone()
        if row:
            user = {"UserId": row[0], "UserName": row[1], "Email": row[2]}
            return func.HttpResponse(json.dumps(user), mimetype="application/json", status_code=200)
        else:
            return func.HttpResponse("User not found", status_code=404)

    else:  # Fetch all users if no specific query is provided
        cursor.execute("SELECT UserId, UserName, Email FROM Users")
        rows = cursor.fetchall()
        users = [{"UserId": row[0], "UserName": row[1], "Email": row[2]} for row in rows]
        return func.HttpResponse(json.dumps(users), mimetype="application/json", status_code=200)


# ✅ POST: Handle Login Validation and User Creation
def handle_post(req, cursor, conn):
    try:
        req_body = req.get_json()
        username = req_body.get("UserName")
        password_hash = req_body.get("PasswordHash")  # Pre-encrypted password

        if not username or not password_hash:
            return func.HttpResponse("Missing Username or Password", status_code=400)

        # 🔹 Check if it's a Login Request
        if req_body.get("Login", False):
            cursor.execute("SELECT UserId, UserName, Email, PasswordHash FROM Users WHERE UserName = ?", (username,))
            row = cursor.fetchone()
            if row:
                stored_password = row[3]
                if stored_password == password_hash:  # Basic password comparison
                    user = {"UserId": row[0], "UserName": row[1], "Email": row[2]}
                    return func.HttpResponse(json.dumps(user), mimetype="application/json", status_code=200)
                else:
                    return func.HttpResponse("Invalid password", status_code=401)
            else:
                return func.HttpResponse("User not found", status_code=404)

        # 🔹 If not login, create a new user
        email = req_body.get("Email")
        if not email:
            return func.HttpResponse("Email is required for registration", status_code=400)

        cursor.execute("INSERT INTO Users (UserName, Email, PasswordHash) VALUES (?, ?, ?)", 
                       (username, email, password_hash))
        conn.commit()
        return func.HttpResponse(f"User {username} created", status_code=201)

    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)


# ✅ PUT: Update User Email
def handle_put(req, cursor, conn):
    try:
        req_body = req.get_json()
        user_id = req_body.get("UserId")
        email = req_body.get("Email")

        if not user_id or not email:
            return func.HttpResponse("Missing fields", status_code=400)

        cursor.execute("UPDATE Users SET Email = ? WHERE UserId = ?", (email, user_id))
        conn.commit()
        return func.HttpResponse(f"User {user_id} email updated", status_code=200)

    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)


# ✅ DELETE: Remove a User
def handle_delete(req, cursor, conn):
    try:
        req_body = req.get_json()
        user_id = req_body.get("UserId")

        if not user_id:
            return func.HttpResponse("Missing UserId", status_code=400)

        cursor.execute("DELETE FROM Users WHERE UserId = ?", (user_id,))
        conn.commit()
        return func.HttpResponse(f"User {user_id} deleted", status_code=200)

    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
