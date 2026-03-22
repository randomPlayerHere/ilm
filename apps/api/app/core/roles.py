ROLE_HOME_PATHS = {
    "admin": "/admin",
    "principal": "/org-analytics",
    "teacher": "/(teacher)",
    "parent": "/(parent)",
    "student": "/(student)",
}


def is_supported_role(role: str) -> bool:
    return role in ROLE_HOME_PATHS


def home_path_for_role(role: str) -> str:
    return ROLE_HOME_PATHS.get(role, "/")
