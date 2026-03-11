import re
from fastapi.exceptions import HTTPException
from pymongo.synchronous.collection import Collection
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from ..models.account import Account
from .audit_log import log_action
from datetime import timezone
from datetime import datetime
from zoneinfo import ZoneInfo
from src.controllers import auth,mail
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=5)
IST = ZoneInfo("Asia/Kolkata")

def insert_notes(user_id, user_role, note, parent_id, db, module_name, pg_db: Session):
    try:
        user_coll = db["users"]
        notes_coll = db["Notes"]
        Owner = user_coll.find_one(
            {"id": str(user_id)}, {"_id": 0, "id": 1, "first_name": 1, "email": 1}
        )
        raw_parent_acc = (
            pg_db.query(
                Account.id.label("id"), Account.account_name.label("account_name")
            )
            .filter(Account.id == int(parent_id))
            .one()
        )
        Parent_Id = {
            "id": str(raw_parent_acc.id),
            "account_name": raw_parent_acc.account_name,
        }
        Modified_By = None
        Created_By = user_coll.find_one(
            {"id": str(user_id)}, {"_id": 0, "id": 1, "first_name": 1, "email": 1}
        )
        if Created_By and "first_name" in Created_By:
            Created_By["name"] = Created_By.pop("first_name")

        result = notes_coll.insert_one({
            "Owner": Owner,
            "Created_By": Created_By,
            "Modified_By": Modified_By,
            "Note_Content": note,
            "Parent_Id": Parent_Id,
            "module":module_name,
            "Created_Time": datetime.now(timezone.utc).isoformat(),
            "Modified_Time": datetime.now(timezone.utc).isoformat(),
        })
        print("Insertion result",result)

        log_action(
            pg_db,
            user_id,
            user_role,
            "CREATED",
            "Note",
            int(parent_id),
            {"note": note, "parent_id": parent_id},
        )
        #create a background worker to send mention emails in a separate eventloop
        executor.submit(
            mentions,
            note,
            module_name,
            parent_id,
            user_coll
        )

        return JSONResponse(
            status_code=201, content={"message": "Note saved successfully"}
        )
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"error": str(e)})


def get_notes(id_list: list, notes_collection: Collection):
    try:
        notes_cursor = notes_collection.find(
            {"Parent_Id.id": {"$in":id_list}},
            {
                "_id": 0,
                "Owner": 1,
                "Note_Content": 1,
                "Parent_Id": 1,
                "Modified_By": 1,
                "Created_By": 1,
                "Created_Time": 1,
                "Modified_Time": 1,
                "module": 1,
            },
        )

        notes = []
        for note in notes_cursor:
            if note.get("Created_Time"):
                created = datetime.fromisoformat(note["Created_Time"]).replace(tzinfo=timezone.utc).astimezone(IST)
                note["Created_Time"] = created.strftime("%d %b %Y, %I:%M %p")

            if note.get("Modified_Time"):
                modified = datetime.fromisoformat(note["Modified_Time"]).replace(tzinfo=timezone.utc).astimezone(IST)
                note["Modified_Time"] = modified.strftime("%d %b %Y, %I:%M %p")
            note["Note_Content"] = map_user_name_with_id(note["Note_Content"])
            notes.append(note)
        return notes

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error"},
        )

def map_user_name_with_id(note_text:str)->str:
    pattern = r"zsu\[@user:(\d+)\]zsu|crm\[user#(\d+)#(\d+)\]crm"
    def replace(match):
        user_id = match.group(1) if match.group(1) else match.group(2)

        if not user_id:
            return match.group(0)

        user_id = int(user_id)

        return "@" + auth.users.get(user_id, str(user_id))
    return re.sub(pattern, replace, note_text)



def is_note_has_comment(note_text: str) -> bool:
    pattern = re.compile(r"crm\[user#(\d+)\]crm")
    return bool(pattern.search(note_text))


def mentions(note,module_name,parent_id,user_coll):
    try:#check if the note_content have mentions in them
        is_note_there = is_note_has_comment(note)
        print("is_note_there",is_note_there)
        if is_note_there: #mention is there in the comment
            pattern = re.compile(r"crm\[user#(\d+)\]crm")
            user_ids = pattern.findall(note)
            users = user_coll.find(
                {"id": {"$in": list(user_ids)}},
                {"id": 1, "full_name": 1, "email": 1, "_id": 0}
            )
            email_list = []  # holds the list of emails_id of user with the msg
            for user in users:
                email_list.append({
                    "user_name": user["full_name"],
                    "user_email_address": user["email"],
                    "module": module_name,
                    "entity_id": parent_id,
                    "note": map_user_name_with_id(note)
                })
            print(email_list)
            #after collection all the emails of the user time to prepare the body and send the email
            mail.process_mention_emails(email_list)
            print("All emails sent successfully")
            return None
    except Exception as e:
        print(e)
        return None