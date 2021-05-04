def indented(line, indent_level, char=True):
    ichar = "⁍"
    if indent_level == 1:
        ichar = "‣"
    if indent_level == 2:
        ichar = "•"
    if indent_level == 3:
        ichar = "◦"
    char_part = f"{ichar} " if char else "  "
    return f'{"  " * indent_level}{char_part}{line}'


def format_centers_markdown(available_centers):
    level = 0
    lines = []
    for center in available_centers:
        lines.append(indented(f"*{center['name']}*", level))
        level = 1
        lines.append(indented(f"*Address:* {center['address']}", level, char=False))
        lines.append(indented(f"*Pincode:* {center['pincode']}", level, char=False))
        lines.append(
            indented(f"*Hours:* {center['from']} - {center['to']}", level, char=False)
        )
        lines.append(indented(f"*Fees:* {center['fee_type']}", level, char=False))

        lines.append(indented("*Sessions:*", level, char=False))
        for session in center["sessions"]:
            level = 2
            lines.append(indented(f"*{session['date']}*", level))
            level = 3
            lines.append(
                indented(
                    f"*Minimum Age:* {session['min_age_limit']}", level, char=False
                )
            )
            lines.append(
                indented(f"*Vaccine:* {session['vaccine']}", level, char=False)
            )
            lines.append(
                indented(
                    f"*Available:* {session['available_capacity']}", level, char=False
                )
            )
            lines.append(
                indented(
                    f"*Slots:* {'  |  '.join(session['slots'])}", level, char=False
                )
            )

    return "\n".join(lines)
