from .scheduler import Job, JobScheduler
from .registry import AgentRegistry
from .shared_memory import SharedMemory


class Orchestrator:

    def __init__(self):
        self.scheduler = JobScheduler()
        self.registry = AgentRegistry()
        self.memory = SharedMemory()

    def register(self, name, agent):
        self.registry.register(name, agent)

    def submit(self, job_name, priority=2):
        self.scheduler.add(Job(job_name, priority))

    def next_job(self):
        return self.scheduler.next()

    def status(self):
        return {
            "agents": self.registry.list(),
            "jobs": self.scheduler.size(),
            "memory": self.memory.keys(),
        }
