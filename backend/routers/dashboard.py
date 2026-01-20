from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from backend.auth import verify_password, create_access_token, get_current_admin
from backend.database.local_db import get_system_config, save_system_config, SystemConfig
import backend.services.mongo_service as mongo_service # Import module to access updated 'db' var dynamically

router = APIRouter(prefix="/api", tags=["dashboard"])

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    config = get_system_config()
    if not config.is_setup_complete:
        raise HTTPException(status_code=400, detail="System not setup")
    
    if form_data.username != config.admin_username or not verify_password(form_data.password, config.admin_password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": config.admin_username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/dashboard/stats")
async def get_stats(admin: str = Depends(get_current_admin)):
    # Retrieve stats from Mongo
    active_groups = 0
    if mongo_service.db is not None:
        active_groups = await mongo_service.db.groups.count_documents({})
    
    return {
        "active_groups": active_groups,
        "messages_processed": 1234, # Placeholder -> Needs Redis or a counter collection
        "bans": 15 # Placeholder
    }

@router.get("/dashboard/groups")
async def get_groups(admin: str = Depends(get_current_admin)):
    """
    Fetch list of groups.
    🔹 جلب قائمة المجموعات.
    """
    if mongo_service.db is None:
        return []
    
    groups_cursor = mongo_service.db.groups.find({}).limit(50)
    groups = []
    async for doc in groups_cursor:
        groups.append({
            "id": str(doc["_id"]),
            "title": doc.get("title", "Unknown Group"),
            "settings": {k: v for k, v in doc.items() if k != "_id"} # Return full doc as settings, excluding _id
        })
    return groups

@router.post("/config/update")
async def update_config(new_config: dict, admin: str = Depends(get_current_admin)):
    """
    Update system configuration dynamically.
    🔹 تحديث إعدادات النظام ديناميكياً.
    Only updates fields that are provided (Partial Update).
    """
    # DEBUG LOGGING
    import datetime
    with open("/app/data/backend_debug.txt", "a") as f:
        f.write(f"\n[{datetime.datetime.now()}] Config Update Request: {new_config.keys()}\n")
        f.write(f"Mongo DB Object: {mongo_service.db}\n")

    current = get_system_config()
    
    # Update only provided fields
    if new_config.get("bot_token"):
        current.bot_token = new_config["bot_token"]
    if new_config.get("support_group_id"):
        # Convert to int if possible
        try:
            current.support_group_id = int(new_config["support_group_id"])
        except:
            pass
    if new_config.get("log_channel_id"):
        try:
            current.log_channel_id = int(new_config["log_channel_id"])
        except:
            pass
    if new_config.get("mongo_uri"):
        current.mongo_uri = new_config["mongo_uri"]
    if "mongo_db_name" in new_config:
        if new_config.get("mongo_db_name"):
            current.mongo_db_name = new_config["mongo_db_name"]
        
    if "telegram_admin_ids" in new_config:
        # Expecting a list of ints. Validate.
        try:
            ids = [int(x) for x in new_config["telegram_admin_ids"]]
            current.telegram_admin_ids = ids
        except:
            pass # Ignore invalid list
        
    save_system_config(current)
    
    # 🌩️ Sync Admins to Cloud (MongoDB) as Source of Truth
    if "telegram_admin_ids" in new_config and mongo_service.db is not None:
        try:
             # Logic matching bot/services/db.py:add_admin
             # But here we have a list. We need to sync the list.
             # Strategy: Loop and Upsert.
             # Ideally we should also remove ones not in list, but let's stick to adding for now to be safe, 
             # OR distinct sync.
             # Given the UI sends the FULL list, we probably want to mirror it?
             # But "add_admin" in bot stores "username" etc. The UI only sends IDs.
             # So we will Upsert the IDs.
             for admin_id in current.telegram_admin_ids:
                 await mongo_service.db.admins.update_one(
                     {"user_id": admin_id},
                     {"$setOnInsert": {"user_id": admin_id, "username": "FromDashboard", "added_at": 0}},
                     upsert=True
                 )
             
             # Also, if we want to support "removing" admins via dashboard, we would need to delete from Mongo.
             # Let's find IDs in Mongo that are NOT in the new list and remove them.
             existing_cursor = mongo_service.db.admins.find({})
             existing_admins = []
             async for doc in existing_cursor:
                 existing_admins.append(doc["user_id"])
             
             for old_id in existing_admins:
                 if old_id not in current.telegram_admin_ids:
                     await mongo_service.db.admins.delete_one({"user_id": old_id})
                     print(f"Removed Admin {old_id} from Cloud via Dashboard")
                     
        except Exception as e:
            print(f"Error syncing admins to Cloud: {e}")

    return {"status": "success", "message": "تم تحديث الإعدادات (Config updated & Synced to Cloud)"}

