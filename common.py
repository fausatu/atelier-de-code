def Q(q, options, answer, why):
    return {"q": q, "options": options, "answer": answer, "why": why}


def code(lang, src):
    return {"lang": lang, "code": src.strip("\n")}


def M(id, track, title, minutes, goal, why, flow, points, pitfalls, example, notes, quiz, td):
    return {
        "id": id,
        "track": track,
        "title": title,
        "minutes": minutes,
        "goal": goal,
        "why": why,
        "flow": flow,
        "points": points,
        "pitfalls": pitfalls,
        "example": {**example, "notes": notes},
        "quiz": quiz,
        "td": td,
    }


def TD(title, enonce, consignes, starter, hints, solution, checks):
    return {
        "title": title,
        "enonce": enonce,
        "consignes": consignes,
        "starter": starter,
        "hints": hints,
        "solution": solution,
        "checks": checks,
    }
