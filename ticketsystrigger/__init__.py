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

# PUT: Update Ticket (Various Cases)
def handle_put(req, cursor, conn):
    try:
        req_body = req.get_json()
        ticket_id = req_body.get("TicketId")  # TicketId (cannot be updated)
        user_id = req_body.get("UserId")  # UserId (cannot be updated)
        admin_id = req_body.get("AdminId")  # AdminId
        description = req_body.get("Description")  # Description
        comments = req_body.get("Comments")  # Comments
        status = req_body.get("Status")  # Status
        attachment = req_body.get("Attachment")  # Attachment

        # Ensure TicketId is provided
        if not ticket_id:
            return func.HttpResponse("Missing required field: TicketId", status_code=400)

        # Ensure UserId is not included (as it cannot be updated)
        if user_id:
            return func.HttpResponse("UserId cannot be updated", status_code=400)

        # Case 1: Update only AdminId
        if admin_id and not (description or comments or status or attachment):
            cursor.execute("UPDATE Tickets SET AdminId = ? WHERE TicketId = ?", (admin_id, ticket_id))
            conn.commit()
            return func.HttpResponse("AdminId updated successfully", status_code=200)

        # Case 2: Update only Description
        elif description and not (admin_id or comments or status or attachment):
            cursor.execute("UPDATE Tickets SET Description = ? WHERE TicketId = ?", (description, ticket_id))
            conn.commit()
            return func.HttpResponse("Description updated successfully", status_code=200)

        # Case 3: Update only Comments
        elif comments and not (admin_id or description or status or attachment):
            cursor.execute("UPDATE Tickets SET Comments = ? WHERE TicketId = ?", (comments, ticket_id))
            conn.commit()
            return func.HttpResponse("Comments updated successfully", status_code=200)

        # Case 4: Update both Comments and Description
        elif comments and description and not (admin_id or status or attachment):
            cursor.execute("UPDATE Tickets SET Description = ?, Comments = ? WHERE TicketId = ?", (description, comments, ticket_id))
            conn.commit()
            return func.HttpResponse("Description and Comments updated successfully", status_code=200)

        # Case 5: Update Status only
        elif status and not (admin_id or description or comments or attachment):
            cursor.execute("UPDATE Tickets SET Status = ? WHERE TicketId = ?", (status, ticket_id))
            conn.commit()
            return func.HttpResponse("Status updated successfully", status_code=200)

        # Case 6: Update Attachment only
        elif attachment and not (admin_id or description or comments or status):
            cursor.execute("UPDATE Tickets SET Attachment = ? WHERE TicketId = ?", (attachment, ticket_id))
            conn.commit()
            return func.HttpResponse("Attachment updated successfully", status_code=200)

        # Case 7: Update all except TicketId and UserId
        elif admin_id or description or comments or status or attachment:
            cursor.execute("""
                UPDATE Tickets
                SET AdminId = ?, Description = ?, Comments = ?, Status = ?, Attachment = ?
                WHERE TicketId = ?
            """, (admin_id, description, comments, status, attachment, ticket_id))
            conn.commit()
            return func.HttpResponse("Ticket updated successfully", status_code=200)

        else:
            return func.HttpResponse("No valid fields to update", status_code=400)

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
