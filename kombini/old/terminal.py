import os
import typing as ty

XT_RESET = 0
XT_BOLD = 1
XT_UNDERLINE = 4
XT_BLINK = 5
XT_REVERSE = 7

# XT_COL_WHITE=7
# XT_COL_BLACK=0

# def color(red,green,blue):
#     "each color btw 0 and 5"
#     return blue+green*6+red*36+16

# XT_COL_WHITE=color(5,5,5)
XT_COL_WHITE = 231
XT_COL_BLACK = 16
# XT_COL_BLACK=color(0,0,0)

def term_width() -> ty.Dict[str, int]:
    """
    Return size of terminal
    """
    # r,c=[int(x) for x in os.popen('stty size','r').read().split()]
    c, r = os.get_terminal_size()
    return {"rows": r, "columns": c}

def esc_effect(effect=XT_RESET):
    return "\033[%sm" % effect

def esc_color(fg=XT_COL_WHITE, bg=XT_COL_BLACK):
    return "\033[38;5;%sm\033[48;5;%sm" % (fg, bg)

def string(s, fg=XT_COL_WHITE, bg=XT_COL_BLACK):
    return esc_color(fg=fg, bg=bg) + s + esc_color()

def raw_len(s):
    """
    Calculate length of string without the escape sequences
    """
    l = 0
    in_esc = False
    for c in s:
        if in_esc:
            if c == "m":
                in_esc = False
        else:
            if c == "\033":
                in_esc = True
            else:
                l += 1
    # print 's=%s len=%s raw_len=%s' % (s,len(s),l)
    return l

class Ansi:
    """
    http://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html
    """
    RESET='\u001b[0m'
    BASIC_COLORS={
        'black':0,
        'red':1,
        'green':2,
        'yellow':3,
        'blue':4,
        'magenta':5,
        'cyan':6,
        'white':7,
        }

    @staticmethod
    def basic(color,bright=False,background=False):
        if background:
            code='\u001b[4%d' % Ansi.BASIC_COLORS[color.lower()]
        else:
            code='\u001b[3%d' % Ansi.BASIC_COLORS[color.lower()]
        if bright:
            code+=';1'
        return code+'m'

    @staticmethod
    def c256(n):
        return '\u001b[38;5;%dm' % n
