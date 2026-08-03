class Job:

    def __init__(self, name, priority=2):
        self.name = name
        self.priority = priority


class JobScheduler:

    def __init__(self):
        self.jobs = []

    def add(self, job):
        self.jobs.append(job)
        self.jobs.sort(key=lambda j: j.priority)

    def next(self):
        if not self.jobs:
            return None

        return self.jobs.pop(0)

    def size(self):
        return len(self.jobs)
