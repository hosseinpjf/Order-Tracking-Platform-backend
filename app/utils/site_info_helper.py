from fastapi import HTTPException



def update_list(is_image, old_list, new_list, old_images):
    old_list = old_list or []
    new_list = new_list or []

    old_map = {}

    for item in old_list:
        if not isinstance(item, dict): continue

        item_id = item.get("id")

        if item_id: old_map[item_id] = item
        # {"1":{...},"2":{...}}

    for new_item in new_list:

        if not isinstance(new_item, dict): continue

        item_id = new_item.get("id")

        if not item_id:
            raise HTTPException(status_code=400, detail="Item id is required")

        if item_id not in old_map:
            raise HTTPException(status_code=400, detail=f"Item '{item_id}' not found")

        for key, value in new_item.items():

            if key == "id": continue

            old_value = old_map[item_id].get(key)
            if is_image and key in ("icon", "url") and value and old_value and old_value != value:
                old_images.add(old_value)

            if value is not None: old_map[item_id][key] = value

    return list(old_map.values())


def update_section(old_section: dict | None, new_section, old_images):
    old_section = old_section or {}

    if isinstance(new_section, dict):
        data = new_section
    else:
        data = new_section.model_dump(
            mode="json",
            exclude_unset=True,
            exclude_none=True
        )

    section = old_section.copy()

    for key, value in data.items():

        if key == "images":
            section["images"] = update_list(True, section.get("images", []), value, old_images)

        elif key == "buttons":
            section["buttons"] = update_list(False, section.get("buttons", []), value, old_images)

        else:
            section[key] = value

    return section


def delete_list(is_image, current, value, old_images):
    ids = {item["id"] for item in value}
    current_ids = {item["id"] for item in current}

    missing_ids = ids - current_ids
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Item(s) not found: {', '.join(sorted(missing_ids))}")

    if is_image:
        for item in current:
            if item.get("id") in ids:
                image = item.get("icon") or item.get("url")
                if image:
                    old_images.add(image)

    return [
        item
        for item in current
        if item["id"] not in ids
    ]

