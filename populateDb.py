from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from databaseSetup import Category, Base, Item

engine = create_engine('sqlite:///catalogitem.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

category1 = Category(name="Kite Boarding")

session.add(category1)
session.commit()

item1 = Item(name='14m^2 Kite',
             description='Kite for light winds.',
             category=category1)

session.add(item1)
session.commit()

item2 = Item(name='11m^2 Kite',
             description='Kite for higher winds.',
             category=category1)

session.add(item2)
session.commit()

item3 = Item(name='Bar and Lines',
             description='Enable attachment of the kite to harness and steering.',
             category=category1)

session.add(item3)
session.commit()

item4 = Item(name='Harness',
             description='Connects rider to kite.',
             category=category1)

session.add(item4)
session.commit()

category2 = Category(name='Climbing')

session.add(category2)
session.commit()

item1 = Item(name='Harness',
             description='Connects climber to rope in the event of a fall :)',
             category=category2)

session.add(item1)
session.commit()

item2 = Item(name='Rope',
             description='Used to protect against a fall.',
             category=category2)

session.add(item2)
session.commit()

item3 = Item(name='Shoes',
             description='Rubber soles increase friction with rock.',
             category=category2)

session.add(item3)
session.commit()
