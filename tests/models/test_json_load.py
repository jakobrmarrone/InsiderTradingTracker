# Std lib
import json

# Local lib
from insider_trading.types.sec_filings import SECFilingJSON

with open("./insider_trades.json", 'r') as file:
    pydantic_json_model = SECFilingJSON.model_validate_json(file.read())
    print(pydantic_json_model)


