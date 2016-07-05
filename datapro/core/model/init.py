# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import func

from datapro.core.model.common import Date
from datapro.core.db import OrmConnection


def init(connection):

    # Dimension Tables
    Date.__table__.create(connection.engine, checkfirst=True)

    connection.session.commit()

    if connection.session.query(func.count(Date.id)).scalar() == 0:
        start_date = datetime.date(1999, 12, 27)
        end_date = datetime.date(2019, 12, 29)
        for this_date in (start_date + datetime.timedelta(n) for n in range((end_date - start_date).days + 1)):
            connection.session.add(Date.from_date(this_date))
        connection.session.commit()


if __name__ == '__main__':

    connection = OrmConnection('admin')
    init(connection)
