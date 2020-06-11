def time_change(second):
    second = int(second)
    h = second // 3600
    m = (second // 60) % 60
    s = second % 60
    if m < 10:
        m = str('0' + str(m))
    else:
        m = str(m)
    if s < 10:
        s = str('0' + str(s))
    else:
        s = str(s)
    if h < 10:
        h = str('0' + str(h))
    else:
        h = str(h)

    return [h, m, s]


def time_word(t, id):
    times = {"0": ["час", "часа", "часов"], "1": ["минута", "минуты", "минут"], '2': ["секунда", "секунды", "секунд"]}
    s = str(t)
    s = s.lstrip("0")
    if len(s) == 0:
        return times[str(id)][2]
    elif len(s) >= 2:
        if int(s[-2]) == 1 or int(s[-1]) == 0:
            return times[str(id)][2]
        else:
            if int(s) == 0 or (5 <= int(s[-1]) <= 9):
                return times[str(id)][2]
            elif 2 <= int(s[-1]) <= 4:
                return times[str(id)][1]
            else:
                return times[str(id)][0]
    else:
        if int(s) == 0 or 5 <= int(s[-1]) <= 9:
            return times[str(id)][2]
        elif 2 <= int(s[-1]) <= 4:
            return times[str(id)][1]
        else:
            return times[str(id)][0]


def tts_change(h, m, s):
    hour = time_word(int(h), 0)
    minute = time_word(int(m), 1)
    second = time_word(int(s), 2)
    text = ""
    for i in [[h, hour], [m, minute], [s, second]]:
        if str(i[0]).lstrip("0") != "":
            text += str(int(str(i[0]).lstrip("0"))) + " " + str(i[1]) + " "
    return text

print(time_change(5000000000000))