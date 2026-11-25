"""Shared location and platform rules for the job service (pure functions, no network)."""
import re
from urllib.parse import urlparse

_CANADA = re.compile(
    r"\bcanada\b|\btoronto\b|\bontario\b|\bvancouver\b|\bmontr[eé]al\b|\bqu[eé]bec\b|\bottawa\b|\bcalgary\b|"
    r"\bwaterloo\b|\bedmonton\b|\bwinnipeg\b|\bhalifax\b|\bmississauga\b|\bkitchener\b|\balberta\b|"
    r"\bbritish columbia\b|\bnova scotia\b|,\s*(ON|BC|QC|AB|MB|NS)\b", re.I)
_US_STATES = ("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY "
              "NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC").split()
_US = re.compile(
    r"united states|\bU\.?S\.?A?\b|\bnew york\b|\bsan francisco\b|\bseattle\b|\bboston\b|\bchicago\b|\baustin\b|"
    r"\bbay area\b|\blos angeles\b|\bsan jose\b|\bmountain view\b|\bsunnyvale\b|\bsan diego\b|\bdenver\b|"
    r"\batlanta\b|\bpalo alto\b|\bmenlo park\b|\bredmond\b|\bbellevue\b|\bpittsburgh\b|\bwashington, d\.?c\.?|"
    r",\s*(" + "|".join(_US_STATES) + r")\b", re.I)

SUPPORTED_PLATFORMS = ("greenhouse", "lever", "ashby")


def in_canada(text):
    return bool(_CANADA.search(text or ""))


def in_us(text):
    return bool(_US.search(text or ""))


def in_scope(text):
    """Canada or the US (or both) is named somewhere in the location text."""
    return in_canada(text) or in_us(text)


def country_for(text):
    """'CA', 'US', 'BOTH' or None. 'BOTH' means a multi-country listing: sponsorship answers must be escalated."""
    ca, us = in_canada(text), in_us(text)
    if ca and us:
        return "BOTH"
    return "CA" if ca else ("US" if us else None)


def platform(url):
    host = urlparse(url or "").netloc.lower()
    for name, needles in (("greenhouse", ("greenhouse.io",)), ("lever", ("lever.co",)), ("ashby", ("ashbyhq.com",)),
                          ("workday", ("myworkdayjobs.com", "workday.com")), ("linkedin", ("linkedin.com",)),
                          ("workable", ("workable.com",))):
        if any(n in host for n in needles):
            return name
    return "other"


# Order for an outside agent working from a cloud browser: sites it can open first, sites that block it or need a
# login last (Lever pages show a CAPTCHA or block cloud browsers; LinkedIn needs a sign-in).
PLATFORM_RANK = {"greenhouse": 0, "ashby": 0, "other": 1, "workday": 1, "workable": 1, "lever": 2, "linkedin": 3}


def platform_rank(url):
    return PLATFORM_RANK.get(platform(url), 1)


def apply_mode(url):
    """'auto' when the apply step can drive this site, else 'manual' (the owner applies by hand)."""
    return "auto" if platform(url) in SUPPORTED_PLATFORMS else "manual"
