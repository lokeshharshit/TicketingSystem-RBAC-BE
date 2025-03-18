import logging
import azure.functions as func
import pyodbc
import json

# Azure SQL Database Connection Details
server = "ticketingsystemserver.database.windows.net"
database = "ticketingsystemDB"
username = "ssadmin"
password = "Ww@hack,2025"
driver = "{ODBC Driver 17 for SQL Server}"

# Function to Get Database Connection
def get_db_connection():
    conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    return pyodbc.connect(conn_str)

# Main Azure Function Entry Point
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

# GET: Fetch All UserRoles or By UserId
def handle_get(req, cursor):
    user_id = req.params.get("UserId")

    if user_id:
        cursor.execute("SELECT UserId, RoleId FROM UserRoles WHERE UserId = ?", (user_id,))
    else:
        cursor.execute("SELECT UserId, RoleId FROM UserRoles")

    rows = cursor.fetchall()
    roles = [{"UserId": row[0], "RoleId": row[1]} for row in rows]

    return func.HttpResponse(json.dumps(roles), mimetype="application/json", status_code=200)

# POST: Assign a New Role to a User
def handle_post(req, cursor, conn):
    try:
        req_body = req.get_json()
        user_id = req_body.get("UserId")
        role_id = req_body.get("RoleId")

        if not user_id or not role_id:
            return func.HttpResponse("Missing required fields", status_code=400)

        cursor.execute("INSERT INTO UserRoles (UserId, RoleId) VALUES (?, ?)", (user_id, role_id))
        conn.commit()
        return func.HttpResponse("Role assigned successfully", status_code=201)
    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

# PUT: Update an Existing Role for a User
def handle_put(req, cursor, conn):
    try:
        req_body = req.get_json()
        user_id = req_body.get("UserId")
        new_role_id = req_body.get("RoleId")  # Just the new role

        if not user_id or not new_role_id:
            return func.HttpResponse("Missing required fields", status_code=400)

        # Check if user exists in UserRoles
        cursor.execute("SELECT COUNT(*) FROM UserRoles WHERE UserId = ?", (user_id,))
        user_exists = cursor.fetchone()[0]

        if user_exists == 0:
            return func.HttpResponse("User has no existing roles to update", status_code=404)

        # Update the role for the given user
        cursor.execute("""
            UPDATE UserRoles 
            SET RoleId = ? 
            WHERE UserId = ?
        """, (new_role_id, user_id))

        conn.commit()
        return func.HttpResponse("User role updated successfully", status_code=200)

    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

# DELETE: Remove a Role from a User
def handle_delete(req, cursor, conn):
    try:
        req_body = req.get_json()
        user_id = req_body.get("UserId")
        role_id = req_body.get("RoleId")

        if not user_id or not role_id:
            return func.HttpResponse("Missing required fields", status_code=400)

        cursor.execute("DELETE FROM UserRoles WHERE UserId = ? AND RoleId = ?", (user_id, role_id))
        conn.commit()
        return func.HttpResponse("Role removed successfully", status_code=200)
    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
