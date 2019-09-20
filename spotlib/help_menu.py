"""

Help Menu

    Help menu object containing body of help content.
    For printing with formatting

"""

from spotlib.statics import PACKAGE
from spotlib.variables import c, bbc, rst


ACCENT = c.ORANGE               # orange accent highlight color
bdacct = c.ORANGE + c.BOLD      # bold orange
bdcy = c.CYAN + c.BOLD          # bold blue
lbrct = bbc + ' [ ' + rst        # left bracket
rbrct = bbc + ' ] ' + rst        # right bracket
vdiv = bbc + ' | ' + rst
tab = '\t'.expandtabs(24)

menu_title = '\n' + c.BOLD + tab + PACKAGE + rst + ' command help'

synopsis_cmd = (
        ACCENT + 'spotcli' + rst + ' --start <value> ' + '--end <value>' + vdiv +
        '--duration-days'
    )

url_doc = c.URL + 'http://spotlib.readthedocs.io' + rst
url_sc = c.URL + 'https://github.com/fstab50/spotlib' + rst


menu_body = menu_title + c.BOLD + """

  DESCRIPTION""" + rst + """

            A tool to retrieve Amazon EC2  Spot Instance Pricing
            Source Code Repo: """ + url_sc + """
    """ + c.BOLD + """
  SYNOPSIS""" + rst + """

        $ """ + synopsis_cmd + """

                        -r, --region <value>
                       [-s, --start  <value>  ]
                       [-e, --end    <value>  ]
                       [-l, --list   <methods> | <regions>  ]
                       [-d, --debug    ]
                       [-h, --help     ]
                       [-V, --version  ]
    """ + c.BOLD + """
  OPTIONS
    """ + c.BOLD + """
        -D, --duration-days""" + rst + """ <value>: Number of days of price data
            history to retrieve ending at midnight on present day
    """ + c.BOLD + """
        -e, --end""" + rst + """ <value>:  Datetime of end of the price sampling
            period (example: 2019-09-04T23:59:59)
    """ + c.BOLD + """
        -l, --list""" + rst + """ <value>: List available method calls or Amazon
            Web Services' region codes
    """ + c.BOLD + """
        -d, --debug""" + rst + """:  Print out additional  debugging information
    """ + c.BOLD + """
        -h, --help""" + rst + """: Show this help message, symbol legend, & exit
    """ + c.BOLD + """
        -r, --region""" + rst + """:  AWS region code (e.g. us-east-1) for which
    """ + c.BOLD + """
        -s, --start""" + rst + """ <value>:  Datetime of start of price sampling
            period (example: 2019-09-03T00:00:00)
            you wish to retrieve EC2 spot price data
    """ + c.BOLD + """
        -V, --version""" + rst + """: Print version, license, and copyright info
    """
