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

# GET: Fetch All Roles or Specific Role by RoleId
def handle_get(req, cursor):
    role_id = req.params.get("RoleId")
    
    if role_id:
        cursor.execute("SELECT RoleId, RoleName FROM Roles WHERE RoleId = ?", (role_id,))
        row = cursor.fetchone()
        if row:
            role = {"RoleId": row[0], "RoleName": row[1]}
            return func.HttpResponse(json.dumps(role), mimetype="application/json", status_code=200)
        else:
            return func.HttpResponse("Role not found", status_code=404)
    
    cursor.execute("SELECT RoleId, RoleName FROM Roles")
    rows = cursor.fetchall()
    roles = [{"RoleId": row[0], "RoleName": row[1]} for row in rows]
    return func.HttpResponse(json.dumps(roles), mimetype="application/json", status_code=200)

# POST: Create a New Role
def handle_post(req, cursor, conn):
    try:
        req_body = req.get_json()
        role_name = req_body.get("RoleName")

        if not role_name:
            return func.HttpResponse("Missing required field: RoleName", status_code=400)

        cursor.execute("INSERT INTO Roles (RoleName) VALUES (?)", (role_name,))
        conn.commit()
        return func.HttpResponse("Role created successfully", status_code=201)
    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

# PUT: Update Role Name by RoleId
def handle_put(req, cursor, conn):
    try:
        req_body = req.get_json()
        role_id = req_body.get("RoleId")
        role_name = req_body.get("RoleName")

        if not role_id or not role_name:
            return func.HttpResponse("Missing required fields", status_code=400)

        cursor.execute("UPDATE Roles SET RoleName = ? WHERE RoleId = ?", (role_name, role_id))
        conn.commit()
        return func.HttpResponse("Role updated successfully", status_code=200)
    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

# DELETE: Remove a Role by RoleId
def handle_delete(req, cursor, conn):
    try:
        req_body = req.get_json()
        role_id = req_body.get("RoleId")

        if not role_id:
            return func.HttpResponse("Missing RoleId", status_code=400)

        cursor.execute("DELETE FROM Roles WHERE RoleId = ?", (role_id,))
        conn.commit()
        return func.HttpResponse("Role deleted successfully", status_code=200)
    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