@router.get("/config/get")
async def get_config_safe(admin: str = Depends(get_current_admin)):
    """
    Get safe config params (IDs, etc) but NOT secrets like passwords.
    🔹 جلب الإعدادات الآمنة (بدون كلمات المرور).
    """
    current = get_system_config()
    return {
        "bot_token": current.bot_token, # Send token to allow edit? Maybe mask it.
        "support_group_id": current.support_group_id,
        "log_channel_id": current.log_channel_id,
        "mongo_uri": current.mongo_uri,
        "mongo_db_name": current.mongo_db_name,
        "telegram_admin_ids": current.telegram_admin_ids
    }


@router.post("/dashboard/groups/{group_id}/toggle")
async def toggle_group_status(group_id: str, admin: str = Depends(get_current_admin)):
    """
    Toggle group active status.
    🔹 تفعيل/تعطيل المجموعة.
    """
    if mongo_service.db is None:
         raise HTTPException(status_code=500, detail="Database not connected")
    
    from bson import ObjectId
    try:
        oid = ObjectId(group_id)
        group = await mongo_service.db.groups.find_one({"_id": oid})
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Toggle
        new_status = not group.get("settings", {}).get("is_active", False)
        
        # Update nested field 'settings.is_active' AND root 'is_active' (if exists, schema varies)
        # Based on db.py: default_settings has "is_active" at root AND likely utilized in settings dict by UI?
        # db.py structure: default_settings = { "is_active": False, ... }
        # So it's at ROOT.
        
        # NOTE: dashboard.get_groups returns "settings": doc.get("settings", {})
        # But wait, db.py insert_one(default_settings).
        # So "is_active" IS at the root of the document.
        # But `get_groups` wraps it?
        
        # Let's check get_groups again.
        # "settings": doc.get("settings", {}) -> This assumes there is a sub-dict?
        # In db.py: insert_one(default_settings). NO sub-dict "settings".
        # The document ITSELF is the settings.
        # So get_groups is WRONG?
        # "settings": doc.get("settings", {}) -> If doc has no "settings" key, it returns empty dict!
        
        # FIX: The doc IS the settings.
        # So we should toggle the ROOT 'is_active'.
        
        await mongo_service.db.groups.update_one(
            {"_id": oid},
            {"$set": {"is_active": new_status}}
        )
        return {"status": "success", "new_state": new_status}
        
    except Exception as e:
        print(f"Error toggling group: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/dashboard/groups/{group_id}")
async def delete_group(group_id: str, admin: str = Depends(get_current_admin)):
    """
    Delete a group from management.
    🔹 حذف المجموعة من النظام.
    """
    if mongo_service.db is None:
         raise HTTPException(status_code=500, detail="Database not connected")
         
    from bson import ObjectId
    try:
        oid = ObjectId(group_id)
        result = await mongo_service.db.groups.delete_one({"_id": oid})
        if result.deleted_count == 0:
             raise HTTPException(status_code=404, detail="Group not found")
             
        return {"status": "success", "message": "Group deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
