import uuid
from datetime import datetime
from typing import Dict, List, Optional

class ProjectManager:
    def __init__(self):
        self.projects = {}
        self.samples = {}
    
    def create_project(self, name: str) -> str:
        project_id = str(uuid.uuid4())
        self.projects[project_id] = {
            "id": project_id,
            "name": name,
            "created_at": datetime.now(),
            "samples": []
        }
        return project_id
    
    def add_sample(self, project_id: str, sample_data: dict) -> str:
        sample_id = str(uuid.uuid4())
        self.samples[sample_id] = {
            "id": sample_id,
            "project_id": project_id,
            **sample_data
        }
        if project_id in self.projects:
            self.projects[project_id]["samples"].append(sample_id)
        return sample_id
    
    def update_alleles(self, sample_id: str, locus: str, alleles: List[str]):
        if sample_id in self.samples:
            if "alleles" not in self.samples[sample_id]:
                self.samples[sample_id]["alleles"] = {}
            self.samples[sample_id]["alleles"][locus] = alleles
            return True
        return False
