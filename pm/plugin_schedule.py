from pm.plug_manager import wxsch_list

class SchCon:
    def __init__(self, job):
        self.job = job

    def __call__(self, cls):
        wxsch_list.append((self.job, cls))
        cls.__sch_plug = True
        return cls
