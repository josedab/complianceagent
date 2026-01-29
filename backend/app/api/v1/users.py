"""User endpoints."""

from fastapi import APIRouter

from app.api.v1.deps import DB, CurrentUser
from app.core.security import get_password_hash
from app.schemas.user import UserRead, UserUpdate


router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_current_user_info(current_user: CurrentUser) -> UserRead:
    """Get current user information."""
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_current_user(
    user_in: UserUpdate,
    current_user: CurrentUser,
    db: DB,
) -> UserRead:
    """Update current user information."""
    update_data = user_in.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.flush()
    await db.refresh(current_user)

    return current_user
