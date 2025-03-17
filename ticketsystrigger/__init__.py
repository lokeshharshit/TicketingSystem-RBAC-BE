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

# GET: Fetch Tickets by TicketId or UserId
def handle_get(req, cursor):
    ticket_id = req.params.get("TicketId")
    user_id = req.params.get("UserId")

    if ticket_id:
        cursor.execute("SELECT * FROM Tickets WHERE TicketId = ?", (ticket_id,))
        row = cursor.fetchone()
        if row:
            ticket = {"TicketId": row[0], "UserId": row[1], "AdminId": row[2], "Description": row[3], "Status": row[4], "Attachment": row[5], "Comments": row[6]}
            return func.HttpResponse(json.dumps(ticket), mimetype="application/json", status_code=200)
        else:
            return func.HttpResponse("Ticket not found", status_code=404)

    elif user_id:
        cursor.execute("SELECT * FROM Tickets WHERE UserId = ?", (user_id,))
        rows = cursor.fetchall()
        tickets = [{"TicketId": row[0], "UserId": row[1], "AdminId": row[2], "Description": row[3], "Status": row[4], "Attachment": row[5], "Comments": row[6]} for row in rows]
        return func.HttpResponse(json.dumps(tickets), mimetype="application/json", status_code=200)
    
    else:
        cursor.execute("SELECT * FROM Tickets")
        rows = cursor.fetchall()
        tickets = [{"TicketId": row[0], "UserId": row[1], "AdminId": row[2], "Description": row[3], "Status": row[4], "Attachment": row[5], "Comments": row[6]} for row in rows]
        return func.HttpResponse(json.dumps(tickets), mimetype="application/json", status_code=200)

# POST: Create a New Ticket
def handle_post(req, cursor, conn):
    try:
        req_body = req.get_json()
        user_id = req_body.get("UserId")
        admin_id = req_body.get("AdminId")
        description = req_body.get("Description", "")
        status = req_body.get("Status")
        attachment = req_body.get("Attachment", "")
        comments = req_body.get("Comments", "")

        if not user_id or not admin_id or not status:
            return func.HttpResponse("Missing required fields", status_code=400)

        cursor.execute("INSERT INTO Tickets (UserId, AdminId, Description, Status, Attachment, Comments) VALUES (?, ?, ?, ?, ?, ?)", 
                       (user_id, admin_id, description, status, attachment, comments))
        conn.commit()
        return func.HttpResponse("Ticket created successfully", status_code=201)
    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

# PUT: Update Ticket Status and Comments
def handle_put(req, cursor, conn):
    try:
        req_body = req.get_json()
        ticket_id = req_body.get("TicketId")
        status = req_body.get("Status")
        comments = req_body.get("Comments", "")

        if not ticket_id or not status:
            return func.HttpResponse("Missing required fields", status_code=400)

        cursor.execute("UPDATE Tickets SET Status = ?, Comments = ? WHERE TicketId = ?", (status, comments, ticket_id))
        conn.commit()
        return func.HttpResponse("Ticket updated successfully", status_code=200)
    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

# DELETE: Remove a Ticket
def handle_delete(req, cursor, conn):
    try:
        req_body = req.get_json()
        ticket_id = req_body.get("TicketId")

        if not ticket_id:
            return func.HttpResponse("Missing TicketId", status_code=400)

        cursor.execute("DELETE FROM Tickets WHERE TicketId = ?", (ticket_id,))
        conn.commit()
        return func.HttpResponse("Ticket deleted successfully", status_code=200)
    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
