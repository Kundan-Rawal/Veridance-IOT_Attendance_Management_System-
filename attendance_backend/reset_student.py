import os
from dotenv import load_dotenv

load_dotenv()

from database import SessionLocal
from auth import hash_password
import models

def reset_student_password():
    db = SessionLocal()
    
    # We are targeting your specific roll number
    target_roll_no = "0002CB221024"
    new_password = "Student@1234"
    
    try:
        # Find the student in the database
        student = db.query(models.Student).filter(models.Student.roll_no == target_roll_no).first()
        
        if student:
            print(f"Found student: {student.name} ({student.roll_no}). Resetting password...")
            student.password_hash = hash_password(new_password)
            db.commit()
            print(f"SUCCESS: Password for {target_roll_no} has been reset to: {new_password}")
        else:
            print(f"ERROR: Student {target_roll_no} not found. Are you sure they are enrolled?")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_student_password()