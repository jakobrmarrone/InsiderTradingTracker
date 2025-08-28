from dataclasses import dataclass, field
from datetime import datetime, date

# === Top level JSON === 
@dataclass
class SECTotal:
    value: int
    relation: str

    def __post_init__(self):
        valid_relation_types: list[str] = ["eq"] # Add more as they come
        if not isinstance(self.relation, str):
            raise TypeError("Relation must be of type string")
        if self.relation not in valid_relation_types:
            raise ValueError(f"Unknown relation type seen, add or or confirm this error.\nRelation type: {self.relation}")
# === End Top Level JSON ===

# === Transaction ===
@dataclass
class SECTransactionIssuer:
    cik:            int
    name:           str
    tradingSymbol:  bool

    def __post_init__(self):
        if isinstance(self.cik, str):
            self.cik = int(self.cik)

@dataclass
class SECTransactionReportingOwner:
    cik:            int
    name:           str
    address

@dataclass
class SECTransaction:
    id:                     str
    accessionNo:            str
    filedAt:                datetime
    schmaVersion:           str
    documentType:           int
    periodOfReport:         date
    notSubjectToSection16:  bool
    issuer:                 SECTransactionIssuer
    reportingOwner:         SECTransactionReportingOwner


    def __post_init__(self):
        if isinstance(self.filedAt, str):
            self.filedAt = datetime.fromisoformat(self.filedAt)
        elif not isinstance(self.filedAt, datetime):
            raise TypeError("Filed at timestamp must be a datetime or start as a string")
        
        if isinstance(self.documentType, str):
            self.documentType = int(self.documentType)
        elif not isinstance(self.documentType, int):
            raise TypeError("Document type must be an int or start as a string")

        if isinstance(self.periodOfReport, str):
            self.periodOfReport = date.fromisoformat(self.periodOfReport)
        
# === End Transaction === 

@dataclass
class SECFilingJSON:
    total: SECTotal
    transactions: list[SECTransaction]


class MyClass:

    def __init__(self):
        self.age = 10
        self.name = "a"
        self.running = False
    
    def run(self):
        self.running = True
    
    def stop(self):
        self.running = False
    

mc: MyClass = MyClass()

mc.run()