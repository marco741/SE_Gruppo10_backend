from db import db
from common.utils import get_metadata
from config import MAINTAINER_WORK_HOURS, MAINTAINER_WORK_START_HOUR
from functools import reduce


class MaintenanceActivityModel(db.Model):
    """Maintenance Activity class for database interaction"""
    __tablename__ = "maintenance_activities"

    activity_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_type = db.Column(db.Enum("planned", "unplanned", "extra",
                                      name="type_enum", create_type=False))
    site = db.Column(db.String(128))
    typology = db.Column(db.String(128))
    description = db.Column(db.String(128))
    interruptible = db.Column(db.Boolean)
    materials = db.Column(db.String(128), nullable=True)
    workspace_notes = db.Column(db.String(128), nullable=True)
    estimated_time = db.Column(db.Integer)
    week = db.Column(db.Integer, db.CheckConstraint(
        "week >= 1 AND week <= 52"))
    week_day = db.Column(db.Enum("monday", "tuesday", "wednesday", "thursday",
                                 "friday", "saturday", "sunday", name="week_day_enum", create_type=False), nullable=True)
    start_time = db.Column(db.Integer,  db.CheckConstraint(
        f"start_time >= {MAINTAINER_WORK_START_HOUR} AND start_time <= {MAINTAINER_WORK_START_HOUR + MAINTAINER_WORK_HOURS}"), nullable=True)

    maintainer_username = db.Column(db.String(128),
                                    db.ForeignKey("users.username"),
                                    nullable=True)
    maintainer = db.relationship("UserModel")

    def __init__(self, activity_type, site, typology, description, estimated_time,
                 interruptible, week, materials=None, workspace_notes=None, activity_id=None):
        """ 
        MaintenanceActivityModel constructor.

        Args:
            activity_id (int): Unique identifier for Maintenance Activities
            activity_type(String): Type of the Activity
            site(String): Factory's site and area in which the Activity will be performed
            typology(String): Typology of the Activity
            description(String): Description of the Activity
            estimated_time(int): Expected Activity's lifetime in minutes
            interruptible(Boolean): Is the Activity interruptible by a Emergency Work Order?
            materials(String): List of materials to be used during the Activity
            week(int): Week (1 to 52) in which the activity will be performed
            workspace_notes(String): Editable description of the workspace
        """
        self.activity_id = activity_id
        self.activity_type = activity_type
        self.site = site
        self.typology = typology
        self.description = description
        self.estimated_time = estimated_time
        self.interruptible = interruptible
        self.materials = materials
        self.week = week
        self.workspace_notes = workspace_notes

    def json(self):
        """Public representation for MaintenanceActivityModel instance.
        Returns:
            dict of (str, str): The dictionary representation of Maintenance Activity.
        """
        return {
            "activity_id": self.activity_id,
            "activity_type": self.activity_type,
            "site": self.site,
            "typology": self.typology,
            "description": self.description,
            "estimated_time": self.estimated_time,
            "interruptible": self.interruptible,
            "materials": self.materials,
            "week": self.week,
            "workspace_notes": self.workspace_notes,
            "skills_needed": ["PAV certification", "Electrical Maintenance", "Knowledge of cable types",
                              "XYZ-type robot knowledge", "Knowledge of robot workstation 23"]
        }

    def save_to_db(self):
        """Saves user instance to the database"""
        db.session.add(self)
        db.session.commit()

    def update(self, data):
        """Updates activity with passed data.
        Args:
            data (dict of (str, str)): Dictionary of activity's new attributes.
        """
        for k in data:
            setattr(self, k, data[k])

    def update_and_save(self, data):
        """Updates MaintenanceActivityModel instance with passed data and saves it to the database. 

        Args:
            data (dict of (str, str)): Dictionary of activity's attributes.
        """
        self.update(data)
        self.save_to_db()

    def delete_from_db(self):
        """Deletes MaintenanceActivityModel instance from database"""
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, activity_id):
        """Finds a Maintenance Activity in the database based on given id.
        Args:
            activity_id (int): The identifier of the Maintenance Activity to retrieve.
        Returns:
            MaintenanceActivityModel: The found activity
        """
        return cls.query.filter_by(activity_id=activity_id).first()

    @classmethod
    def find_all(cls):
        """Finds every Maintenance Activity in the database
        Returns:
            list of (MaintenanceActivityModel): List of found Maintenance Activities
        """
        return cls.query.all()

    @classmethod
    def find_some(cls, current_page=1, page_size=10):
        """Finds the selected page of Maintenance Activitis by means of given current_page and page_size.
            Fails if current_page does not exist.

        Args:
            current_page (int, optional): The desired page number, starting from 1. Defaults to 1.
            page_size (int, optional): The desired page size. Defaults to 10.

        Returns:
            ( list of (MaintenanceActivityModel), dict of (str, int) ): 
            The first tuple element is a list of paginated MaintenanceActivityModel instances; 
            The second tuple element is the pagination metadata;
            """
        rows = cls.query.offset(
            page_size*(current_page-1)).limit(page_size).all()

        meta = get_metadata(
            cls.query.paginate(page=current_page, per_page=page_size)
        )
        return rows, meta

    @classmethod
    def find_all_in_day(cls, week, week_day):
        """Finds every Maintenance Activity for a given day

        Args:
            week (int): The nth week of the year
            week_day (str): The day of the week (i.e.: monday, tuesday, ...)

        Returns:
            list of (MaintenanceActivityModel): List of found Maintenance Activities
        """
        return cls.query.filter_by(week=week).filter_by(week_day=week_day).all()

    @classmethod
    def find_some_in_day(cls, week, week_day, current_page=1, page_size=10):
        """Finds the selected page of Maintenance Activitis for a given day by means of given current_page and page_size.
            Fails if current_page does not exist.

        Args:
            week (int): The nth week of the year
            week_day (str): The day of the week (i.e.: monday, tuesday, ...)
            current_page (int, optional): The desired page number, starting from 1. Defaults to 1.
            page_size (int, optional): The desired page size. Defaults to 10.

        Returns:
            ( list of (MaintenanceActivityModel), dict of (str, int) ): 
            The first tuple element is a list of paginated MaintenanceActivityModel instances; 
            The second tuple element is the pagination metadata;
        """
        rows = (cls.query
                .filter_by(week=week)
                .filter_by(week_day=week_day)
                .offset(page_size*(current_page-1))
                .limit(page_size)
                .all())

        meta = get_metadata(
            cls.query
            .filter_by(week=week)
            .filter_by(week_day=week_day)
            .paginate(page=current_page, per_page=page_size)
        )
        return rows, meta

    @classmethod
    def find_all_in_day_for_user(cls, username, week, week_day, exclude=None):
        """Finds every Maintenance Activity for a given day and a given user

        Args:
            username (str): The username for the maintainer who has to perform those maintenance activities
            week (int): The nth week of the year
            week_day (str): The day of the week (i.e.: monday, tuesday, ...)
            exclude (int, optional): a valid identifier for an activity that has to be assigned

        Returns:
            list of (MaintenanceActivityModel): List of found Maintenance Activities
        """
        activities = cls.query.filter_by(maintainer_username=username).filter_by(
            week=week).filter_by(week_day=week_day).all()
        if exclude:
            activities = list(
                filter(lambda activity: activity.activity_id != exclude, activities))
        return activities

    @classmethod
    def find_some_in_day_for_user(cls, username, week, week_day, current_page=1, page_size=10):
        """Finds the selected page of Maintenance Activitis for a given day and a given user 
            by means of given current_page and page_size.
            Fails if current_page does not exist.

        Args:
            username (str): The username for the maintainer who has to perform those maintenance activities
            week (int): The nth week of the year
            week_day (str): The day of the week (i.e.: monday, tuesday, ...)
            current_page (int, optional): The desired page number, starting from 1. Defaults to 1.
            page_size (int, optional): The desired page size. Defaults to 10.

        Returns:
            ( list of (MaintenanceActivityModel), dict of (str, int) ): 
            The first tuple element is a list of paginated MaintenanceActivityModel instances; 
            The second tuple element is the pagination metadata;
        """
        rows = (cls.query
                .filter_by(maintainer_username=username)
                .filter_by(week=week)
                .filter_by(week_day=week_day)
                .offset(page_size*(current_page-1))
                .limit(page_size)
                .all())

        meta = get_metadata(
            cls.query
            .filter_by(maintainer_username=username)
            .filter_by(week=week)
            .filter_by(week_day=week_day)
            .paginate(page=current_page, per_page=page_size)
        )
        return rows, meta

    @classmethod
    def find_all_in_week(cls, week):
        """Finds every Maintenance Activity for a given week

        Args:
            week (int): The nth week of the year

        Returns:
            list of (MaintenanceActivityModel): List of found Maintenance Activities
        """
        return cls.query.filter_by(week=week).all()

    @classmethod
    def find_some_in_week(cls, week, current_page=1, page_size=10):
        """Finds the selected page of Maintenance Activitis for a given week by means of given current_page and page_size.
            Fails if current_page does not exist.

        Args:
            week (int): The nth week of the year
            current_page (int, optional): The desired page number, starting from 1. Defaults to 1.
            page_size (int, optional): The desired page size. Defaults to 10.

        Returns:
            ( list of (MaintenanceActivityModel), dict of (str, int) ): 
            The first tuple element is a list of paginated MaintenanceActivityModel instances; 
            The second tuple element is the pagination metadata;
        """
        rows = (cls.query
                .filter_by(week=week)
                .offset(page_size*(current_page-1))
                .limit(page_size)
                .all())

        meta = get_metadata(
            cls.query
            .filter_by(week=week)
            .paginate(page=current_page, per_page=page_size)
        )
        return rows, meta

    @classmethod
    def get_total_estimated_time(cls, activities):
        """Calculates the sum of activities' estimated time given a list of activities

        Args:
            activities (list of (MaintenanceActivityModel)): The list of Maintenance Activities

        Returns:
            int: The total estimated time in minutes
        """
        return reduce(lambda acc,
                      activity: acc + activity.estimated_time, activities, 0)
