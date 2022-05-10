"""
TEMPLATE TO USE

#==============================================================================
# Imports
#==============================================================================
#-System-----------------------------------------------------------------------
#-Third party------------------------------------------------------------------
#-Own modules------------------------------------------------------------------
from outils.cli     import Cli
# from outils.cli     import date_type
# from outils.cli     import time_type
#==============================================================================
# Constants & Functions
#==============================================================================


#==============================================================================
#
#==============================================================================
class MyCli(Cli):
    def setup_parser(self):
        ''' 
        Add more options
        '''
        p=self.parser
        p.add_argument('--path')
        # p.add_argument('--foo')
        # p.add_argument('--flag',action='store_true')
        # p.add_argument('--nb',type-int)
        # p.add_argument('--date',type=date_type)
        # p.add_argument('--time',type=time_type)


    def after_parse(self):
        '''
        Put here things to do after parse
        '''
        pass


    #--------------------------------------------------------------------------
    #
    #--------------------------------------------------------------------------


    #--------------------------------------------------------------------------
    # Handlers (start method name with 'h_')
    #--------------------------------------------------------------------------
    def h_main(self):
        '''
        This is the function that get executed if no command is passed
        '''
        pass

    def h_test(self):
        pass


#==============================================================================
# CLI Main
#==============================================================================
if __name__=='__main__':
    MyCli().run_parser()
"""

# ==============================================================================
# Imports
# ==============================================================================
# -System-----------------------------------------------------------------------
import argparse
import datetime
import os
import platform
import sys
import traceback

# -Third party------------------------------------------------------------------
# -Own modules------------------------------------------------------------------
import outils.logger as OuL
import outils.email as OuE
import outils.html as OuHtml

# ==============================================================================
# Constants
# ==============================================================================
LOG_LEVEL = "info"

# ==============================================================================
#
# ==============================================================================
def date_type(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        try:
            return datetime.datetime.strptime(s, "%Y-%m").date()
        except:
            pass
    raise argparse.ArgumentTypeError(
        s + " is not a valid date in format YYYY-MM-DD or YYYY-MM"
    )


def time_type(s):
    try:
        return datetime.datetime.strptime(s, "%H:%M:%S").time()
    except ValueError:
        try:
            return datetime.datetime.strptime(s, "%H:%M").time()
        except ValueError:
            pass
    raise argparse.ArgumentTypeError(
        s + " is not a valid time in format HH:MM:SS or HH:MM"
    )


def datetime_type(s):
    try:
        return datetime.datetime.strptime(s, "%Y%m%d_%H%M%S")
    except ValueError:
        raise argparse.ArgumentTypeError(
            s + " is not a valid datetime in format %Y%m%d_%H%M%S"
        )


# ==============================================================================
#
# ==============================================================================
class Cli:
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog=None, description=None, epilog=None)
        self.output = []

    def setup_parser_initial(self):
        # self.parser.add_argument('--verbose',help='increase output verbosity'
        #                          action='store_true')
        # self.parser.add_argument('--date',dest='date',type=date_type)
        # self.parser.add_argument('--time',dest='time',type=time_type)
        # self.parser.add_argument('--foo')

        parser = self.parser

        parser.add_argument("--logfile", help="Log into a file")
        parser.add_argument("--loglevel", help="Loggging level", default=LOG_LEVEL)

        parser.add_argument("--mailto", action="append")

        parser.add_argument("command", nargs="?", help="Command to run", default="main")

    def setup_parser(self):
        """
        Put here things to set up the arguments parser
        """
        pass

    def after_parse(self):
        """
        Put here things to do after parse
        """
        pass

    def run_parser(self, run_cmd=True):
        try:
            self.setup_parser_initial()
            self.setup_parser()
            try:
                self.args = self.parser.parse_args()
            except:
                self.bye()
            self.logger = OuL.get_logger(
                name=None, level=self.args.loglevel, file=self.args.logfile
            )
            self.after_parse()
            if run_cmd:
                try:
                    command = getattr(self, "h_%s" % self.args.command)
                except KeyError:
                    self.bye("Command %s unknown" % self.args.command)
                else:
                    command()
        except:
            self.send_mail(
                subject="Error executing %s" % sys.argv, body=traceback.format_exc()
            )
            raise

    # --------------------------------------------------------------------------
    # Convenience functions
    # --------------------------------------------------------------------------
    def bye(self, msg=None, error=0):
        if msg:
            if error:
                self.logger.critical(msg)
            else:
                self.logger.info(msg)
        if error:
            sys.exit(error)
        else:
            #Do that to exit without error instead of sys.exit(0)
            #because the latter always causes an error
            os._exit(0)

    def send_mail(self, subject, body=None, body_html=None, atts=None):
        if self.args.mailto:
            rs = ",".join(self.args.mailto)
            if not body_html and self.output:
                body_html = OuHtml.html(OuHtml.pre("\n".join(self.output)))
            OuE.send_orgmode_message(
                recipient=rs,
                subject="[@%s] %s" % (platform.node(), subject),
                body=body,
                body_html=body_html,
                atts=atts,
                logger=self.logger,
            )
            self.logger.info("Mail sent to %s" % rs)

    def get_arg(self, k, bye_if_none=True):
        v = getattr(self.args, k)
        if v is None and bye_if_none:
            self.bye("No --%s provided" % k)
        return v

    def print(self, s):
        self.output.append(s)
        print(s)

    # --------------------------------------------------------------------------
    #
    # --------------------------------------------------------------------------
    def h_main(self):
        pass

    def h_test(self):
        self.logger.info("Test")


# ==============================================================================
#
# ==============================================================================
