import os
from dotenv import load_dotenv

load_dotenv()

from database import SessionLocal
from auth import hash_password
import models

def reset_password():
    db = SessionLocal()
    
    target_email = "rawalkundan987@gmail.com"
    new_password = "Admin@1234"
    
    try:
        # Find the admin
        admin = db.query(models.Admin).filter(models.Admin.email == target_email).first()
        
        if admin:
            print(f"Found admin: {admin.email}. Resetting password...")
            admin.password_hash = hash_password(new_password)
            db.commit()
            print(f"SUCCESS: Password for {target_email} has been reset to: {new_password}")
        else:
            print(f"Admin {target_email} not found. Creating a new one...")
            new_admin = models.Admin(
                name="System Admin",
                email=target_email,
                password_hash=hash_password(new_password)
            )
            db.add(new_admin)
            db.commit()
            print(f"SUCCESS: New admin created for {target_email} with password: {new_password}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_password()