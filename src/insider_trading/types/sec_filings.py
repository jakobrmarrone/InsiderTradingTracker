# std lib
from datetime import datetime, date

# packages
from pydantic import BaseModel, ConfigDict, Field

# === Top level JSON === 
class SECTotal(BaseModel):
    value: int
    relation: str
# === End Top Level JSON ===

# === Transaction ===
class TransactionIssuer(BaseModel):
    cik:            int
    name:           str
    tradingSymbol:  str

class ReportingOwnerAddress(BaseModel):
    street1:    str
    city:       str
    state:      str
    zipCode:    str

class ReportingOwnerRelationship(BaseModel):
    isDirector:         bool
    isOfficer:          bool
    officerTitle:       str | None = None
    isTenPercentOwner:  bool
    isOther:            bool

class TransactionReportingOwner(BaseModel):
    cik:            int
    name:           str
    address:        ReportingOwnerAddress
    relationship:   ReportingOwnerRelationship

class NonDerivativeCoding(BaseModel):
    formType:               str
    code:                   str
    equitySwapInvolved:     bool


class NonDerivativeAmounts(BaseModel):
    shares:                     int
    pricePerShare:              float | None = None
    pricePerShareFootnoteId:    list[str] = []
    acquiredDisposedCode:       str

class NonDerivPostTransAmount(BaseModel):
    sharesOwnedFollowingTransaction:    int

class NonDerivOwnerNature(BaseModel):
    directOrIndirectOwnership: str

class NonDerivativeTransaction(BaseModel):
    securityTitle:              str
    securityTitleFootnoteId:    list[str] = []
    transactionDate:            date
    coding:                     NonDerivativeCoding
    amounts:                    NonDerivativeAmounts
    postTransactionAmounts:     NonDerivPostTransAmount
    ownershipNature:            NonDerivOwnerNature

class TransactionNonDerivativeTable(BaseModel):
    transactions:           list[NonDerivativeTransaction]

class TransactionFootnote(BaseModel):
    id:                     str
    text:                   str

class SECTransaction(BaseModel):
    id:                     str
    accessionNo:            str
    filedAt:                datetime
    schemaVersion:          str
    documentType:           int
    periodOfReport:         date
    notSubjectToSection16:  bool
    issuer:                 TransactionIssuer
    reportingOwner:         TransactionReportingOwner
    nonDerivativeTable:     TransactionNonDerivativeTable | None = None
    derivativeTable:        TransactionNonDerivativeTable | None = None
    footnotes:              list[TransactionFootnote] = []
    ownerSignatureName:     str
    ownerSignatureNameDate: date
    
# === End Transaction === 

class SECFilingJSON(BaseModel):
    total: SECTotal
    transactions: list[SECTransaction]