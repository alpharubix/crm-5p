import re
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from pymongo.synchronous.collection import Collection
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from src.controllers import auth, mail
from src.controllers.Background_threads import BackgroundThreadPool
from src.database import SessionLocal
from src.models.account import Account
from src.models.contact import Contact
from src.models.deal import Deal
from src.models.ticket import Ticket
from src.models.user import User

from .audit_log import log_action

IST = ZoneInfo("Asia/Kolkata")


def insert_notes(user_id, user_role, note, parent_id, db, module_name, pg_db: Session, notes_parent_id: str | None = None):
    try:
        notes_coll = db["Notes"]

        # Multi-strategy User / Owner lookup
        owner_name = None
        owner_email = None
        owner_id_str = str(user_id) if user_id is not None else "unknown"

        # 1. Try PostgreSQL DB (User model)
        if pg_db and user_id is not None:
            try:
                user_id_int = int(user_id) if str(user_id).isdigit() else None
                pg_user = None
                if user_id_int is not None:
                    pg_user = pg_db.query(User).filter(User.id == user_id_int).first()
                if not pg_user:
                    pg_user = pg_db.query(User).filter(User.zuid == str(user_id)).first()
                if pg_user:
                    owner_name = pg_user.full_name
                    owner_email = pg_user.email
                    owner_id_str = str(pg_user.id)
            except Exception as e:
                print(f"Error querying Postgres User in insert_notes: {e}")

        # 2. Try MongoDB users collection
        if not owner_name:
            try:
                user_coll = db["users"]
                mongo_user = (
                    user_coll.find_one({"id": str(user_id)})
                    or user_coll.find_one({"id": int(user_id) if str(user_id).isdigit() else user_id})
                    or user_coll.find_one({"zuid": str(user_id)})
                )
                if mongo_user:
                    owner_name = (
                        mongo_user.get("first_name")
                        or mongo_user.get("name")
                        or mongo_user.get("full_name")
                    )
                    owner_email = mongo_user.get("email") or owner_email
                    owner_id_str = str(mongo_user.get("id") or user_id)
            except Exception as e:
                print(f"Error querying MongoDB users in insert_notes: {e}")

        # 3. Try auth.users dictionary
        if not owner_name:
            try:
                user_id_int = int(user_id) if str(user_id).isdigit() else None
                if user_id_int and user_id_int in auth.users:
                    owner_name = auth.users[user_id_int]
                elif str(user_id) in auth.users:
                    owner_name = auth.users[str(user_id)]
            except Exception:
                pass

        # 4. Fallback based on user_role or generic default
        if not owner_name:
            if user_role:
                owner_name = str(user_role).replace(".", " ").replace("_", " ").title()
            else:
                owner_name = f"User #{user_id}"

        Owner = {
            "id": owner_id_str,
            "first_name": owner_name,
            "name": owner_name,
            "full_name": owner_name,
            "email": owner_email or "",
        }

        Created_By = {
            "id": owner_id_str,
            "name": owner_name,
            "first_name": owner_name,
            "email": owner_email or "",
        }
        Modified_By = None

        # Handle parent ID resolution for modules
        if module_name in ["Accounts", "Accounts_5pc"]:
            raw_parent_acc = (
                pg_db.query(Account.id, Account.account_name)
                .filter(Account.id == int(parent_id))
                .first()
            )
            Parent_Id = {
                "id": str(raw_parent_acc.id) if raw_parent_acc else str(parent_id),
                "account_name": raw_parent_acc.account_name if raw_parent_acc else "Unknown",
            }
        elif module_name in ["Contacts", "Contacts_5pc"]:
            raw_parent_con = (
                pg_db.query(Contact.id, Contact.last_name)
                .filter(Contact.id == int(parent_id))
                .first()
            )
            Parent_Id = {
                "id": str(raw_parent_con.id) if raw_parent_con else str(parent_id),
                "contact_name": raw_parent_con.last_name if raw_parent_con else "Unknown",
            }
        elif module_name in ["Tickets", "Tickets_5pc"]:
            raw_parent_ticket = (
                pg_db.query(Ticket.id, Deal.account_name)
                .join(Deal, Ticket.deal_id == Deal.id)
                .filter(Ticket.id == int(parent_id))
                .first()
            )
            Parent_Id = {
                "id": str(raw_parent_ticket.id) if raw_parent_ticket else str(parent_id),
                "ticket_name": raw_parent_ticket.account_name if raw_parent_ticket else "Unknown",
            }
        elif module_name in ["Job_Requirements", "Job_Requirements_5pc"]:
            from src.models.hiring import JobRequirement

            raw_parent_jr = (
                pg_db.query(JobRequirement.id, JobRequirement.hiring_position)
                .filter(JobRequirement.id == int(parent_id))
                .first()
            )
            Parent_Id = {
                "id": str(raw_parent_jr.id) if raw_parent_jr else str(parent_id),
                "job_requirement_name": raw_parent_jr.hiring_position
                if raw_parent_jr
                else "Unknown",
            }
        elif module_name in ["Candidates", "Candidates_5pc"]:
            from src.models.hiring import Candidate

            raw_parent_can = (
                pg_db.query(Candidate.id, Candidate.candidate_name)
                .filter(Candidate.id == int(parent_id))
                .first()
            )
            Parent_Id = {
                "id": str(raw_parent_can.id) if raw_parent_can else str(parent_id),
                "candidate_name": raw_parent_can.candidate_name
                if raw_parent_can
                else "Unknown",
            }
        elif module_name in ["Account_Tasks", "AccountTasks", "AccountTask"]:
            from src.models.account_task import AccountTask

            p_int = int(parent_id) if str(parent_id).isdigit() else None
            raw_parent_task = (
                pg_db.query(AccountTask.id, AccountTask.task_type)
                .filter(AccountTask.id == parent_id if p_int is None else (AccountTask.id == p_int))
                .first()
            )
            Parent_Id = {
                "id": str(raw_parent_task.id) if raw_parent_task else str(parent_id),
                "task_name": f"Account Task #{raw_parent_task.id}"
                if raw_parent_task
                else "Account Task",
            }
        else:
            raw_parent_deal = (
                pg_db.query(Deal.id, Deal.deal_name)
                .filter(Deal.id == int(parent_id))
                .first()
            )
            Parent_Id = {
                "id": str(raw_parent_deal.id) if raw_parent_deal else str(parent_id),
                "deal_name": raw_parent_deal.deal_name
                if raw_parent_deal
                else "Unknown",
            }

        now_iso = datetime.now(UTC).isoformat()
        note_doc = {
            "Owner": Owner,
            "Created_By": Created_By,
            "Modified_By": Modified_By,
            "Note_Content": note,
            "Parent_Id": Parent_Id,
            "module": module_name,
            "notesParentId": notes_parent_id,
            "Created_Time": now_iso,
            "Modified_Time": now_iso,
        }

        result = notes_coll.insert_one(note_doc)
        print("Insertion result", result)

        inserted_id = str(result.inserted_id)
        note_doc["_id"] = inserted_id

        # Format Created_Time / Modified_Time to readable string for response consistency
        try:
            dt = datetime.fromisoformat(now_iso).astimezone(IST)
            note_doc["Created_Time"] = dt.strftime("%d %b %Y, %I:%M %p")
            note_doc["Modified_Time"] = dt.strftime("%d %b %Y, %I:%M %p")
        except Exception:
            pass

        log_action(
            pg_db,
            user_id,
            user_role,
            "CREATED",
            "Note",
            int(parent_id),
            {"note": note, "parent_id": parent_id, "notesParentId": notes_parent_id},
        )

        creator_name = (
            Owner.get("first_name")
            if (Owner and Owner.get("first_name"))
            else "A CRM User"
        )
        BackgroundThreadPool.execute_task(
            mentions,
            note,
            module_name,
            parent_id,
            creator_name,
        )

        return JSONResponse(
            status_code=201,
            content={
                "message": "Note saved successfully",
                "data": note_doc,
            },
        )
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"error": str(e)})


