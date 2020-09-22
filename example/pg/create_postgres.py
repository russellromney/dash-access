from postgres_setup import User, db, accessdb, PostgresAccessStore, group, server

################################################################################
### Setup fake users and groups and permissions
################################################################################
adb = PostgresAccessStore(accessdb)
adb.drop_tables()
adb.create_tables()

# create groups structure
group.add(adb, name="all",permissions=["*"])
group.add(adb, name="entry",permissions=["open"])
group.add(adb, name="mid",permissions=["sensitive"],inherits=["entry"])
group.add(adb, name="top",permissions=["classified"],inherits=["mid"])

with server.app_context():
    db.create_all()
    
    admin = User(id='admin',name='admin',)
    admin.set_password("test")
    admin.add_group("all")

    employee = User(id='employee',name='employee',)
    employee.set_password("test")
    employee.add_group("entry")

    manager = User(id='manager',name='manager',)
    manager.set_password("test")
    manager.add_group("mid")

    executive = User(id='executive',name='executive',)
    executive.set_password("test")
    executive.add_group("top")

    try:
        db.session.add(admin)
        db.session.add(employee)
        db.session.add(manager)
        db.session.add(executive)
        db.session.commit()
    except:
        # already made them before, ignore
        pass

