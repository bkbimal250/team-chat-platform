from types import SimpleNamespace
from uuid import uuid4

from app.main import User
from app.workspace import workspace_directory_visible, workspace_profile


def test_workspace_directory_hides_contacts_only_visibility():
    privacy = SimpleNamespace(profile_photo_visibility="CONTACTS", about_visibility="CONTACTS")
    assert workspace_directory_visible(privacy) is False


def test_workspace_profile_masks_fields_by_visibility():
    user = User(
        id=uuid4(),
        identity_id=uuid4(),
        display_name="Ada",
        about="Bio",
        avatar_media_id=uuid4(),
        status="ACTIVE",
    )
    privacy = SimpleNamespace(profile_photo_visibility="NOBODY", about_visibility="ORGANIZATION")
    result = workspace_profile(user, privacy)
    assert result["display_name"] == "Ada"
    assert result["about"] == "Bio"
    assert result["avatar_media_id"] is None
