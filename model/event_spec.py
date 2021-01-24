class EventSpec:
    def __init__(self, summary: str, location: str, start_datetime_str: str, end_datetime_str: str, description: str, gid: str):
        self.summary = summary
        self.location = location
        self.start_datetime_str = start_datetime_str
        self.end_datetime_str = end_datetime_str
        self.description = description
        self.gid = gid

        # default color
        self.colorId = "5"

    @property
    def id(self):
        return self.gid.lower()

    @property
    def start_date_str(self):
        return self.get_date_str(dt=self.start_datetime_str)

    @property
    def end_date_str(self):
        return self.get_date_str(dt=self.end_datetime_str)

    @property
    def start_time_str(self):
        return self.get_time_str(dt=self.start_datetime_str)

    @property
    def end_time_str(self):
        return self.get_time_str(dt=self.end_datetime_str)

    def get_date_str(self, dt) -> str:
        return "" or dt[0:10]

    def get_time_str(self, dt) -> str:
        return "" or dt[11:16]

    def __str__(self):
        return f"summary:{self.summary},gid:{self.gid},StartDate:{self.start_datetime_str},EndDate:{self.end_datetime_str}"
    
    def __getitem__(self, x):
        return getattr(self, x)