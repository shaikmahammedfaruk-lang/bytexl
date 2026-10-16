def shared_demo_brand_filter() -> dict:
    """Match only explicitly shared demo brands, never legacy ownerless records."""
    return {
        "owner_id": {"$exists": True, "$eq": None},
        "is_demo": True,
        "is_shared": True,
    }


def is_shared_demo_brand(brand: dict) -> bool:
    return (
        "owner_id" in brand
        and brand.get("owner_id") is None
        and brand.get("is_demo") is True
        and brand.get("is_shared") is True
    )


def readable_brand_filter(user_id: str) -> dict:
    """Return the private-brand and shared-demo visibility rule."""
    return {
        "$or": [
            {"owner_id": user_id},
            shared_demo_brand_filter(),
        ]
    }


def brand_child_filter(brand: dict, user_id: str) -> dict:
    """Scope brand-associated records to their private owner or explicit demo status."""
    brand_id = str(brand.get("_id") or brand.get("id") or "")
    if not brand_id:
        return {"_id": {"$exists": False}}

    if (
        brand.get("owner_id") is not None
        and str(brand.get("owner_id")) == user_id
    ):
        owner_filter = {
            "$or": [
                {"owner_id": user_id},
                {"owner_id": {"$exists": False}},
            ]
        }
    elif is_shared_demo_brand(brand):
        owner_filter = {
            "owner_id": {"$exists": True, "$eq": None},
            "is_demo": True,
            "is_shared": True,
        }
    else:
        return {"_id": {"$exists": False}}

    return {
        "$and": [
            {"brand_id": brand_id},
            owner_filter,
        ]
    }


def is_brand_child_visible(
    brand: dict,
    user_id: str,
    record: dict,
) -> bool:
    """Check child ownership after resolving its parent brand."""
    if (
        brand.get("owner_id") is not None
        and str(brand.get("owner_id")) == user_id
    ):
        return (
            "owner_id" not in record
            or str(record.get("owner_id")) == user_id
        )

    return (
        is_shared_demo_brand(brand)
        and "owner_id" in record
        and record.get("owner_id") is None
        and record.get("is_demo") is True
        and record.get("is_shared") is True
    )


def readable_brand_children_filter(
    brands: list[dict],
    user_id: str,
) -> dict:
    """Build a non-empty owner-scoped query across visible brand records."""
    clauses = []
    private_brand_ids = []
    shared_demo_brand_ids = []

    for brand in brands:
        brand_id = str(brand.get("_id") or brand.get("id") or "")
        if not brand_id:
            continue

        if (
            brand.get("owner_id") is not None
            and str(brand.get("owner_id")) == user_id
        ):
            private_brand_ids.append(brand_id)
        elif is_shared_demo_brand(brand):
            shared_demo_brand_ids.append(brand_id)

    if private_brand_ids:
        clauses.append({
            "brand_id": {"$in": private_brand_ids},
            "$or": [
                {"owner_id": user_id},
                {"owner_id": {"$exists": False}},
            ],
        })

    if shared_demo_brand_ids:
        clauses.append({
            "brand_id": {"$in": shared_demo_brand_ids},
            "owner_id": {"$exists": True, "$eq": None},
            "is_demo": True,
            "is_shared": True,
        })

    if not clauses:
        return {"_id": {"$exists": False}}

    return {"$or": clauses}
