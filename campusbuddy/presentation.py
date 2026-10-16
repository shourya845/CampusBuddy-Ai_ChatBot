import json


def render(result):
    if "error" in result:
        return result["error"]
    if result.get("status") == "confirmation_required":
        return (
            "Please confirm this change: "
            + json.dumps(result.get("proposed_change"), ensure_ascii=False)
            + f". {result.get('present', '')} present / {result.get('absent', '')} absent. No academic records changed. Use Confirm change or Cancel."
        )
    if "below_75" in result:
        return (
            f"{result['course']}: {result['count']} students below 75%.\n"
            + "\n".join(
                (
                    f"- Roll {record['roll_no']} ({record['name']}): {record['percentage']}%"
                    for record in result["below_75"]
                )
            )
        )

    def line(record):
        pct = (
            "No held classes"
            if record["percentage"] is None
            else f"{record['percentage']}% ({record['present']}/{record['held']})"
        )
        text = f"{record['course']}: {pct}. {record['message']} Remaining planned classes: {record['remaining_planned_classes']}."
        if "exams" in record:
            text += (
                " Marks: "
                + ", ".join(
                    (
                        f"{e['exam_type']} {(e['score'] if e['score'] is not None else 'pending')}/{e['max_score']}"
                        for e in record["exams"]
                    )
                )
                + f". Grade {record['grade']}."
            )
        if record.get("unrecorded_classes"):
            text += f" {record['unrecorded_classes']} unrecorded held classes counted as absent."
        return text

    if "courses" in result:
        return (
            "\n\n".join((line(record) for record in result["courses"]))
            or "No accessible courses found."
        )
    if "percentage" in result:
        return line(result)
    return json.dumps(result, indent=2)
