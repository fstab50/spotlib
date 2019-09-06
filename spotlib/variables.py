"""
    Static assignments for universally used colors and variables

"""
import os
from spotlib.statics import local_config
from libtools import Colors

c = Colors()

try:

    from spotlib.oscodes_unix import exit_codes
    os_type = 'Linux'
    user_home = os.getenv('HOME')
    splitchar = '/'                                     # character for splitting paths (linux)

    # special colors - linux
    acct = c.BOLD + c.BRIGHT_GREEN
    text = c.BRIGHT_PURPLE
    TITLE = c.WHITE + c.BOLD

except Exception:
    from spotlib.oscodes_win import exit_codes           # non-specific os-safe codes
    os_type = 'Windows'
    username = os.getenv('username')
    splitchar = '\\'                                    # character for splitting paths (windows)
    user_home = 'Users' + splitchar + username
    # special colors - windows
    acct = c.CYAN
    text = c.LT2GRAY
    TITLE = c.WHITE + c.BOLD


# universal colors
rd = c.RED + c.BOLD
yl = c.YELLOW + c.BOLD
fs = c.GOLD3
bd = c.BOLD
gn = c.BRIGHT_GREEN
title = c.BRIGHT_WHITE + c.BOLD
bcy = c.BRIGHT_CYAN
bdcy = c.CYAN + c.BOLD          # bold blue
bbc = bd + c.BRIGHT_CYAN
bbl = bd + c.BRIGHT_BLUE
highlight = bd + c.BRIGHT_BLUE
frame = gn + bd
btext = text + c.BOLD
bwt = c.BRIGHT_WHITE
bdwt = c.BOLD + c.BRIGHT_WHITE
ub = c.UNBOLD
rst = c.RESET

# globals
config_dir = local_config['CONFIG']['CONFIG_PATH']      # path to localhost configuration directory
