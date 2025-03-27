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

# ✅ GET: Fetch Users with RoleId
def handle_get(req, cursor):
    user_id = req.params.get("UserId")
    username = req.params.get("UserName")

    query = """
        SELECT u.UserId, u.UserName, u.Email, ur.RoleId 
        FROM Users u
        LEFT JOIN UserRoles ur ON u.UserId = ur.UserId
    """

    if user_id:
        query += " WHERE u.UserId = ?"
        cursor.execute(query, (user_id,))
    elif username:
        query += " WHERE u.UserName = ?"
        cursor.execute(query, (username,))
    else:
        cursor.execute(query)

    rows = cursor.fetchall()
    users = [{"UserId": row[0], "UserName": row[1], "Email": row[2], "RoleId": row[3]} for row in rows]
    return func.HttpResponse(json.dumps(users), mimetype="application/json", status_code=200)

# ✅ POST: Register or Login User
def handle_post(req, cursor, conn):
    try:
        req_body = req.get_json()
        username = req_body.get("UserName")
        email = req_body.get("Email")
        password_hash = req_body.get("PasswordHash")

        if req_body.get("Login", False):  # 🔹 Handle Login
            cursor.execute("SELECT UserId, UserName, Email, PasswordHash FROM Users WHERE UserName = ?", (username,))
            row = cursor.fetchone()

            if not row:
                return func.HttpResponse(json.dumps({"message": "User Not Found"}), status_code=404)

            stored_password = row[3]
            if stored_password != password_hash:
                return func.HttpResponse(json.dumps({"message": "Invalid Password"}), status_code=401)

            cursor.execute("SELECT RoleId FROM UserRoles WHERE UserId = ?", (row[0],))
            role_row = cursor.fetchone()
            role_id = role_row[0] if role_row else None  

            user_data = {
                "UserId": row[0],
                "UserName": row[1],
                "Email": row[2],
                "RoleId": role_id
            }
            return func.HttpResponse(json.dumps(user_data), status_code=200)

        else:  # 🔹 Handle Registration
            role_id = req_body.get("RoleId")
            if not username or not password_hash or not email or not role_id:
                return func.HttpResponse(json.dumps({"message": "Missing required fields"}), status_code=400)

            cursor.execute("INSERT INTO Users (UserName, Email, PasswordHash) OUTPUT INSERTED.UserId VALUES (?, ?, ?)",
                           (username, email, password_hash))
            user_id = cursor.fetchone()[0]

            cursor.execute("INSERT INTO UserRoles (UserId, RoleId) VALUES (?, ?)", (user_id, role_id))
            conn.commit()
            return func.HttpResponse(json.dumps({"message": f"User {username} created with RoleId {role_id}"}), status_code=201)
    
    except Exception as e:
        logging.error(f"POST Error: {str(e)}")
        return func.HttpResponse(json.dumps({"message": f"Error: {str(e)}"}), status_code=500)

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

        if update_fields:
            update_query = f"UPDATE Users SET {', '.join(update_fields)} WHERE UserId = ?"
            params.append(user_id)
            cursor.execute(update_query, params)

        if "RoleId" in req_body:
            role_id = req_body["RoleId"]
            cursor.execute("SELECT COUNT(*) FROM UserRoles WHERE UserId = ?", (user_id,))
            role_exists = cursor.fetchone()[0] > 0

            if role_exists:
                cursor.execute("UPDATE UserRoles SET RoleId = ? WHERE UserId = ?", (role_id, user_id))
            else:
                cursor.execute("INSERT INTO UserRoles (UserId, RoleId) VALUES (?, ?)", (user_id, role_id))

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
