import datetime
import motor.motor_asyncio

class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.files = self.db.files

    def new_user(self, user_id):
        return {
            "id": int(user_id),
            "join_date": datetime.date.today().isoformat()
        }

    async def add_user(self, user_id):
        await self.col.insert_one(self.new_user(user_id))

    async def is_user_exist(self, user_id):
        user = await self.col.find_one({"id": int(user_id)})
        return bool(user)

    async def total_users_count(self):
        return await self.col.count_documents({})

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({"id": int(user_id)})

    async def save_file(self, file_id, file_name, file_size, message_id):
        await self.files.update_one(
            {"file_id": int(file_id)},
            {"$set": {
                "file_id": int(file_id),
                "file_name": file_name,
                "file_size": int(file_size),
                "message_id": int(message_id)
            }},
            upsert=True
        )

    async def get_file(self, file_id):
        return await self.files.find_one({"file_id": int(file_id)})
