#!/usr/bin/env python

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import ConfigParser
import migrate.exceptions

from migrate.versioning.shell import main

if __name__ == '__main__':
    import os.path
    import sys
    for path in sys.path:
        migrate_repo_path = os.path.join(path, 'fusion', 'db', 'sqlalchemy',
                                         'migrate_repo')
        if os.path.exists(migrate_repo_path):
            break
    
    config = ConfigParser.SafeConfigParser()
    try:
        config = ConfigParser.SafeConfigParser()
        config.readfp(open('/etc/fusion/fusion.conf'))
        sql_connection = config.get('database', 'connection')
    except Exception:
        sql_connection = 'mysql://fusion:fusion@localhost/fusion'

    try:
        main(url=sql_connection, debug='False', repository=migrate_repo_path)
    except migrate.exceptions.DatabaseAlreadyControlledError:
        print('Database already version controlled.')
