class EventSpec:
    def __init__(self, summary: str, location: str, start_datetime_str: str, end_datetime_str: str, description: str, gid: str):
        self.summary = summary
        self.location = location
        self.start_datetime_str = start_datetime_str
        self.end_datetime_str = end_datetime_str
        self.description = description
        self.gid = gid
        self.to_str_format = 'html'

        # default color
        self.colorId = "5"

    @property
    def id(self):
        return self.gid.lower()

    #TODO return pre-generated id for email notification.

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

        if self.to_str_format == 'html':
            style = 'style= "border: 1px solid black; border-collapse: collapse; padding: 6px;"'
            return f'<table {style}"> \
                    <tr {style}>\
                        <th {style}>Attribute</th>\
                        <th {style}>Value</th>\
                    </tr>\
                    <tr {style}>\
                        <td {style}><strong>Id</strong></td>\
                        <td {style}>{self.id}</td>\
                    </tr>\
                    <tr {style}>\
                        <td {style}><strong>Summary</strong></td>\
                        <td {style}>{self.summary}</td>\
                    </tr>\
                    <tr {style}>\
                        <td {style}><strong>Location</strong></td>\
                        <td {style}>{self.location}</td>\
                    </tr>\
                    <tr {style}>\
                        <td {style}><strong>Description</strong></td>\
                        <td {style}>{self.description}</td>\
                    </tr>\
                    <tr {style}>\
                        <td {style}><strong>Start Date</strong></td>\
                        <td {style}>{self.start_date_str}</td>\
                    </tr>\
                    <tr {style}>\
                        <td {style}><strong>End Date</strong></td>\
                        <td {style}>{self.end_date_str}</td>\
                    </tr>\
                    </table>'
            
        else:
            return f"summary:{self.summary},gid:{self.gid},StartDate:{self.start_datetime_str},EndDate:{self.end_datetime_str}" 

    def __getitem__(self, x):
        return getattr(self, x)