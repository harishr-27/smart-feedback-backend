import asyncio
import aiohttp
import json

BASE_URL = "http://127.0.0.1:8000"

async def test_api():
    async with aiohttp.ClientSession() as session:
        # 1. Create Assignment
        print("1️⃣ Creating Assignment...")
        assignment_data = {
            "title": "Phase 2 Test Assignment",
            "rubric_id": "mock_rubric_id", 
            "reference_material_ids": []
        }
        # Note: We need a rubric first usually, but for now just testing connectivity
        # Let's create a rubric first to be safe
        rubric_data = {
            "name": "Test Rubric",
            "criteria": []
        }
        async with session.post(f"{BASE_URL}/rubrics/", json=rubric_data) as resp:
            if resp.status != 200:
                print(f"❌ Failed to create rubric: {await resp.text()}")
                return
            rubric = await resp.json()
            rubric_id = rubric["_id"]
            print(f"✅ Rubric Created: {rubric_id}")
            
        assignment_data["rubric_id"] = rubric_id
        
        async with session.post(f"{BASE_URL}/assignments/", json=assignment_data) as resp:
            if resp.status != 200:
                print(f"❌ Failed to create assignment: {await resp.text()}")
                return
            assignment = await resp.json()
            assignment_id = assignment["_id"]
            print(f"✅ Assignment Created: {assignment_id}")

        # 2. List Assignments
        print("2️⃣ Listing Assignments...")
        async with session.get(f"{BASE_URL}/assignments/") as resp:
            assignments = await resp.json()
            print(f"✅ Found {len(assignments)} assignments")

if __name__ == "__main__":
    asyncio.run(test_api())
