#!/usr/bin/env python
"""MariaDB slave status checker"""
import sys
import argparse
import MySQLdb


class SlaveStatusCheck(object):
    """Class to help us run slave status queries against MariaDB"""
    REPLICATION_LAG_MODE = 'replication_lag'
    SLAVESQL_MODE = 'slave_sql'
    SLAVEIO_MODE = 'slave_io'
    MODES = (REPLICATION_LAG_MODE,
             SLAVESQL_MODE,
             SLAVEIO_MODE)

    def __init__(self, hostname, username, password, slave_conn,
                 mode, verbose=False, warning=None, critical=None):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.warning = warning
        self.critical = critical
        self.verbose = verbose
        self.mode = mode

        # Execute the query and store the results
        self._result = {}
        self.get_slave_status(slave_conn)

    def run_check(self):
        """Execute the check against the given mode"""
        check_fn = getattr(self, self.mode)
        check_fn()

    def replication_lag(self):
        pass

    def slave_sql(self):
        """Check that Slave_SQL_Running = Yes"""
        if self._result.get('Slave_SQL_Running') == "Yes":
            print "OK - Slave sql is running"
            sys.exit(0)
        else:
            print "CRITICAL - Slave sql is not running"
            sys.exit(2)

    def slave_io(self):
        """Check that Slave_IO_Running = Yes"""
        if self._result.get('Slave_IO_Running') == "Yes":
            print "OK - Slave io is running"
            sys.exit(0)
        else:
            print "CRITICAL - Slave io is not running"
            sys.exit(2)

    def get_slave_status(self, slave_connection):
        """Run the query!"""
        try:
            sql = 'SHOW SLAVE "{0}" STATUS'.format(slave_connection)
            conn = None
            conn = MySQLdb.Connection(
                self.hostname,
                self.username,
                self.password)

            curs = conn.cursor(MySQLdb.cursors.DictCursor)
            curs.execute(sql)
            conn.commit()

            self._result = curs.fetchall()[0]
            if self.verbose:
                print self._result
        except MySQLdb.Error, exc:
            print "ERROR - {0}: {1}".format(exc.args[0], exc.args[1])
            sys.exit(1)
        finally:
            if conn:
                conn.close()


def main():
    """starter method"""
    parser = argparse.ArgumentParser(description='MariaDB slave status checker')
    parser.add_argument('--hostname', default='localhost', type=str,
                        help="MariaDB hostname")
    parser.add_argument('--username', type=str, help="MariaDB username")
    parser.add_argument('--password', type=str, help="MariaDB password")
    parser.add_argument('--connection', required=True, type=str,
                        help="MariaDB slave connection")
    parser.add_argument('--mode', type=str, required=True,
                        choices=SlaveStatusCheck.MODES,
                        help="slave state to check")
    parser.add_argument('-w', '--warning', type=int, default=None,
                        help="warning limit")
    parser.add_argument('-c', '--critical', type=int, default=None,
                        help="critical limit")
    parser.add_argument('--verbose', action='store_true', default=False,
                        help="enable verbose mode")

    args = parser.parse_args()
    ssc = SlaveStatusCheck(args.hostname, args.username, args.password,
                           args.connection, args.mode, args.verbose,
                           args.warning, args.critical)
    ssc.run_check()
