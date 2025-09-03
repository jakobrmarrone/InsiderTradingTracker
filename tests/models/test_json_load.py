# Std lib
import json

# Local lib
from insider_trading.types.sec_filings import SECFilingJSON, NonDerivativeTransaction

# Packages
from pydantic_core import from_json
from logging import Logger


logger = Logger("test", 0)


with open("./insider_trades.json", 'r') as file:
    raw = file.read()
    
pydantic_json_model: SECFilingJSON = SECFilingJSON.model_validate_json(raw)
print(pydantic_json_model.transactions[0].nonDerivativeTable.transactions[0].amounts)

# Get all nonDerivateTransactions
