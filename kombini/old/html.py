# ==============================================================================
"""
    name:           my/html.py

    description:    


(c) Alfred LEUNG 2008-2012
"""
# ==============================================================================

# ==============================================================================
# Import
# ==============================================================================
import re


# ==============================================================================
# Various functions
# ==============================================================================
def remove_tags(data):
    "Remove tags from data"
    p = re.compile(r"<.*?>")
    return p.sub("", data)


# ==============================================================================
# Intermediary functions
# ==============================================================================
def _t(tag, content, align=None, rowspan=None, colspan=None):
    "Table cell"
    rez = "<%s" % tag
    if rowspan:
        rez += ' rowspan="%s"' % rowspan
    if colspan:
        rez += ' colspan="%s"' % colspan
    if align:
        rez += ' align="%s"' % align
    rez += ">%s</%s>\n" % (content, tag)
    return rez


# ==============================================================================
# Generic element
# ==============================================================================
def tag(name, body=None, atts=None):
    def escape(s):
        return s

    if atts:
        s_atts = " " + " ".join('%s="%s"' % (k, escape(atts[k])) for k in atts)
    else:
        s_atts = ""
    return "<%s%s>%s</%s>" % (name, s_atts, body if body else "", name)


# ==============================================================================
# Shortcuts
# ==============================================================================


def sh_color(text, color):
    return '<font color="%s">%s</font>' % (color, text)


# ==============================================================================
# Extended structures
# ==============================================================================

# ==============================================================================
# Tag creators
# ==============================================================================


def b(text):
    return "<b>%s</b>" % text


def body(text, bgcolor):
    return '<html><body bgcolor="%s">%s</body></html>' % (bgcolor, text)


def br():
    return "<br />"


def caption(text):
    "caption in table"
    return "<caption>%s</caption>\n" % text


def dd(text):
    return "<dd>%s</dd>" % text


def dl(text):
    return "<dl>%s</dl>" % text


def dt(text):
    return "<dt>%s</dt>" % text


def font(text, face=None, size=None, color=None):
    rez = ""
    if face:
        rez += 'face="%s" ' % face
    if size:
        rez += 'size="%s" ' % size
    if color:
        rez += 'color="%s" ' % color
    return "<font %s>%s</font>" % (rez, text)


def form(body, action, method="GET"):
    return """
        <form method=%s action="%s">
        %s
        </form>
    """ % (
        method,
        action,
        body,
    )


def h(text, level=1, align="left", props=""):
    return """<h%s %s align="%s">%s</h%s>\n""" % (level, props, align, text, level)


def href(text, ref, props="", new_window=False):
    "hyperlink"
    if new_window:
        extra = 'target="_blank"'
    else:
        extra = ""
    if props:
        extra = "%s %s" % (extra, props)
    return """<a href="%s" %s>%s</a>""" % (ref, extra, text)


def html(body, head=None, title=None):
    return """
        <html>
            <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
            %s
            %s
            </head>
            <body>
            %s
            </body>
        </html>
    """ % (
        ("<title>%s</title>" % title) if title else "",
        head if head else "",
        body,
    )


def input(type, parms):
    """
    types
    - button
        + [value] :: name on the button
        + [onclick]
    - radio
        + [name]
        + [value]
        + [checked(bool]
    - checkbox
        + [name]
        + [value]
        + [checked(bool)]
    - password
        + [name]
        + [value]
    - text
        + [name] :: name of the variable
        + [value] :: initial (default) value of variable
        + [onclick] :: can put javascript in it
        + [onfocus]
        + [onchange]
        + [onload]
        + [onblur] :: when user leaves the input field
        + [size] :: size of field
        + [maxlength] :: max length of field
    - reset
        + [value] :: name on the button
    - submit
        + [value] :: name on the button
    """

    def fmt(k):
        v = parms[k]
        if not v:
            return ""
        elif v is True:
            return str(k)
        else:
            return '%s="%s"' % (k, v)

    parms_s = " ".join([fmt(k) for k in parms]) if parms else ""
    return "<input type=%s %s />" % (type, parms_s)


def label(id, text):
    return '<label for="%s">%s</label>\n' % (id, text)


def li(text):
    return "<li>%s</li>\n" % text


def ol(text):
    "ordered list"
    return "<ol>%s</ol>\n" % text


def option(text, value=None, selected=False):
    if value:
        vl = 'value="%s"' % value
    else:
        vl = ""
    if selected:
        sl = 'selected="selected"'
    else:
        sl = ""
    return "<option %s %s>%s</option>\n" % (vl, sl, text)


def p(text):
    "paragraph"
    return (
        """
        <p>
        %s
        </p>
    """
        % text
    )


def pre(text):
    "paragraph"
    return "<pre>%s</pre>" % text


def select(body, name=None, size=0, multiple=False):
    """
    multiple to authorize multiple selection
    <select name="foo" size="3" multiple>
        <option value="val1" selected>val1</option>
        <option value="val2" >val2</option>
        <option value="val3" >val3</option>
    </select>
    """
    return """
    <select %s %s %s>
    %s
    </select>
    """ % (
        'name="%s"' % name if name else "",
        'size="%s"' % size if size else "",
        "multiple" if multiple else "",
        body,
    )


def small(text):
    return "<small>%s</small>" % text


def sub(text):
    "subscript"
    return "<sub>%s</sub>" % text


def sup(text):
    "superscript (to display exponent)"
    return "<sup>%s</sup>" % text


def table(content, border=0):
    return """
        <table border="%s">
        %s
        </table>
    """ % (
        border,
        content,
    )


def td(content, align=None, rowspan=None, colspan=None):
    "table cell"
    return _t(tag="td", content=content, align=align, rowspan=rowspan, colspan=colspan)


def th(content, align=None):
    "table header"
    return _t(tag="th", content=content, align=align)


def tr(content):
    "table row"
    return "<tr>%s</tr>" % content


def ul(body, type="disc"):
    return """
        <ul type="%s">
        %s
        </ul>
    """ % (
        type,
        body,
    )


# ==============================================================================
# Convenience functions
# ==============================================================================


def cv_select(name, options, size=0, multiple=False):
    def proc(o):
        if type(o) is str:
            return option(o)
        else:
            return option(o[0], value=o[1])

    body = "\n".join(proc(o) for o in options)
    return select(body, name=name, size=size, multiple=multiple)
