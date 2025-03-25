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
    user_id = req.params.get("UserId")
    username = req.params.get("UserName")

    if user_id:
        cursor.execute("""
            SELECT u.UserId, u.UserName, u.Email, ur.RoleId 
            FROM Users u
            LEFT JOIN UserRoles ur ON u.UserId = ur.UserId
            WHERE u.UserId = ?
        """, (user_id,))
        rows = cursor.fetchall()
        if rows:
            user_data = [{"UserId": row[0], "UserName": row[1], "Email": row[2], "RoleId": row[3]} for row in rows]
            return func.HttpResponse(json.dumps(user_data), mimetype="application/json", status_code=200)
        return func.HttpResponse(json.dumps({"message": "User not found"}), status_code=404)

    elif username:
        cursor.execute("""
            SELECT u.UserId, u.UserName, u.Email, ur.RoleId 
            FROM Users u
            LEFT JOIN UserRoles ur ON u.UserId = ur.UserId
            WHERE u.UserName = ?
        """, (username,))
        rows = cursor.fetchall()
        if rows:
            user_data = [{"UserId": row[0], "UserName": row[1], "Email": row[2], "RoleId": row[3]} for row in rows]
            return func.HttpResponse(json.dumps(user_data), mimetype="application/json", status_code=200)
        return func.HttpResponse(json.dumps({"message": "User not found"}), status_code=404)

    cursor.execute("""
        SELECT u.UserId, u.UserName, u.Email, ur.RoleId 
        FROM Users u
        LEFT JOIN UserRoles ur ON u.UserId = ur.UserId
    """)
    users = [{"UserId": row[0], "UserName": row[1], "Email": row[2], "RoleId": row[3]} for row in cursor.fetchall()]
    return func.HttpResponse(json.dumps(users), mimetype="application/json", status_code=200)

# ✅ POST: Handle Login & User Registration
def handle_post(req, cursor, conn):
    try:
        req_body = req.get_json()
        username = req_body.get("UserName")
        password_hash = req_body.get("PasswordHash")

        if not username or not password_hash:
            return func.HttpResponse(json.dumps({"message": "Missing Username or Password"}), status_code=400)

        # 🔹 Handle Login (Modified to return RoleId)
        if req_body.get("Login", False):
            cursor.execute("SELECT UserId, UserName, Email, PasswordHash FROM Users WHERE UserName = ?", (username,))
            row = cursor.fetchone()

            if not row:
                return func.HttpResponse(json.dumps({"message": "User Not Found"}), status_code=404)

            stored_password = row[3]
            if stored_password != password_hash:
                return func.HttpResponse(json.dumps({"message": "Invalid Password"}), status_code=401)

            # ✅ Fetch RoleId separately and add to login response
            cursor.execute("SELECT RoleId FROM UserRoles WHERE UserId = ?", (row[0],))
            role_row = cursor.fetchone()
            role_id = role_row[0] if role_row else None  

            user_data = {
                "UserId": row[0],
                "UserName": row[1],
                "Email": row[2],
                "RoleId": role_id  # ✅ RoleId is now included in the response
            }

            return func.HttpResponse(json.dumps(user_data), mimetype="application/json", status_code=200)

        # 🔹 Handle User Registration (Original logic unchanged)
        email = req_body.get("Email")
        if not email:
            return func.HttpResponse(json.dumps({"message": "Email is required for registration"}), status_code=400)

        cursor.execute("INSERT INTO Users (UserName, Email, PasswordHash) VALUES (?, ?, ?)", 
                       (username, email, password_hash))
        conn.commit()
        return func.HttpResponse(json.dumps({"message": f"User {username} created"}), status_code=201)

    except Exception as e:
        return func.HttpResponse(json.dumps({"message": f"Error: {str(e)}"}), status_code=500)

# ✅ PUT: Update User Details
def handle_put(req, cursor, conn):
    try:
        req_body = req.get_json()
        user_id = req_body.get("UserId")

        if not user_id:
            return func.HttpResponse(json.dumps({"message": "Missing UserId"}), status_code=400)

        update_fields = []
        params = []

        if "UserName" in req_body:
            update_fields.append("UserName = ?")
            params.append(req_body["UserName"])

        if "Email" in req_body:
            update_fields.append("Email = ?")
            params.append(req_body["Email"])

        if "PasswordHash" in req_body:
            update_fields.append("PasswordHash = ?")
            params.append(req_body["PasswordHash"])

        if not update_fields:
            return func.HttpResponse(json.dumps({"message": "No valid fields provided for update"}), status_code=400)

        update_query = f"UPDATE Users SET {', '.join(update_fields)} WHERE UserId = ?"
        params.append(user_id)

        cursor.execute(update_query, params)
        conn.commit()
        return func.HttpResponse(json.dumps({"message": f"User {user_id} updated successfully"}), status_code=200)

    except Exception as e:
        return func.HttpResponse(json.dumps({"message": f"Error: {str(e)}"}), status_code=500)

# ✅ DELETE: Remove a User
def handle_delete(req, cursor, conn):
    try:
        req_body = req.get_json()
        user_id = req_body.get("UserId")

        if not user_id:
            return func.HttpResponse(json.dumps({"message": "Missing UserId"}), status_code=400)

        cursor.execute("DELETE FROM Users WHERE UserId = ?", (user_id,))
        conn.commit()
        return func.HttpResponse(json.dumps({"message": f"User {user_id} deleted"}), status_code=200)

    except Exception as e:
        return func.HttpResponse(json.dumps({"message": f"Error: {str(e)}"}), status_code=500)
