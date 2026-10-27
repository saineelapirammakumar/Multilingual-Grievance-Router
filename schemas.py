from typing import Literal
from pydantic import BaseModel,Field,field_validator,model_validator
DEPARTMENTS=['Electricity','Roads','Sanitation','Waste Management','Water Supply']
Urgency=Literal['Routine','Urgent','Emergency']
Status=Literal['Submitted','Assigned','In Progress','Resolved','Reopened','Rejected']
class Location(BaseModel):
    district:str=Field(default='',max_length=100)
    place:str=Field(default='',max_length=150)
    municipality:str=Field(default='',max_length=100)
    ward:str=Field(default='',max_length=50)
    area:str=Field(default='',max_length=100)
    latitude:float|None=Field(default=None,ge=-90,le=90)
    longitude:float|None=Field(default=None,ge=-180,le=180)
    @model_validator(mode='after')
    def coordinates(self):
        if (self.latitude is None)!=(self.longitude is None):raise ValueError('Provide both coordinates or neither')
        if bool(self.district.strip()) != bool(self.place.strip()):raise ValueError('Select both a district and place, or leave both empty for legacy integrations')
        if self.district:
            import json
            from pathlib import Path
            data=json.loads((Path(__file__).resolve().parents[1]/'config'/'tamil_nadu_places.json').read_text())
            if self.district not in data:raise ValueError('Choose a valid Tamil Nadu district')
            if self.place not in data[self.district]:raise ValueError('Choose a place within the selected district')
        return self
class GrievanceRequest(BaseModel):
    text:str=Field(min_length=2,max_length=5000)
    source:Literal['web','sms','app','voice','text']='web'
    location:Location=Field(default_factory=Location)
    email:str|None=Field(default=None,max_length=254)
    email_opt_in:bool=False
    @field_validator('text')
    @classmethod
    def not_blank(cls,v):
        if len(v.strip())<2:raise ValueError('Enter a meaningful complaint')
        return v.strip()
    @field_validator('email')
    @classmethod
    def valid_email(cls,v):
        import re
        if v and not re.fullmatch(r'[^\s@\r\n]+@[^\s@\r\n]+\.[^\s@\r\n]+',v):raise ValueError('Invalid email')
        return v or None
class UpdateRequest(BaseModel):
    expected_version:int=Field(ge=1)
    status:Status|None=None
    assigned_department:str|None=Field(default=None,max_length=100)
    departments:list[str]|None=None
    urgency:Urgency|None=None
    resolution:str|None=Field(default=None,max_length=3000)
    note:str=Field(min_length=3,max_length=3000)
    location:Location|None=None
    @field_validator('departments')
    @classmethod
    def valid_departments(cls,v):
        if v is not None and (not v or len(v)!=len(set(v)) or any(x not in DEPARTMENTS for x in v)):raise ValueError('Choose valid unique departments')
        return v
    @field_validator('assigned_department')
    @classmethod
    def valid_assignment(cls,v):
        if v is not None and v not in DEPARTMENTS:raise ValueError('Unknown department')
        return v
    @field_validator('note')
    @classmethod
    def valid_note(cls,v):
        if len(v.strip())<3:raise ValueError('Provide an audit note')
        return v.strip()
class DuplicateRequest(BaseModel):
    other_id:str
    note:str=Field(min_length=3,max_length=1000)

class UnsolvableRequest(BaseModel):
    expected_version:int=Field(ge=1)
    reason:str=Field(min_length=5,max_length=3000)
    @field_validator('reason')
    @classmethod
    def valid_reason(cls,v):
        if len(v.strip())<5:raise ValueError('Provide a meaningful reason for marking the complaint unsolvable')
        return v.strip()
