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
lbrct = bbc + '[ ' + rst        # left bracket
rbrct = bbc + ' ]' + rst        # right bracket
vdiv = bbc + ' | ' + rst
tab = '\t'.expandtabs(24)

menu_title = '\n' + c.BOLD + tab + PACKAGE + rst + ' help contents'

synopsis_cmd = (
        ACCENT + PACKAGE + rst + ' --start <values> ' +
        lbrct + '--end <values>' + rst
    )

url_doc = c.URL + 'http://spotlib.readthedocs.io' + rst
url_sc = c.URL + 'https://github.com/fstab50/spotlib' + rst


menu_body = menu_title + c.BOLD + """

  DESCRIPTION""" + rst + """

            A tool to retrieve Amazon EC2 Spot Instance Pricing
            Source Code Repo: """ + url_sc + """
    """ + c.BOLD + """
  SYNOPSIS""" + rst + """

        $ """ + synopsis_cmd + """

                        -l, --list  <methods> | <regions>
                       [-d, --debug    ]
                       [-h, --help     ]
                       [-V, --version  ]
    """ + c.BOLD + """
  OPTIONS
    """ + c.BOLD + """
        -l, --list""" + rst + """ <value>:  List available method calls or AWS
            region codes
    """ + c.BOLD + """
        -d, --debug""" + rst + """:  Print out additional  debugging information
    """ + c.BOLD + """
        -h, --help""" + rst + """: Show this help message, symbol legend, & exit
    """ + c.BOLD + """
        -V, --version""" + rst + """:  Print package version  and copyright info
    """
