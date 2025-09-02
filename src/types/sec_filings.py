from dataclasses import dataclass, field, MISSING
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
class TransactionIssuer:
    cik:            int
    name:           str
    tradingSymbol:  bool

    def __post_init__(self):
        if isinstance(self.cik, str):
            self.cik = int(self.cik)

@dataclass
class ReportingOwnerAddress:
    street1:    str
    city:       str
    state:      str
    zipcode:    str

    def __post_init__(self):
        if isinstance(self.zipcode, str):
            self.zipcode = int(self.zipcode)

@dataclass
class ReportingOwnerRelationship:
    isDirector:         bool
    isOfficer:          bool
    officerTitle:       str | None = field(default=None)
    isTenPercentOwner:  bool
    isOther:            bool

@dataclass
class TransactionReportingOwner:
    cik:            int
    name:           str
    address:        ReportingOwnerAddress
    relationship:   ReportingOwnerRelationship

@dataclass
class NonDerivativeCoding:
    formtype:               int
    code:                   str
    equitySwapInvolved:     bool

    def __post_init__(self):
        if isinstance(self.formtype, str):
            self.formtype = int(self.formtype)
        elif isinstance(self.formtype, None):
            raise ValueError("Form instance cannot be None!")

@dataclass
class NonDerivativeAmounts:
    shares:                     int
    pricePerShare:              int
    pricePerShareFootnoteId:    list[str]
    aquiredDisposedCode:        str

@dataclass
class NonDerivPostTransAmount:
    sharedOwnedFollowingTransaction:    int

@dataclass
class NonDerivOwnerNature:
    directOrIndirectOwndership: str

@dataclass
class NonDerivativeTransaction:
    securityTitle:              str
    securityTitleFoornoteId:    list[str]
    transactionDate:            date
    coding:                     NonDerivativeCoding
    amounts:                    NonDerivativeAmounts
    postTransactionAmounts:     NonDerivPostTransAmount
    ownershipNature:            NonDerivOwnerNature

@dataclass
class TransactionNonDerviateTable:
    transactions:           list[NonDerivativeTransaction]

@dataclass
class TransactionFootnote:
    id:         str
    text:       str

@dataclass
class SECTransaction:
    id:                     str
    accessionNo:            str
    filedAt:                datetime
    schmaVersion:           str
    documentType:           int
    periodOfReport:         date
    notSubjectToSection16:  bool
    issuer:                 TransactionIssuer
    reportingOwner:         TransactionReportingOwner
    nonDerivateTable:       TransactionNonDerviateTable
    footNotes:              list[TransactionFootnote]
    ownerSignatureName:     str
    ownerSignatureNameDate: date
    


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
        
        if isinstance(self.ownerSignatureNameDate, str):
            self.ownerSignatureNameDate = date.fromisoformat(self.ownerSignatureNameDate)
        else:
            raise ValueError("Could not convert ownerSignatureNameDate string to a date", self.ownerSignatureNameDate)
        
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