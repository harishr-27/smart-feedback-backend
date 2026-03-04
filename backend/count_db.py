import asyncio
from database import init_db
from models import StudentSubmission, User, Assignment

async def check():
    await init_db()
    users = await User.find_all().to_list()
    subs = await StudentSubmission.find_all().to_list()
    assigns = await Assignment.find_all().to_list()
    print(f"Users: {len(users)}")
    # for u in users:
    #     print(f"  - {u.email} (ID: {u.id})")

    print(f"Submissions: {len(subs)}")
    student_ids = set()
    for s in subs:
        student_ids.add(str(s.student_id))
    
    print("Unique Student IDs in Submissions:")
    for sid in student_ids:
        print(f"  - '{sid}'")

if __name__ == "__main__":
    asyncio.run(check())
