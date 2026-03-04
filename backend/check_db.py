import asyncio
from database import init_db
from models import StudentSubmission, User

async def check():
    await init_db()
    
    print("--- Users ---")
    users = await User.find_all().to_list()
    for u in users:
        print(f"Email: {u.email}, Role: {u.role}, ID: {u.id}")

    print("\n--- Submissions ---")
    subs = await StudentSubmission.find_all().to_list()
    print(f"Total Submissions: {len(subs)}")
    for s in subs:
        print(f"ID: {s.id}, Student: {s.student_id}, Assignment: {s.assignment_id}")

if __name__ == "__main__":
    asyncio.run(check())
