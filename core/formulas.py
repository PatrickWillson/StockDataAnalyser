"""
Graham's balance-sheet values, defined once and used by every caller (annual, TTM and the
dossier's worked calculations), so the figures shown always match the figures tested.

The functions are plain arithmetic: they accept floats or Decimals and leave rounding,
"N/A" handling and warnings to the caller.
"""


def tangible_equity(total_equity, intangible_assets, goodwill):
    """
    Book value for the common in Graham's sense: equity less goodwill and other intangibles
    (GRAHAM_METHODOLOGY §3.5, Security Analysis ch. 42). Intangibles and goodwill are taken as
    magnitudes because some filers report them as negative numbers.
    """
    return total_equity - abs(intangible_assets) - abs(goodwill)


def net_current_asset_value(current_assets, total_liabilities, claims_outside_equity=0):
    """
    Net current asset value: "current assets alone, minus all liabilities and claims ahead of
    the issue" (GRAHAM_METHODOLOGY §3.3). claims_outside_equity covers minority interests and
    redeemable equity; Graham excluded "the interest of the minority stockholders of a
    subsidiary" from working capital. Deducting the whole minority interest (not just its share
    of subsidiary current assets) is the conservative reading (§8.4).
    Not working capital (current assets − current liabilities).
    """
    return current_assets - total_liabilities - claims_outside_equity
