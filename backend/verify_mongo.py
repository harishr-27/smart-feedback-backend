import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def verify_mongo():
    uri = "mongodb://localhost:27017"
    print(f"🔌 Connecting to MongoDB at {uri}...")
    
    try:
        client = AsyncIOMotorClient(uri)
        # Force a connection verification
        await client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
        
        print("\n📂 Listing Databases:")
        dbs = await client.list_database_names()
        for db in dbs:
            print(f" - {db}")
            
        target_db_name = "smart_feedback_db"
        if target_db_name in dbs:
            print(f"\n✅ Found target database: '{target_db_name}'")
            db = client[target_db_name]
            collections = await db.list_collection_names()
            print(f"   Collections in '{target_db_name}':")
            for col_name in collections:
                count = await db[col_name].count_documents({})
                print(f"    - {col_name}: {count} documents")
        else:
            print(f"\n❌ Target database '{target_db_name}' NOT FOUND.")
            
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_mongo())