def get_notes(
    notes_collection: Collection,
    pair_filters: list[dict[str, str]] = None,
    id_list: Any = None,
    module_name: str | list[str] = None,
):
    try:
        filter_query = {}

        # 1. Handle the NEW paired filters (from the code I gave you)
        if pair_filters:
            filter_query = {"$or": pair_filters}

        # 2. Handle the OLD style (to fix the Internal Server Error in Deals/Contacts)
        elif id_list:
            filter_query = (
                {"Parent_Id.id": {"$in": id_list}}
                if isinstance(id_list, list)
                else {"Parent_Id.id": id_list}
            )
            if module_name:
                if isinstance(module_name, list):
                    filter_query["module"] = {"$in": module_name}
                else:
                    filter_query["module"] = module_name

        else:
            return []

        projection = {
            "_id": 1,
            "id": 1,
            "Owner": 1,
            "Note_Content": 1,
            "Parent_Id": 1,
            "Modified_By": 1,
            "Created_By": 1,
            "Created_Time": 1,
            "Modified_Time": 1,
            "module": 1,
            "notesParentId": 1,
        }

        notes_cursor = notes_collection.find(filter_query, projection).sort(
            [("Created_Time", -1), ("_id", -1)]
        )
        notes = []
        for note in notes_cursor:
            if "_id" in note:
                note["_id"] = str(note["_id"])
            if "notesParentId" not in note:
                note["notesParentId"] = None

            # Fix/Backfill missing or incomplete Owner/Created_By
            owner_obj = note.get("Owner")
            created_by_obj = note.get("Created_By")

            uid = None
            if isinstance(created_by_obj, dict) and created_by_obj.get("id"):
                uid = created_by_obj.get("id")
            elif isinstance(owner_obj, dict) and owner_obj.get("id"):
                uid = owner_obj.get("id")
            elif isinstance(owner_obj, (str, int)):
                uid = owner_obj

            if uid:
                uid_str = str(uid)
                uid_int = int(uid) if uid_str.isdigit() else None
                resolved_name = None

                if uid_int and uid_int in auth.users:
                    resolved_name = auth.users[uid_int]
                elif uid_str in auth.users:
                    resolved_name = auth.users[uid_str]

                if resolved_name:
                    if not owner_obj or not isinstance(owner_obj, dict):
                        note["Owner"] = {
                            "id": uid_str,
                            "first_name": resolved_name,
                            "name": resolved_name,
                            "full_name": resolved_name,
                        }
                    elif not (owner_obj.get("first_name") or owner_obj.get("name")):
                        owner_obj["first_name"] = resolved_name
                        owner_obj["name"] = resolved_name
                        owner_obj["full_name"] = resolved_name

                    if not created_by_obj or not isinstance(created_by_obj, dict):
                        note["Created_By"] = {
                            "id": uid_str,
                            "name": resolved_name,
                            "first_name": resolved_name,
                            "full_name": resolved_name,
                        }
                    elif not created_by_obj.get("name"):
                        created_by_obj["name"] = resolved_name
                        created_by_obj["first_name"] = resolved_name
                        created_by_obj["full_name"] = resolved_name

            # Time formatting
            for time_key in ["Created_Time", "Modified_Time"]:
                if note.get(time_key):
                    val = note[time_key]
                    try:
                        dt = (
                            datetime.fromisoformat(val) if isinstance(val, str) else val
                        )
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=UTC)
                        dt = dt.astimezone(IST)
                        note[time_key] = dt.strftime("%d %b %Y, %I:%M %p")
                    except Exception:
                        pass

            notes.append(note)
        return notes

    except Exception as e:
        print(f"Notes Error: {e}")
        return []


