#!/usr/bin/env python
#
#  Copyright 2011 Tjerk Santegoeds
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import sqlalchemy as sql

from os import path
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

BFT_HOME = os.sep.join(path.abspath(__file__).split(os.sep)[:-2])
BFT_HOME = os.environ.get("BFT_HOME", BFT_HOME)

# TODO: Load database information from a configuration file.
BFT_DB = os.environ.get("BFT_DB", path.join(BFT_HOME, "data", "betfair.db"))

sqlite = sql.create_engine("sqlite:///" + BFT_DB)
Session = orm.scoped_session(orm.sessionmaker(bind=sqlite))

Base = declarative_base(bind=sqlite)


class Exchange(Base):
    __tablename__ = "exchanges"
    __table_args__ = {"schema": "bft"}

    def __init__(self, id, name):
        super(Exchange, self).__init__()
        self.id = id
        self.name = name

    id = sql.Column(sql.Integer, primary_key=True)
    name = sql.Column(sql.String)

    def __repr__(self):
        return "<%s(id='%s', name='%s')>" % (type(self).__name__, self.id,
               self.name)


class Market(Base):
    __tablename__ = "markets"
    __table_args__ = {"schema": "bft"}

    id = sql.Column(sql.Integer, primary_key=True)
    exchange_id = sql.Column(sql.Integer, sql.ForeignKey(Exchange.id),
                             primary_key=True)
    name = sql.Column(sql.String)
    type = sql.Column(sql.String)
    date = sql.Column(sql.Date)
    menu_path = sql.Column(sql.String)
    event_hierarchy = sql.Column(sql.String)
    bet_delay = sql.Column(sql.String)
    country_code = sql.Column(sql.String)
    last_refresh = sql.Column(sql.DateTime)
    runners = sql.Column(sql.Integer)
    winners = sql.Column(sql.Integer)
    amount_matched = sql.Column(sql.Float)
    is_bsp_market = sql.Column(sql.Boolean)
    is_turning_in_play = sql.Column(sql.Boolean)

    def __repr__(self):
        return "<%s(id='%s', name='%s', type='%s', date='%s')>" % (
               type(self).__name__, self.name, self.type,
               self.date.strftime("%Y%m%d"))


class Runner(Base):
    __tablename__ = "runners"
    __table_args__ = {"schema": "bft"}

    market_id = sql.Column(sql.Integer, ForeignKey(Market.id),
                           primary_key=True)
    selection_id = sql.Column(sql.Integer, primary_key=True)
    time = sql.Column(sql.DateTime, primary_key=True)
    actual_bsp = sql.Column(sql.Float)
    asian_line_id = sql.Column(sql.Integer)
    far_bsp = sql.Column(sql.Float)
    handicap = sql.Column(sql.Float)
    last_price_matched = sql.Column(sql.Float)
    near_bsp = sql.Column(sql.Float)
    reduction_factor = sql.Column(sql.Float)
    total_amount_matched = sql.Column(sql.Float)
    is_vacant = sql.Column(sql.Boolean)

    def __repr__(self):
        return "<%s(time='%s', market_id='%d', selection_id='%d'"  % (
               type(self).__name__, self.time.strftime("%Y%m%d.%H%M%S"),
               self.market_id, self.selection_id)


class RemovedRunner(Base):
    __tablename__ = "runners"
    __table_args__ = {"schema": "bft"}

    market_id = sql.Column(sql.String, sql.ForeignKey(Market.id),
                           primary_key=True)
    selection_name = sql.Column(sql.String, primary_key=True)
    removed_time = sql.Column(sql.DateTime, not_null=True)
    adjustment_factor = sql.Column(sql.String)

    def __repr__(self):
        return "<%s(removed_time='%s', market_id='%d', selection_name='%s'"  % (
               type(self).__name__, self.removed.strftime("%Y%m%d.%H%M%S"),
               self.market_id, self.selection_id)


class Selection(Base):
    __tablename__ = "selections"
    __table_args__ = {"schema": "bft"}



class Price(Base):
    __tablename__ = "prices"
    __table_args__ = {"schema": "bft"}

    date_time = sql.Column(sql.DateTime, primary_key=True)
    market_id = sql.Column(sql.Integer, primary_key=True)
    selection_id = sql.Column(sql.Integer, primary_key=True)
    bet_type = sql.Column(sql.Enum("B", "L", "T"))
    price = sql.Column(sql.Float)

    def __repr__(self):
        return "<%s(date_time='%s', market_id='%d', selection_id='%d', " \
               "bet_type='%s', price='%.4f')>" % (type(self).__name__,
               self.date_type.strftime("%Y%m%d.%H%M%S"), self.market_id,
               self.selection_id, self.bet_type, self.price)


def create_all():
    """Create all tables."""
    Base.metadata.create_all(sqlite)
    Session.merge(Exchange(1, "UK"))
    Session.merge(Exchange(2, "AU"))
    Session.commit()
    Session.close()


if __name__ == "__main__":
    create_all()
