from datetime import datetime, timezone

def identify_contact(conn, email, phone_number):
    cursor = conn.cursor(dictionary=True)

    # ── 1. Find all contacts matching email OR phoneNumber ──────────────────
    conditions = []
    params = []
    if email:
        conditions.append("email = %s")
        params.append(email)
    if phone_number:
        conditions.append("phoneNumber = %s")
        params.append(phone_number)

    query = f"SELECT * FROM Contact WHERE ({' OR '.join(conditions)}) AND deletedAt IS NULL"
    cursor.execute(query, params)
    matched_contacts = cursor.fetchall()

    # ── 2. No match → create brand-new primary contact ──────────────────────
    if not matched_contacts:
        now = datetime.now(timezone.utc)
        cursor.execute(
            """INSERT INTO Contact (phoneNumber, email, linkedId, linkPrecedence, createdAt, updatedAt, deletedAt)
               VALUES (%s, %s, NULL, 'primary', %s, %s, NULL)""",
            (phone_number, email, now, now)
        )
        conn.commit()
        new_id = cursor.lastrowid
        return {
            "primaryContatctId": new_id,
            "emails": [email] if email else [],
            "phoneNumbers": [phone_number] if phone_number else [],
            "secondaryContactIds": []
        }

    # ── 3. Collect all root primary IDs from matched contacts ───────────────
    primary_ids = set()
    for c in matched_contacts:
        if c["linkPrecedence"] == "primary":
            primary_ids.add(c["id"])
        else:
            primary_ids.add(c["linkedId"])

    # ── 4. Fetch all contacts under each primary (full cluster) ─────────────
    if len(primary_ids) == 1:
        primary_id = next(iter(primary_ids))
    else:
        # Two separate primary clusters are being linked → keep oldest as primary
        format_strings = ','.join(['%s'] * len(primary_ids))
        cursor.execute(
            f"SELECT * FROM Contact WHERE id IN ({format_strings}) AND deletedAt IS NULL",
            list(primary_ids)
        )
        primaries = cursor.fetchall()
        # Oldest = smallest createdAt
        primaries.sort(key=lambda x: x["createdAt"])
        true_primary = primaries[0]
        primary_id = true_primary["id"]

        # Turn all other primaries into secondaries
        now = datetime.now(timezone.utc)
        for p in primaries[1:]:
            cursor.execute(
                """UPDATE Contact SET linkedId=%s, linkPrecedence='secondary', updatedAt=%s
                   WHERE id=%s""",
                (primary_id, now, p["id"])
            )
            # Also re-point all their existing secondaries to the true primary
            cursor.execute(
                """UPDATE Contact SET linkedId=%s, updatedAt=%s
                   WHERE linkedId=%s AND deletedAt IS NULL""",
                (primary_id, now, p["id"])
            )
        conn.commit()

    # ── 5. Fetch the full cluster under true primary ─────────────────────────
    cursor.execute(
        """SELECT * FROM Contact
           WHERE (id=%s OR linkedId=%s) AND deletedAt IS NULL
           ORDER BY createdAt ASC""",
        (primary_id, primary_id)
    )
    cluster = cursor.fetchall()

    # ── 6. Check if incoming request brings NEW information ─────────────────
    existing_emails = {c["email"] for c in cluster if c["email"]}
    existing_phones = {c["phoneNumber"] for c in cluster if c["phoneNumber"]}

    is_new_email = email and email not in existing_emails
    is_new_phone = phone_number and phone_number not in existing_phones

    if is_new_email or is_new_phone:
        now = datetime.now(timezone.utc)
        cursor.execute(
            """INSERT INTO Contact (phoneNumber, email, linkedId, linkPrecedence, createdAt, updatedAt, deletedAt)
               VALUES (%s, %s, %s, 'secondary', %s, %s, NULL)""",
            (phone_number, email, primary_id, now, now)
        )
        conn.commit()
        # Refresh cluster
        cursor.execute(
            """SELECT * FROM Contact
               WHERE (id=%s OR linkedId=%s) AND deletedAt IS NULL
               ORDER BY createdAt ASC""",
            (primary_id, primary_id)
        )
        cluster = cursor.fetchall()

    # ── 7. Build response ────────────────────────────────────────────────────
    primary_contact = next(c for c in cluster if c["id"] == primary_id)

    emails = []
    phone_numbers = []
    secondary_ids = []

    # Primary info goes first
    if primary_contact["email"]:
        emails.append(primary_contact["email"])
    if primary_contact["phoneNumber"]:
        phone_numbers.append(primary_contact["phoneNumber"])

    for c in cluster:
        if c["id"] == primary_id:
            continue
        if c["email"] and c["email"] not in emails:
            emails.append(c["email"])
        if c["phoneNumber"] and c["phoneNumber"] not in phone_numbers:
            phone_numbers.append(c["phoneNumber"])
        secondary_ids.append(c["id"])

    cursor.close()
    return {
        "primaryContatctId": primary_id,
        "emails": emails,
        "phoneNumbers": phone_numbers,
        "secondaryContactIds": secondary_ids
    }