def map_user_name_with_id(note_text: str) -> str:
    pattern = r"zsu\[@user:(\d+)\]zsu|crm\[user#(\d+)#(\d+)\]crm|crm\[user#(\d+)\]crm"

    def replace(match):
        if match.group(1):  # zsu[@user:ID]zsu
            user_id = match.group(1)
        elif match.group(2):  # crm[user#ID#ID]crm
            user_id = match.group(2)
        elif match.group(4):  # crm[user#ID]crm
            user_id = match.group(4)
        else:
            return match.group(0)  # no user_id found, return original

        if not user_id:
            return match.group(0)

        user_id = int(user_id)

        return "@" + auth.users.get(user_id, str(user_id))

    return re.sub(pattern, replace, note_text)


def is_note_has_comment(note_text: str) -> bool:
    pattern = re.compile(r"crm\[user#(\d+)\]crm")
    return bool(pattern.search(note_text))


def mentions(note, module_name, parent_id, creator_name: str = "A CRM User"):
    try:  # check if the note_content have mentions in them
        is_note_there = is_note_has_comment(note)
        if is_note_there:  # mention is there in the comment
            pattern = re.compile(r"crm\[user#(\d+)\]crm")
            user_ids = pattern.findall(note)
            with SessionLocal() as db:
                users = (
                    db.query(User.id, User.full_name, User.email)
                    .filter(User.id.in_(user_ids))
                    .all()
                )

            email_list = []  # holds the list of emails_id of user with the msg
            for user in users:
                email_list.append(
                    {
                        "recipient_name": user.full_name,
                        "creator_name": creator_name,
                        "user_name": creator_name,
                        "user_email_address": user.email,
                        "module": module_name,
                        "entity_id": parent_id,
                        "note": map_user_name_with_id(note),
                    }
                )
            # after collection all the emails of the user time to prepare the body and send the email
            mail.process_mention_emails(email_list)
            print("All emails sent successfully")
            return
    except Exception as e:
        print(e)
        return
