from app.constants import PERMISSIONS


def checkbox_value(form, key):
    return form.get(key) == "on"


def list_value(form, key):
    return form.getlist(key)


def user_payload_from_form(form, include_password=True):
    payload = {
        "employeeCode": form.get("employeeCode", "").strip(),
        "fullName": form.get("fullName", "").strip(),
        "email": form.get("email", "").strip().lower(),
        "mobileNo": form.get("mobileNo", "").strip(),
        "departmentId": form.get("departmentId", ""),
        "designation": form.get("designation", "").strip(),
        "reportingManagerId": form.get("reportingManagerId", ""),
        "userTypeId": form.get("userTypeId", ""),
        "roleId": form.get("roleId", ""),
        "systemAccess": list_value(form, "systemAccess"),
        "defaultDashboard": form.get("defaultDashboard", "requester"),
        "isActive": checkbox_value(form, "isActive"),
        "notificationEmail": checkbox_value(form, "notificationEmail"),
        "notificationInApp": checkbox_value(form, "notificationInApp"),
    }
    if include_password:
        payload["password"] = form.get("password", "")
    return payload


def permissions_from_form(form):
    return {key: checkbox_value(form, key) for key, _ in PERMISSIONS}


def validate_user_payload(payload, creating=True):
    errors = []
    if not payload.get("employeeCode"):
        errors.append("Employee code is required.")
    if not payload.get("fullName"):
        errors.append("Full name is required.")
    if not payload.get("email") or "@" not in payload["email"]:
        errors.append("Valid email is required.")
    if creating and not payload.get("password"):
        errors.append("Password is required.")
    if payload.get("password") and len(payload["password"]) < 8:
        errors.append("Password must be at least 8 characters.")
    if not payload.get("userTypeId"):
        errors.append("User type is required.")
    if not payload.get("roleId"):
        errors.append("Role is required.")
    return errors


def ticket_payload_from_form(form):
    return {
        "systemId": form.get("systemId", ""),
        "categoryId": form.get("categoryId", ""),
        "areaId": form.get("areaId", ""),
        "customAreaName": form.get("customAreaName", "").strip(),
        "priority": form.get("priority", ""),
        "title": form.get("title", "").strip(),
        "description": form.get("description", "").strip(),
        "expectedDate": form.get("expectedDate", ""),
        "attachmentName": form.get("attachmentName", "").strip(),
    }


def validate_ticket_payload(payload):
    errors = []
    if not payload.get("systemId"):
        errors.append("System is required.")
    if not payload.get("categoryId"):
        errors.append("Category is required.")
    if not payload.get("areaId"):
        errors.append("Area is required.")
    # If user picked "Other", they must describe the custom area.
    area_id = payload.get("areaId", "")
    if area_id.startswith("area_") and area_id.endswith("_other") and not payload.get("customAreaName"):
        errors.append("Please describe the custom area when choosing 'Other'.")
    if not payload.get("priority"):
        errors.append("Priority is required.")
    if len(payload.get("title", "")) < 5:
        errors.append("Title must be at least 5 characters.")
    if len(payload.get("description", "")) < 20:
        errors.append("Description must be at least 20 characters.")
    return errors
