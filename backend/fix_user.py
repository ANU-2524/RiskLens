
import asyncio
from app.core.security import hash_password
from app.db.models import User, UserRole
from app.db.session import AsyncSessionLocal
from sqlalchemy import select

async def fix():
    print("Connecting to DB...")
    async with AsyncSessionLocal() as session:
        # Check if user exists
        result = await session.execute(select(User).where(User.email == "test@test.com"))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("User test@test.com already exists, updating password.")
            existing.hashed_password = hash_password("password123")
        else:
            print("Creating user test@test.com")
            user = User(
                email="test@test.com", 
                hashed_password=hash_password("password123"), 
                role=UserRole.ANALYST
            )
            session.add(user)
        
        await session.commit()
        print("Success: User 'test@test.com' with password 'password123' is now ready.")

if __name__ == "__main__":
    asyncio.run(fix())
